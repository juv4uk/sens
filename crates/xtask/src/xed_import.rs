//! #175 (MACHINE-ISA-2): normalize pinned XED evidence into Lisp-owned
//! machine records.
//!
//! This module is a transport/normalization mechanism only. It reads
//! vendored, pinned upstream XED text (see lib/machine/xed/provenance.lisp),
//! extracts a bounded set of fields (instruction class, XED extension tag,
//! category, ISA-set grouping, a coarse form count, and one representative
//! operand descriptor), maps the XED extension tag onto an already-admitted
//! sens extension name, and emits deterministic Lisp data with a stable
//! digest. It never invents a public semantic ID, never touches the
//! semantic registry, and fails closed on anything it cannot parse
//! confidently rather than guessing.

use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

/// XED extension tag -> already-admitted sens extension name. Every
/// value here must already exist as an `(admitted-extension ...)` fact in
/// lib/machine/cpu/intel-core-i5-6400-inventory.lisp; this table renames
/// nothing new into existence, it only aligns two pre-existing vocabularies.
/// Kept in sync with lib/machine/xed/provenance.lisp's `extension-mapping`
/// facts by an integration test.
fn extension_mapping() -> BTreeMap<&'static str, &'static str> {
    [
        ("BASE", "X86-BASE"),
        ("LONGMODE", "X86-64"),
        ("X87", "X87"),
        ("MMX", "MMX"),
        ("SSE", "SSE"),
        ("SSE2", "SSE2"),
        ("SSE3", "SSE3"),
        ("SSSE3", "SSSE3"),
        ("SSE4", "SSE4.1+SSE4.2"),
        ("AES", "AES-NI"),
        ("PCLMULQDQ", "PCLMULQDQ"),
        ("XSAVE", "XSAVE"),
        ("AVX", "AVX"),
        ("AVX2", "AVX2"),
        ("FMA", "FMA3"),
        ("BMI1", "BMI1"),
        ("BMI2", "BMI2"),
        ("CLFLUSHOPT", "CLFLUSHOPT"),
        ("MPX", "MPX"),
        ("SGX", "SGX"),
        ("RDRAND", "RDRAND"),
        ("RDSEED", "RDSEED"),
        ("F16C", "F16C"),
    ]
    .into_iter()
    .collect()
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct XedForm {
    pub admitted_extension: String,
    pub xed_extension: String,
    pub iclass: String,
    pub category: String,
    pub isa_set: Option<String>,
    pub form_count: u32,
    pub operand_summary: String,
    pub source_file: String,
}

/// Parses every `{ ICLASS ... }` block in one vendored XED text file.
/// Fails closed: a block with an ICLASS but a missing EXTENSION, CATEGORY,
/// or OPERANDS field is an error, not a skip -- the pipeline must not
/// silently admit a partially-understood form.
fn parse_vendor_file(path: &Path, display_path: &str) -> Result<Vec<XedForm>, String> {
    let text = fs::read_to_string(path)
        .map_err(|error| format!("cannot read vendor file {}: {error}", path.display()))?;
    let source_file = display_path.to_string();
    let mapping = extension_mapping();

    let mut forms = Vec::new();
    let mut in_block = false;
    let mut block_start_line = 0usize;
    let mut iclass: Option<String> = None;
    let mut extension: Option<String> = None;
    let mut category: Option<String> = None;
    let mut isa_set: Option<String> = None;
    let mut form_count = 0u32;
    let mut operand_summary: Option<String> = None;

    fn field_value(line: &str, key: &str) -> Option<String> {
        let rest = line.strip_prefix(key)?;
        let rest = rest.trim_start();
        let rest = rest.strip_prefix(':')?;
        Some(rest.trim().to_string())
    }

    for (line_number, raw_line) in text.lines().enumerate() {
        let line = raw_line.trim_end();
        if line == "{" {
            if in_block {
                return Err(format!(
                    "{}:{}: nested `{{` without a closing `}}` for the previous block",
                    source_file,
                    line_number + 1
                ));
            }
            in_block = true;
            block_start_line = line_number + 1;
            iclass = None;
            extension = None;
            category = None;
            isa_set = None;
            form_count = 0;
            operand_summary = None;
            continue;
        }
        if line == "}" {
            if !in_block {
                continue;
            }
            in_block = false;
            let Some(iclass) = iclass.take() else {
                // A brace-delimited block with no ICLASS line is not an
                // instruction-form record (XED uses `{}` for a few other
                // section shapes too); it carries no field we import, so
                // it is silently not a form rather than a malformed one.
                continue;
            };
            let extension = extension.take().ok_or_else(|| {
                format!(
                    "{}:{}: ICLASS {iclass} has no EXTENSION field",
                    source_file, block_start_line
                )
            })?;
            let category = category.take().ok_or_else(|| {
                format!(
                    "{}:{}: ICLASS {iclass} has no CATEGORY field",
                    source_file, block_start_line
                )
            })?;
            let operand_summary = operand_summary.take().ok_or_else(|| {
                format!(
                    "{}:{}: ICLASS {iclass} has no OPERANDS field",
                    source_file, block_start_line
                )
            })?;
            if form_count == 0 {
                return Err(format!(
                    "{}:{}: ICLASS {iclass} declares OPERANDS but no PATTERN",
                    source_file, block_start_line
                ));
            }

            let Some(&admitted_extension) = mapping.get(extension.as_str()) else {
                // Not one of the extensions admitted in #174. This is
                // expected and not an error: most vendored files (e.g. the
                // shared base spine) also carry a handful of forms outside
                // our admitted set (VTX, MONITOR, RDTSCP, ...).
                continue;
            };

            forms.push(XedForm {
                admitted_extension: admitted_extension.to_string(),
                xed_extension: extension,
                iclass,
                category,
                isa_set: isa_set.take(),
                form_count,
                operand_summary,
                source_file: source_file.clone(),
            });
            continue;
        }
        if !in_block {
            continue;
        }
        if let Some(value) = field_value(line, "ICLASS") {
            iclass = Some(value);
        } else if let Some(value) = field_value(line, "EXTENSION") {
            extension = Some(value);
        } else if let Some(value) = field_value(line, "CATEGORY") {
            category = Some(value);
        } else if let Some(value) = field_value(line, "ISA_SET") {
            isa_set = Some(value);
        } else if line.trim_start().starts_with("PATTERN") {
            form_count += 1;
        } else if operand_summary.is_none() {
            if let Some(value) = field_value(line, "OPERANDS") {
                operand_summary = Some(value);
            }
        }
    }

    if in_block {
        return Err(format!(
            "{}:{}: unterminated block (missing closing `}}`)",
            source_file, block_start_line
        ));
    }

    Ok(forms)
}

/// Parses every vendor file directly under `vendor_root` (recursively) and
/// returns the admitted, deterministically sorted, conflict-checked form
/// set. Sorting by (admitted_extension, iclass, source_file) makes the
/// result -- and its digest -- independent of upstream line order and of
/// the filesystem's directory-walk order.
pub fn collect_forms(vendor_root: &Path) -> Result<Vec<XedForm>, String> {
    let mut files = Vec::new();
    collect_files(vendor_root, &mut files)?;
    files.sort();

    let mut raw_forms = Vec::new();
    for file in &files {
        let relative = file
            .strip_prefix(vendor_root)
            .unwrap_or(file)
            .to_string_lossy()
            .replace('\\', "/");
        raw_forms.extend(parse_vendor_file(file, &relative)?);
    }
    raw_forms.sort();

    // One ICLASS commonly has several XED `{}` blocks in the same source
    // under the same extension (e.g. VMOVD has distinct reg/mem
    // operand-direction blocks; PMULUDQ has both an MMX-register and an
    // SSE2-register block) -- those are encoding-form variants of one
    // instruction, not a conflict, so they merge into a single record: a
    // summed form_count and every distinct CATEGORY seen, joined
    // deterministically. It only becomes an authority-boundary conflict
    // when the same ICLASS is claimed under two different admitted
    // extensions, which would mean an instruction mnemonic's owning
    // extension is ambiguous across sources.
    let mut forms: Vec<XedForm> = Vec::new();
    for form in raw_forms {
        match forms.last_mut() {
            Some(previous)
                if previous.iclass == form.iclass
                    && previous.admitted_extension == form.admitted_extension =>
            {
                previous.form_count += form.form_count;
                if !previous
                    .category
                    .split('/')
                    .any(|existing| existing == form.category)
                {
                    previous.category.push('/');
                    previous.category.push_str(&form.category);
                }
            }
            Some(previous) if previous.iclass == form.iclass => {
                return Err(format!(
                    "authority-boundary conflict: ICLASS {} admitted from both {} ({}) and {} ({})",
                    form.iclass,
                    previous.source_file,
                    previous.admitted_extension,
                    form.source_file,
                    form.admitted_extension
                ));
            }
            _ => forms.push(form),
        }
    }

    Ok(forms)
}

fn collect_files(dir: &Path, out: &mut Vec<PathBuf>) -> Result<(), String> {
    let entries = fs::read_dir(dir)
        .map_err(|error| format!("cannot read vendor directory {}: {error}", dir.display()))?;
    for entry in entries {
        let entry = entry.map_err(|error| format!("cannot read directory entry: {error}"))?;
        let path = entry.path();
        if path.is_dir() {
            collect_files(&path, out)?;
        } else if path.extension().is_some_and(|ext| ext == "txt") {
            out.push(path);
        }
    }
    Ok(())
}

fn escape_lisp_string(value: &str) -> String {
    value.replace('\\', "\\\\").replace('"', "\\\"")
}

/// Renders the admitted form set as deterministic Lisp data plus a stable
/// sha256 digest computed over the same canonical field tuples (not over
/// the rendered text), so the digest is unaffected by comment/header
/// wording changes and is comparable across a --check run.
pub fn render(forms: &[XedForm], pinned_commit: &str) -> String {
    let mut canonical = String::new();
    for form in forms {
        canonical.push_str(&form.admitted_extension);
        canonical.push('\x1f');
        canonical.push_str(&form.xed_extension);
        canonical.push('\x1f');
        canonical.push_str(&form.iclass);
        canonical.push('\x1f');
        canonical.push_str(&form.category);
        canonical.push('\x1f');
        canonical.push_str(form.isa_set.as_deref().unwrap_or(""));
        canonical.push('\x1f');
        canonical.push_str(&form.form_count.to_string());
        canonical.push('\x1f');
        canonical.push_str(&form.operand_summary);
        canonical.push('\x1e');
    }
    let digest = sha256_hex(canonical.as_bytes());

    let mut out = String::new();
    out.push_str("; GENERATED by `cargo xtask import-xed-evidence` -- do not hand-edit.\n");
    out.push_str("; Source: lib/machine/xed/provenance.lisp (#175 MACHINE-ISA-2).\n");
    out.push_str(&format!("; Pinned XED commit: {pinned_commit}\n"));
    out.push_str(
        "; This is external technical evidence, not semantic authority (#150).\n\n",
    );
    out.push_str("(xed-machine-evidence/1\n");
    out.push_str(&format!("  (pinned-commit \"{pinned_commit}\")\n"));
    out.push_str(&format!("  (source-digest \"sha256:{digest}\")\n"));
    out.push_str(&format!("  (form-count {})\n", forms.len()));
    for form in forms {
        out.push_str("  (form\n");
        out.push_str(&format!(
            "    (extension {})\n",
            form.admitted_extension
        ));
        out.push_str(&format!("    (xed-extension {})\n", form.xed_extension));
        out.push_str(&format!(
            "    (iclass \"{}\")\n",
            escape_lisp_string(&form.iclass)
        ));
        out.push_str(&format!(
            "    (category \"{}\")\n",
            escape_lisp_string(&form.category)
        ));
        match &form.isa_set {
            Some(isa_set) => out.push_str(&format!(
                "    (isa-set \"{}\")\n",
                escape_lisp_string(isa_set)
            )),
            None => out.push_str("    (isa-set ())\n"),
        }
        out.push_str(&format!("    (form-count {})\n", form.form_count));
        out.push_str(&format!(
            "    (operand-summary \"{}\")\n",
            escape_lisp_string(&form.operand_summary)
        ));
        out.push_str("    (source-file \"");
        out.push_str(&escape_lisp_string(&form.source_file));
        out.push_str("\"))\n");
    }
    out.push_str(")\n");
    out
}

pub struct RunOptions {
    pub vendor_root: PathBuf,
    pub out_path: PathBuf,
    pub pinned_commit: String,
    pub check: bool,
}

pub fn run(options: RunOptions) -> ExitCode {
    let forms = match collect_forms(&options.vendor_root) {
        Ok(forms) => forms,
        Err(error) => {
            eprintln!("import-xed-evidence failed: {error}");
            return ExitCode::FAILURE;
        }
    };
    let rendered = render(&forms, &options.pinned_commit);

    if options.check {
        match fs::read_to_string(&options.out_path) {
            Ok(existing) if existing == rendered => {
                println!(
                    "import-xed-evidence --check: {} forms, output matches committed evidence",
                    forms.len()
                );
                ExitCode::SUCCESS
            }
            Ok(_) => {
                eprintln!(
                    "import-xed-evidence --check: {} is stale; rerun `cargo xtask import-xed-evidence` and commit the result",
                    options.out_path.display()
                );
                ExitCode::FAILURE
            }
            Err(error) => {
                eprintln!(
                    "import-xed-evidence --check: cannot read {}: {error}",
                    options.out_path.display()
                );
                ExitCode::FAILURE
            }
        }
    } else {
        if let Some(parent) = options.out_path.parent() {
            if let Err(error) = fs::create_dir_all(parent) {
                eprintln!("cannot create {}: {error}", parent.display());
                return ExitCode::FAILURE;
            }
        }
        match fs::write(&options.out_path, &rendered) {
            Ok(()) => {
                println!(
                    "import-xed-evidence: wrote {} forms to {}",
                    forms.len(),
                    options.out_path.display()
                );
                ExitCode::SUCCESS
            }
            Err(error) => {
                eprintln!("cannot write {}: {error}", options.out_path.display());
                ExitCode::FAILURE
            }
        }
    }
}

/// A tiny self-contained SHA-256 implementation, mirroring
/// external_oracle::sha256_hex so xtask stays dependency-free. Only used
/// for source-digest provenance, never for cryptographic security.
fn sha256_hex(data: &[u8]) -> String {
    const K: [u32; 64] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
        0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
        0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
        0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
        0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
        0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
        0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
        0xc67178f2,
    ];
    let mut h: [u32; 8] = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab,
        0x5be0cd19,
    ];
    let bit_len = (data.len() as u64).wrapping_mul(8);
    let mut msg = data.to_vec();
    msg.push(0x80);
    while (msg.len() % 64) != 56 {
        msg.push(0x00);
    }
    msg.extend_from_slice(&bit_len.to_be_bytes());

    for chunk in msg.chunks(64) {
        let mut w = [0u32; 64];
        for i in 0..16 {
            w[i] = u32::from_be_bytes([
                chunk[i * 4],
                chunk[i * 4 + 1],
                chunk[i * 4 + 2],
                chunk[i * 4 + 3],
            ]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16]
                .wrapping_add(s0)
                .wrapping_add(w[i - 7])
                .wrapping_add(s1);
        }

        let (mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut hh) =
            (h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7]);

        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let temp1 = hh
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(K[i])
                .wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = s0.wrapping_add(maj);

            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(temp1);
            d = c;
            c = b;
            b = a;
            a = temp1.wrapping_add(temp2);
        }

        h[0] = h[0].wrapping_add(a);
        h[1] = h[1].wrapping_add(b);
        h[2] = h[2].wrapping_add(c);
        h[3] = h[3].wrapping_add(d);
        h[4] = h[4].wrapping_add(e);
        h[5] = h[5].wrapping_add(f);
        h[6] = h[6].wrapping_add(g);
        h[7] = h[7].wrapping_add(hh);
    }

    h.iter().map(|word| format!("{word:08x}")).collect()
}
