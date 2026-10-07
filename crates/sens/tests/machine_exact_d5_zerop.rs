use sens::{
    eval_parsed_expressions, eval_program, load_core_library, lower_program, parse, Bit5, CoreD5,
    DomainIdentity, Expr, ExprKind, Session, Span,
};
use std::fs;
use std::path::PathBuf;

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
    load_core_library(&mut session).expect("core");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/capability-axis.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);
    session
}

fn exact_d5_value(bits: u8, args: &str, session: &mut Session) -> sens::Value {
    let mut parsed = parse(&format!("(__d5_probe__ {args})")).expect("probe payload");
    let mut form = parsed.remove(0);
    let ExprKind::List(items) = form.kind else {
        panic!("probe list");
    };
    let mut items = items.to_vec();
    items[0] = Expr {
        kind: ExprKind::DomainIdentity(DomainIdentity::D5(CoreD5::from_word(
            Bit5::new(bits).expect("D5 bits"),
        ))),
        span: Span::default(),
    };
    form.kind = ExprKind::List(items.into());
    eval_parsed_expressions(&[form], session)
        .expect("exact D5 call")
        .value
}

fn parse_bytes(rendered: &str) -> Vec<u8> {
    rendered
        .trim_start_matches('(')
        .trim_end_matches(')')
        .split_whitespace()
        .map(|token| token.parse::<u8>().expect("machine byte"))
        .collect()
}

#[derive(Debug, PartialEq, Eq)]
struct ZeroTail {
    condition_code: u8,
    set_register: u8,
    result_register: u8,
}

fn decode_zero_tail(bytes: &[u8]) -> Option<ZeroTail> {
    // Two MOV r64,imm64 instructions: input + literal zero.
    let tail = bytes.get(20..)?;
    let [
        cmp_rex,
        cmp_opcode,
        cmp_modrm,
        set_prefix,
        set_opcode,
        set_modrm,
        movzx_rex,
        movzx_prefix,
        movzx_opcode,
        movzx_modrm,
        ret,
    ] = tail
    else {
        return None;
    };

    if (*cmp_rex, *cmp_opcode, *cmp_modrm) != (0x48, 0x39, 0xC8) {
        return None;
    }
    if (*set_prefix, *set_opcode, *set_modrm) != (0x0F, 0x94, 0xC0) {
        return None;
    }
    if (*movzx_rex, *movzx_prefix, *movzx_opcode, *movzx_modrm) != (0x48, 0x0F, 0xB6, 0xC0)
        || *ret != 0xC3
    {
        return None;
    }

    Some(ZeroTail {
        condition_code: set_opcode - 0x90,
        set_register: set_modrm & 0b111,
        result_register: (movzx_modrm >> 3) & 0b111,
    })
}

#[test]
fn current_zerop_surface_lowers_to_exact_d5_identity() {
    let lowered = lower_program(&parse("(нуль? 0)").expect("current D5 ZEROP source"));
    let ExprKind::DomainCall(identity, args) = &lowered[0].kind else {
        panic!("ZEROP must lower to exact DomainCall");
    };
    assert_eq!(identity.width(), 5);
    assert_eq!(identity.packed_bits(), 0b01000);
    assert_eq!(args.len(), 1);
}

#[test]
fn exact_d5_zerop_language_law_crosses_only_as_d1() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core");

    for (args, expected) in [
        ("0", true),
        ("1", false),
        ("3/1000000", true),
        ("-3/1000000", true),
        ("31/10000000", false),
    ] {
        let value = exact_d5_value(0b01000, args, &mut session);
        assert_eq!(
            value.as_predicate_bit(),
            Some(expected),
            "D5:01000 ZEROP({args}) must cross as exact D1 PredicateBit"
        );
        assert!(
            !matches!(value, sens::Value::Number(_, _) | sens::Value::Rational(_)),
            "language-visible ZEROP result must not remain numeric 0/1"
        );
    }
}

