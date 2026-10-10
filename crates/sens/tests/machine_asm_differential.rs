use sens::{eval_program, load_core_library, Session};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn load_lisp_file(path: &str, session: &mut Session) {
    let path = repo_root().join(path);
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()));
    eval_program(&source, session)
        .unwrap_or_else(|error| panic!("{} must load as ordinary sens: {error}", path.display()));
}

fn machine_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap before external assembler witness");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    session
}

fn parse_byte_list(rendered: &str) -> Vec<u8> {
    rendered
        .trim_start_matches('(')
        .trim_end_matches(')')
        .split_whitespace()
        .filter(|token| !token.is_empty())
        .map(|token| token.parse().expect("encoded machine byte must fit u8"))
        .collect()
}

fn sens_bytes(form: &str, session: &mut Session) -> Vec<u8> {
    let source = format!("(x86-encode-admitted-program (quote ({form})))");
    let rendered = eval_program(&source, session)
        .unwrap_or_else(|error| panic!("SENS encoder rejected {form}: {error}"))
        .value
        .to_string();
    parse_byte_list(&rendered)
}

fn run(command: &str, args: &[&str]) -> Output {
    Command::new(command)
        .args(args)
        .output()
        .unwrap_or_else(|error| panic!("required external witness tool {command} is unavailable: {error}"))
}

