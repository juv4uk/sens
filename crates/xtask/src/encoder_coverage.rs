//! #176 (MACHINE-ISA-3): generate a deterministic, per-ICLASS encoder
//! coverage manifest from #175's admitted XED evidence.
//!
//! This module is a transport/normalization mechanism only, exactly like
//! xed_import. It never invents encoding facts: for every ICLASS admitted
//! by lib/machine/xed/generated/machine-evidence.lisp it emits either
//! `partial` (an existing Lisp encoder in lib/machine/encoding/x86-64.lisp
//! covers at least one real form of that ICLASS) or `not-yet-implemented`
//! (an explicit, justified gap) -- there is no third, silent outcome. The
//! `partial`/`implemented` ICLASS set is a small curated Rust table kept in
//! sync with the actual encoder by a Rust integration test; this module
//! does not decide what counts as "implemented" on its own.

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

/// ICLASS names for which lib/machine/encoding/x86-64.lisp already defines
/// a concrete encoder covering at least one real operand-form variant.
/// None of these cover every XED form of that ICLASS yet (e.g. MOV has 22
/// XED forms; only a few register/disp8 variants are encoded), so the
/// status is `partial`, not `implemented`.
fn partially_implemented_iclasses() -> BTreeMap<&'static str, &'static str> {
    [
        (
            "RET_NEAR",
            "x86-encode-ret covers the no-operand near-return form only; the imm16 stack-adjust variant is pending",
        ),
        (
            "MOV",
            "x86-encode-mov-r64-imm64 (any of 16 GPRs, non-negative immediate; negative imm64 is admitted but fails closed at the real host boundary -- see #176's negative_mov_r64_imm64_is_admitted_but_fails_closed_at_the_real_host_boundary), x86-encode-mov-r64-mem-disp8, and x86-encode-mov-mem-disp8-r64 (any of 16 GPRs as base/dest, full disp8 range -128..127) cover 3 of MOV's 22 XED forms; the 32/64-bit-displacement, SIB-index, and other MOV forms are pending",
        ),
        (
            "ADD",
            "x86-encode-add-r64-r64 covers the register/register form only, of ADD's 18 XED forms",
        ),
        (
            "OR",
            "x86-encode-or-r64-r64 covers the register/register form only, sharing ADD's group-1 shape one opcode byte apart",
        ),
        (
            "AND",
            "x86-encode-and-r64-r64 covers the register/register form only, sharing ADD's group-1 shape one opcode byte apart",
        ),
        (
            "SUB",
            "x86-encode-sub-r64-r64 covers the register/register form only, sharing ADD's group-1 shape one opcode byte apart",
        ),
        (
            "XOR",
            "x86-encode-xor-r64-r64 covers the register/register form only, sharing ADD's group-1 shape one opcode byte apart",
        ),
        (
            "CMP",
            "x86-encode-cmp-r64-r64 covers the register/register form only, sharing ADD's group-1 shape one opcode byte apart",
        ),
        (
            "TEST",
            "x86-encode-test-r64-r64 covers the register/register form (0x85 /r) only, reusing ADD's group-1 shape",
        ),
        (
            "PUSH",
            "x86-encode-push-r64 covers the single-register 0x50+rd form only; PUSH imm/r-m64-memory/segment forms are pending",
        ),
        (
            "POP",
            "x86-encode-pop-r64 covers the single-register 0x58+rd form only; POP r/m64-memory/segment forms are pending",
        ),
        (
            "INC",
            "x86-encode-inc-r64 covers the group-5 register form (0xFF /0) only; the not64 legacy single-byte form and r/m64-memory forms are pending",
        ),
        (
            "DEC",
            "x86-encode-dec-r64 covers the group-5 register form (0xFF /1) only; the not64 legacy single-byte form and r/m64-memory forms are pending",
        ),
        (
            "NOT",
            "x86-encode-not-r64 covers the group-3 register form (0xF7 /2) only; r/m64-memory forms are pending",
        ),
        (
            "NEG",
            "x86-encode-neg-r64 covers the group-3 register form (0xF7 /3) only; r/m64-memory forms are pending",
        ),
        (
            "JO",
            "x86-encode-jo-rel8 covers the rel8 form (0x70) only; the rel32 form is pending",
        ),
        (
            "JNO",
            "x86-encode-jno-rel8 covers the rel8 form (0x71) only; the rel32 form is pending",
        ),
        (
            "JB",
            "x86-encode-jb-rel8 covers the rel8 form (0x72) only; the rel32 form is pending",
        ),
        (
            "JNB",
            "x86-encode-jnb-rel8 covers the rel8 form (0x73) only; the rel32 form is pending",
        ),
        (
            "JZ",
            "x86-encode-jz-rel8 covers the rel8 form (0x74) only; the rel32 form is pending",
        ),
        (
            "JNZ",
            "x86-encode-jnz-rel8 covers the rel8 form (0x75) only; the rel32 form is pending",
        ),
        (
            "JBE",
            "x86-encode-jbe-rel8 covers the rel8 form (0x76) only; the rel32 form is pending",
        ),
        (
            "JNBE",
            "x86-encode-jnbe-rel8 covers the rel8 form (0x77) only; the rel32 form is pending",
        ),
        (
            "JS",
            "x86-encode-js-rel8 covers the rel8 form (0x78) only; the rel32 form is pending",
        ),
        (
            "JNS",
            "x86-encode-jns-rel8 covers the rel8 form (0x79) only; the rel32 form is pending",
        ),
        (
            "JP",
            "x86-encode-jp-rel8 covers the rel8 form (0x7A) only; the rel32 form is pending",
        ),
        (
            "JNP",
            "x86-encode-jnp-rel8 covers the rel8 form (0x7B) only; the rel32 form is pending",
        ),
        (
            "JL",
            "x86-encode-jl-rel8 covers the rel8 form (0x7C) only; the rel32 form is pending",
        ),
        (
            "JNL",
            "x86-encode-jnl-rel8 covers the rel8 form (0x7D) only; the rel32 form is pending",
        ),
        (
            "JLE",
            "x86-encode-jle-rel8 covers the rel8 form (0x7E) only; the rel32 form is pending",
        ),
        (
            "JNLE",
            "x86-encode-jnle-rel8 covers the rel8 form (0x7F) only; the rel32 form is pending",
        ),
        (
            "JMP",
            "x86-encode-jmp-rel8 covers the unconditional rel8 form (0xEB) only; the rel32 \
             (0xE9) and indirect register/memory (0xFF /4) forms are pending",
        ),
    ]
    .into_iter()
    .collect()
}