#[test]
fn bounded_exact_integer_zerop_reaches_admitted_internal_bit_bytes() {
    let mut session = machine_session();

    assert_eq!(
        eval_program("(machine-capabilities-for-domain 01000)", &mut session)
            .expect("ZEROP machine capability")
            .value
            .to_string(),
        "((integer-zero-test bounded-nonnegative-u64 internal-bit-d1-boundary))"
    );

    let forms = eval_program(
        "(x86-lower-current-zerop-u64-forms 01000 0)",
        &mut session,
    )
    .expect("ZEROP forms")
    .value
    .to_string();
    assert_eq!(
        forms,
        "((mov-r64-imm64 rax 0) (mov-r64-imm64 rcx 0) (cmp-r64-r64 rax rcx) (sete-r8 al) (movzx-r64-r8 rax al) (ret))"
    );

    for value in ["0", "42"] {
        let rendered = eval_program(
            &format!("(x86-encode-current-zerop-bit 01000 {value})"),
            &mut session,
        )
        .expect("ZEROP admitted bytes")
        .value
        .to_string();
        assert_eq!(
            decode_zero_tail(&parse_bytes(&rendered)),
            Some(ZeroTail {
                condition_code: 4,
                set_register: 0,
                result_register: 0,
            }),
            "SETE/MOVZX proof tail for value {value}"
        );
    }
}

#[test]
fn zerop_native_slice_fails_closed_outside_exact_integer_rectangle() {
    let mut session = machine_session();

    // Critical semantic counterexample: the language law says YES here because
    // of the historical epsilon policy, while integer CMP-to-zero says false.
    // Therefore this value must never enter the native integer slice.
    for form in [
        "(x86-encode-current-zerop-bit 01000 3/1000000)",
        "(x86-encode-current-zerop-bit 01000 -3/1000000)",
        "(x86-encode-current-zerop-bit 01000 31/10000000)",
        "(x86-encode-current-zerop-bit 01000 -1)",
        "(x86-encode-current-zerop-bit 01000 18446744073709551616)",
    ] {
        assert_eq!(
            eval_program(form, &mut session)
                .unwrap_or_else(|error| panic!("ZEROP guard failed: {form}: {error}"))
                .value
                .to_string(),
            "exact-d5-fallback-required",
            "{form} must preserve the full exact/historical ZEROP law"
        );
    }

    assert_eq!(
        eval_program("(x86-encode-current-zerop-bit 101 0)", &mut session)
            .expect("wrong exact identity fails closed")
            .value
            .to_string(),
        "unsupported-current-domain-zerop-u64"
    );
}

#[test]
fn zerop_machine_proof_does_not_publish_numeric_boolean_language_semantics() {
    let source =
        fs::read_to_string(repo_root().join("lib/machine/lowering/semantic-x86-64.lisp"))
            .expect("semantic x86 lowering");
    let start = source
        .find("; #4064 exact D5:01000 ZEROP bounded machine proof.")
        .expect("#4064 ZEROP proof block");
    let end = source[start..]
        .find("; #3996 exact-domain structural D3 dispatcher.")
        .map(|offset| start + offset)
        .unwrap_or(source.len());
    let block = &source[start..end];

    assert!(block.contains("(00001001 x86-encode-current-zerop-bit"));
    assert!(block.contains("exact-d5-fallback-required"));
    for forbidden in [
        "x86-call-current-zerop",
        "numeric-boolean",
        "machine-predicate-number",
    ] {
        assert!(
            !block.contains(forbidden),
            "ZEROP machine proof must not publish {forbidden}"
        );
    }

    let profile =
        fs::read_to_string(repo_root().join("lib/machine/profile/current-domain-x86-64.lisp"))
            .expect("current profile");
    assert!(profile.contains(
        "(01000 proof \"CMP+SETE+MOVZX / exact integer internal bit; D1 boundary\")"
    ));
    assert!(!profile.contains("00001000 direct"));
}