fn run_ok(command: &str, args: &[&str]) -> Output {
    let output = run(command, args);
    assert!(
        output.status.success(),
        "{command} {args:?} failed\nstdout:\n{}\nstderr:\n{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    output
}

fn tool_version(command: &str, args: &[&str]) -> String {
    let output = run_ok(command, args);
    let text = if output.stdout.is_empty() {
        String::from_utf8_lossy(&output.stderr).into_owned()
    } else {
        String::from_utf8_lossy(&output.stdout).into_owned()
    };
    text.lines().next().unwrap_or("<no version line>").to_string()
}

fn extract_text(object: &Path, binary: &Path) -> Vec<u8> {
    let object_s = object.to_string_lossy();
    let binary_s = binary.to_string_lossy();
    run_ok(
        "objcopy",
        &[
            "-O",
            "binary",
            "--only-section=.text",
            object_s.as_ref(),
            binary_s.as_ref(),
        ],
    );
    fs::read(binary).unwrap_or_else(|error| panic!("{} must be readable: {error}", binary.display()))
}

fn gas_bytes(dir: &Path, name: &str, body: &str) -> Vec<u8> {
    let source = dir.join(format!("{name}.gas.s"));
    let object = dir.join(format!("{name}.gas.o"));
    let binary = dir.join(format!("{name}.gas.bin"));
    fs::write(
        &source,
        format!(".intel_syntax noprefix\n.text\n.global witness\nwitness:\n    {body}\n"),
    )
    .expect("write GAS witness source");

    let source_s = source.to_string_lossy();
    let object_s = object.to_string_lossy();
    run_ok("as", &["--64", "-o", object_s.as_ref(), source_s.as_ref()]);
    extract_text(&object, &binary)
}

fn nasm_bytes(dir: &Path, name: &str, body: &str) -> Vec<u8> {
    let source = dir.join(format!("{name}.nasm.asm"));
    let object = dir.join(format!("{name}.nasm.o"));
    let binary = dir.join(format!("{name}.nasm.bin"));
    fs::write(
        &source,
        format!("bits 64\nsection .text\nglobal witness\nwitness:\n    {body}\n"),
    )
    .expect("write NASM witness source");

    let source_s = source.to_string_lossy();
    let object_s = object.to_string_lossy();
    run_ok(
        "nasm",
        &["-f", "elf64", "-o", object_s.as_ref(), source_s.as_ref()],
    );
    extract_text(&object, &binary)
}

struct Case {
    name: &'static str,
    form: &'static str,
    gas: &'static str,
    nasm: &'static str,
}

#[test]
#[ignore = "external GAS/NASM witness; run in machine-asm-differential workflow"]
fn gas_and_nasm_match_lisp_owned_encoder_for_admitted_corpus() {
    let gas_version = tool_version("as", &["--version"]);
    let nasm_version = tool_version("nasm", &["-v"]);
    let objcopy_version = tool_version("objcopy", &["--version"]);

    eprintln!(
        "external witness tools: {gas_version} | {nasm_version} | {objcopy_version}"
    );

    assert!(
        gas_version.ends_with(" 2.42"),
        "review #4344 evidence before changing pinned GAS 2.42: {gas_version}"
    );
    assert_eq!(
        nasm_version, "NASM version 2.16.01",
        "review #4344 evidence before changing pinned NASM version"
    );
    assert!(
        objcopy_version.ends_with(" 2.42"),
        "review #4344 evidence before changing pinned objcopy 2.42: {objcopy_version}"
    );

    let temp = std::env::temp_dir().join(format!("sens-asm-differential-{}", std::process::id()));
    if temp.exists() {
        fs::remove_dir_all(&temp).expect("remove stale witness temp directory");
    }
    fs::create_dir_all(&temp).expect("create witness temp directory");

    let cases = [
        Case {
            name: "add_rax_rcx",
            form: "(add-r64-r64 rax rcx)",
            gas: "add rax, rcx",
            nasm: "add rax, rcx",
        },
        Case {
            name: "add_r8_r9",
            form: "(add-r64-r64 r8 r9)",
            gas: "add r8, r9",
            nasm: "add r8, r9",
        },
        Case {
            name: "store_rdi_disp8_rax",
            form: "(mov-mem-disp8-r64 rdi 8 rax)",
            gas: "mov QWORD PTR [rdi + 8], rax",
            nasm: "mov qword [rdi + 8], rax",
        },
        Case {
            name: "load_rax_rdi_disp8",
            form: "(mov-r64-mem-disp8 rax rdi 8)",
            gas: "mov rax, QWORD PTR [rdi + 8]",
            nasm: "mov rax, qword [rdi + 8]",
        },
        Case {
            name: "store_r12_disp8_r9",
            form: "(mov-mem-disp8-r64 r12 8 r9)",
            gas: "mov QWORD PTR [r12 + 8], r9",
            nasm: "mov qword [r12 + 8], r9",
        },
        Case {
            name: "aesenc_xmm0_xmm1",
            form: "(aesenc-xmm-xmm xmm0 xmm1)",
            gas: "aesenc xmm0, xmm1",
            nasm: "aesenc xmm0, xmm1",
        },
        Case {
            name: "aesenc_xmm8_xmm9",
            form: "(aesenc-xmm-xmm xmm8 xmm9)",
            gas: "aesenc xmm8, xmm9",
            nasm: "aesenc xmm8, xmm9",
        },
        Case {
            name: "pclmulqdq_xmm0_xmm1_11",
            form: "(pclmulqdq-xmm-xmm-imm8 xmm0 xmm1 17)",
            gas: "pclmulqdq xmm0, xmm1, 0x11",
            nasm: "pclmulqdq xmm0, xmm1, 0x11",
        },
        Case {
            name: "pclmulqdq_xmm8_xmm9_01",
            form: "(pclmulqdq-xmm-xmm-imm8 xmm8 xmm9 1)",
            gas: "pclmulqdq xmm8, xmm9, 0x01",
            nasm: "pclmulqdq xmm8, xmm9, 0x01",
        },
        Case {
            name: "ret",
            form: "(ret)",
            gas: "ret",
            nasm: "ret",
        },
    ];

    let mut session = machine_session();
    for case in cases {
        let sens = sens_bytes(case.form, &mut session);
        let gas = gas_bytes(&temp, case.name, case.gas);
        let nasm = nasm_bytes(&temp, case.name, case.nasm);

        assert_eq!(
            gas, sens,
            "{}: GAS bytes differ from Lisp-owned encoder for {}",
            case.name, case.form
        );
        assert_eq!(
            nasm, sens,
            "{}: NASM bytes differ from Lisp-owned encoder for {}",
            case.name, case.form
        );
    }

    fs::remove_dir_all(&temp).expect("clean witness temp directory");
}


// Окремий від зовнішніх асемблерів етапний свідок виклику.
// Якщо реальна збірка ще заблокована, звіт показує перший несправний вузол.
#[test]
#[ignore = "машинний GitHub-hosted маршрут; той самий профіль, що GAS/NASM"]
fn x86_encoder_callability_stage_probe() {
    let mut session = machine_session();
    let stages = [
        ("код_rax", "(x86-reg-code (quote rax))"),
        ("код_rcx", "(x86-reg-code (quote rcx))"),
        ("байти_add", "(x86-encode-add-r64-r64 (quote rax) (quote rcx))"),
        (
            "одна_інструкція",
            "(x86-encode-admitted-instruction (quote (add-r64-r64 rax rcx)))",
        ),
        (
            "повна_програма",
            "(x86-encode-admitted-program (quote ((add-r64-r64 rax rcx))))",
        ),
    ];
    let mut failed = Vec::new();
    for (stage, source) in stages {
        match eval_program(source, &mut session) {
            Ok(observation) => eprintln!(
                "X86_ЕТАП_УСПІХ stage={stage} value={}",
                observation.value
            ),
            Err(error) => {
                eprintln!("X86_ЕТАП_БЛОКУВАННЯ stage={stage} error={error}");
                failed.push(stage);
            }
        }
    }
    assert!(
        failed.is_empty(),
        "Не доведено виклики x86-кодувальника на етапах: {failed:?}"
    );
}
