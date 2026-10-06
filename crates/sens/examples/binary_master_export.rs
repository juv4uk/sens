use sens::{lower_program, parse, wire_decode_program, wire_encode_program, Expr, ExprKind};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

const SOURCE_EXTS: &[&str] = &["lisp", "lsp", "cl", "scm", "rkt", "sens"];
const SKIP_DIRS: &[&str] = &[
    ".git", "target", "node_modules", ".venv", "venv", "vendor",
    "__pycache__", "dist", "build",
];

fn should_skip(path: &Path) -> bool {
    path.components().any(|c| {
        let s = c.as_os_str().to_string_lossy();
        SKIP_DIRS.iter().any(|x| *x == s)
    })
}

fn is_source(path: &Path) -> bool {
    path.extension()
        .and_then(|x| x.to_str())
        .is_some_and(|ext| SOURCE_EXTS.contains(&ext))
}

fn collect(root: &Path, out: &mut Vec<PathBuf>) -> std::io::Result<()> {
    for entry in fs::read_dir(root)? {
        let entry = entry?;
        let path = entry.path();
        if should_skip(&path) {
            continue;
        }
        if path.is_dir() {
            collect(&path, out)?;
        } else if is_source(&path) {
            out.push(path);
        }
    }
    Ok(())
}

fn wire_supported(expr: &Expr) -> bool {
    match &expr.kind {
        ExprKind::NumericBuffer(_) => false,
        ExprKind::List(items)
        | ExprKind::Call(_, items)
        | ExprKind::DomainCall(_, items) => items.iter().all(wire_supported),
        ExprKind::Pair(head, tail) => wire_supported(head) && wire_supported(tail),
        _ => true,
    }
}

fn bits(bytes: &[u8]) -> String {
    let mut out = String::with_capacity(bytes.len() * 9);
    for (i, byte) in bytes.iter().enumerate() {
        if i != 0 {
            out.push(' ');
        }
        use std::fmt::Write as _;
        write!(&mut out, "{byte:08b}").expect("String write");
    }
    out.push('\n');
    out
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = env::args().skip(1);
    let root = PathBuf::from(args.next().ok_or("usage: binary_master_export ROOT OUT")?);
    let dest = PathBuf::from(args.next().ok_or("usage: binary_master_export ROOT OUT")?);
    if args.next().is_some() {
        return Err("usage: binary_master_export ROOT OUT".into());
    }

    let root = fs::canonicalize(root)?;
    fs::create_dir_all(&dest)?;

    let mut sources = Vec::new();
    collect(&root, &mut sources)?;
    sources.sort();

    let mut exported = 0usize;
    let mut parse_failed = 0usize;
    let mut empty = 0usize;
    let mut wire_unsupported = 0usize;

    for path in sources {
        let source = match fs::read_to_string(&path) {
            Ok(x) => x,
            Err(error) => {
                eprintln!("SKIP_READ {}: {error}", path.display());
                continue;
            }
        };

        let parsed = match parse(&source) {
            Ok(x) => x,
            Err(error) => {
                parse_failed += 1;
                eprintln!("SKIP_PARSE {}: {error}", path.display());
                continue;
            }
        };
        if parsed.is_empty() {
            empty += 1;
            continue;
        }

        let lowered = lower_program(&parsed);
        if !lowered.iter().all(wire_supported) {
            wire_unsupported += 1;
            eprintln!("SKIP_WIRE_UNSUPPORTED {}: lowered AST contains runtime-only NumericBuffer", path.display());
            continue;
        }
        let wire = wire_encode_program(&lowered);
        let decoded = wire_decode_program(&wire)
            .ok_or_else(|| format!("wire decode failed after encode: {}", path.display()))?;
        let reencoded = wire_encode_program(&decoded);
        if reencoded != wire {
            return Err(format!("wire round-trip changed bytes: {}", path.display()).into());
        }

        let rel = path.strip_prefix(&root)?;
        let mut target = dest.join(rel);
        let file_name = target
            .file_name()
            .and_then(|x| x.to_str())
            .ok_or("non-UTF8 output filename")?
            .to_owned();
        target.set_file_name(format!("{file_name}.wire.bits"));
        if let Some(parent) = target.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::write(&target, bits(&wire))?;
        exported += 1;
        println!("EXPORT {} -> {}", rel.display(), target.strip_prefix(&dest)?.display());
    }

    println!("SUMMARY exported={exported} parse_failed={parse_failed} empty={empty} wire_unsupported={wire_unsupported}");
    if exported == 0 {
        return Err("no parseable source files exported".into());
    }
    Ok(())
}