fn not_yet_implemented_reason(admitted_extension: &str) -> &'static str {
    match admitted_extension {
        "AVX" | "AVX2" | "FMA3" | "BMI1" | "BMI2" | "F16C" => {
            "VEX-prefix encoding not yet implemented"
        }
        "X87" => "x87 stack-register encoding not yet implemented",
        "MMX" => "MMX opcode-map encoding not yet implemented",
        "SSE" | "SSE2" | "SSE3" | "SSSE3" | "SSE4.1+SSE4.2" => {
            "legacy SSE mandatory-prefix/ModRM encoding not yet implemented"
        }
        "AES-NI" | "PCLMULQDQ" => "SSE-prefixed crypto encoding not yet implemented",
        "XSAVE" => "XSAVE control-state encoding not yet implemented",
        "MPX" => "BND-register encoding not yet implemented",
        "SGX" => "ENCLS/ENCLU leaf-function encoding not yet implemented",
        "RDRAND" | "RDSEED" => "0F C7 opcode-map encoding not yet implemented",
        "CLFLUSHOPT" => "cache-management opcode encoding not yet implemented",
        "X86-64" => "long-mode-specific BASE forms pending family-by-family rollout",
        _ => "remaining BASE forms pending family-by-family rollout",
    }
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct CoverageEntry {
    pub iclass: String,
    pub admitted_extension: String,
    pub status: &'static str,
    pub reason: String,
}

/// Reads the #175 evidence file's `(form (extension E) (xed-extension X)
/// (iclass "I") ...)` records and returns the distinct (iclass, extension)
/// pairs. This is intentionally a light-weight line scan, matching
/// xed_import's own style, rather than a full Lisp parse -- the evidence
/// file's shape is generated by this same toolchain and stable by
/// construction.
pub fn admitted_iclasses(evidence_path: &Path) -> Result<BTreeSet<(String, String)>, String> {
    let text = fs::read_to_string(evidence_path).map_err(|error| {
        format!(
            "cannot read evidence file {}: {error}",
            evidence_path.display()
        )
    })?;

    let mut pending_extension: Option<String> = None;
    let mut pairs = BTreeSet::new();
    for line in text.lines() {
        let trimmed = line.trim();
        if let Some(rest) = trimmed.strip_prefix("(extension ") {
            pending_extension = rest.strip_suffix(')').map(str::to_string);
        } else if let Some(rest) = trimmed.strip_prefix("(iclass \"") {
            let Some(iclass) = rest.strip_suffix("\")") else {
                return Err(format!("malformed iclass line: {trimmed}"));
            };
            let Some(extension) = pending_extension.clone() else {
                return Err(format!(
                    "iclass {iclass} has no preceding extension line -- evidence file is malformed"
                ));
            };
            pairs.insert((extension, iclass.to_string()));
        }
    }
    Ok(pairs)
}

pub fn build_coverage(evidence_path: &Path) -> Result<Vec<CoverageEntry>, String> {
    let pairs = admitted_iclasses(evidence_path)?;
    let partial = partially_implemented_iclasses();

    let mut entries: Vec<CoverageEntry> = pairs
        .into_iter()
        .map(|(extension, iclass)| {
            if let Some(&reason) = partial.get(iclass.as_str()) {
                CoverageEntry {
                    iclass,
                    admitted_extension: extension,
                    status: "partial",
                    reason: reason.to_string(),
                }
            } else {
                let reason = not_yet_implemented_reason(&extension).to_string();
                CoverageEntry {
                    iclass,
                    admitted_extension: extension,
                    status: "not-yet-implemented",
                    reason,
                }
            }
        })
        .collect();
    entries.sort();

    // Every curated "partial" ICLASS must actually be admitted; a stale
    // entry (an ICLASS the encoder claims but #175 no longer admits) is a
    // sync bug between this table and the evidence, not a silent no-op.
    let admitted_iclass_names: BTreeSet<&str> =
        entries.iter().map(|entry| entry.iclass.as_str()).collect();
    for &curated in partial.keys() {
        if !admitted_iclass_names.contains(curated) {
            return Err(format!(
                "encoder_coverage: {curated} is marked partially-implemented but is not an admitted ICLASS in {}",
                evidence_path.display()
            ));
        }
    }

    Ok(entries)
}

fn escape_lisp_string(value: &str) -> String {
    value.replace('\\', "\\\\").replace('"', "\\\"")
}

pub fn render(entries: &[CoverageEntry]) -> String {
    let partial_count = entries.iter().filter(|e| e.status == "partial").count();
    let mut out = String::new();
    out.push_str("; GENERATED by `cargo xtask generate-encoder-coverage` -- do not hand-edit.\n");
    out.push_str("; Source: lib/machine/xed/generated/machine-evidence.lisp (#175) cross-\n");
    out.push_str("; referenced against lib/machine/encoding/x86-64.lisp (#176). Every ICLASS\n");
    out.push_str("; admitted by #175 appears here exactly once: `partial` names a real Lisp\n");
    out.push_str("; encoder covering at least one of its forms, `not-yet-implemented` is an\n");
    out.push_str("; explicit, justified gap. There is no third, silent outcome (#176).\n\n");
    out.push_str("(x86-encoder-coverage/1\n");
    out.push_str(&format!("  (form-count {})\n", entries.len()));
    out.push_str(&format!("  (partial-count {partial_count})\n"));
    for entry in entries {
        out.push_str("  (coverage\n");
        out.push_str(&format!(
            "    (iclass \"{}\")\n",
            escape_lisp_string(&entry.iclass)
        ));
        out.push_str(&format!(
            "    (extension {})\n",
            entry.admitted_extension
        ));
        out.push_str(&format!("    (status {})\n", entry.status));
        out.push_str(&format!(
            "    (reason \"{}\"))\n",
            escape_lisp_string(&entry.reason)
        ));
    }
    out.push_str(")\n");
    out
}

pub struct RunOptions {
    pub evidence_path: PathBuf,
    pub out_path: PathBuf,
    pub check: bool,
}

pub fn run(options: RunOptions) -> ExitCode {
    let entries = match build_coverage(&options.evidence_path) {
        Ok(entries) => entries,
        Err(error) => {
            eprintln!("generate-encoder-coverage failed: {error}");
            return ExitCode::FAILURE;
        }
    };
    let rendered = render(&entries);

    if options.check {
        match fs::read_to_string(&options.out_path) {
            Ok(existing) if existing == rendered => {
                println!(
                    "generate-encoder-coverage --check: {} ICLASSes, output matches committed coverage",
                    entries.len()
                );
                ExitCode::SUCCESS
            }
            Ok(_) => {
                eprintln!(
                    "generate-encoder-coverage --check: {} is stale; rerun `cargo xtask generate-encoder-coverage` and commit the result",
                    options.out_path.display()
                );
                ExitCode::FAILURE
            }
            Err(error) => {
                eprintln!(
                    "generate-encoder-coverage --check: cannot read {}: {error}",
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
                    "generate-encoder-coverage: wrote {} ICLASSes to {}",
                    entries.len(),
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
