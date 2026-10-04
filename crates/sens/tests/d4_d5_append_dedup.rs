//! #3287 — D4 APPEND vs revoked D5 APPEND differential probe.
//! Research-only: prints exact outcomes; changes no semantic authority.

use sens::{
    eval_parsed_expressions, eval_program, load_core_library, parse, Bit4, Bit5, CoreD4, CoreD5,
    DomainIdentity, Expr, ExprKind, Session, Span,
};

fn run_exact(identity: DomainIdentity, args_source: &str) -> Result<String, String> {
    let mut session = Session::default();
    load_core_library(&mut session).map_err(|e| format!("load-core: {e:?}"))?;

    let wrapped = format!("(__probe__ {args_source})");
    let mut parsed = parse(&wrapped).map_err(|e| format!("parse: {e:?}"))?;
    let mut form = parsed.remove(0);
    let ExprKind::List(items) = form.kind else { return Err("wrapper-not-list".into()); };
    let mut items = items.to_vec();
    items[0] = Expr {
        kind: ExprKind::DomainIdentity(identity),
        span: Span { start: 0, end: "__probe__".len() },
    };
    form.kind = ExprKind::List(items.into());
    eval_parsed_expressions(&[form], &mut session)
        .map(|o| o.value.to_string())
        .map_err(|e| format!("{:?}: {}", e.kind, e.message))
}

fn run_surface(source: &str) -> Result<String, String> {
    let mut session = Session::default();
    load_core_library(&mut session).map_err(|e| format!("load-core: {e:?}"))?;
    eval_program(source, &mut session)
        .map(|o| o.value.to_string())
        .map_err(|e| format!("{:?}: {}", e.kind, e.message))
}

#[test]
fn ratified_d4_append_owns_the_one_live_semantics() {
    let d4 = DomainIdentity::D4(CoreD4::from_word(Bit4::new(0b1111).unwrap()));
    let d5 = DomainIdentity::D5(CoreD5::from_word(Bit5::new(0b10000).unwrap()));

    let cases = [
        ("empty-empty", "'() '()", "(append (quote ()) (quote ()))"),
        ("empty-list", "'() '(a b)", "(append (quote ()) (quote (a b)))"),
        ("list-empty", "'(a b) '()", "(append (quote (a b)) (quote ()))"),
        ("proper", "'(a b) '(c d)", "(append (quote (a b)) (quote (c d)))"),
        ("nested", "'((a b) c) '(d)", "(append (quote ((a b) c)) (quote (d)))"),
        ("dotted-right", "'(a b) '(c . d)", "(append (quote (a b)) (quote (c . d)))"),
    ];

    for (name,args,surface_source) in cases {
        let exact = run_exact(d4, args).unwrap_or_else(|e| panic!("{name}: D4 failed: {e}"));
        let surface = run_surface(surface_source)
            .unwrap_or_else(|e| panic!("{name}: surface failed: {e}"));
        assert_eq!(exact, surface, "{name}: D4 and surface APPEND diverged");

        let revoked = run_exact(d5, args).expect_err("revoked D5 APPEND must fail closed");
        assert!(
            revoked.contains("not callable") || revoked.contains("no admitted"),
            "{name}: unexpected revoked-D5 error: {revoked}"
        );
        println!("APPEND-DEDUP case={name} result={exact}");
    }

    let d4_bad = run_exact(d4, "'(a . b) '(c)").expect_err("D4 must reject improper left spine");
    let surface_bad = run_surface("(append (quote (a . b)) (quote (c)))")
        .expect_err("surface must reject improper left spine");
    assert!(
        d4_bad.contains("UnsatisfiedConditional"),
        "unexpected D4 improper-left error: {d4_bad}"
    );
    assert!(
        surface_bad.contains("UnsatisfiedConditional"),
        "unexpected surface improper-left error: {surface_bad}"
    );

    let d5_bad = run_exact(d5, "'(a . b) '(c)")
        .expect_err("revoked D5 APPEND must remain uncallable even on error boundary");
    assert!(d5_bad.contains("not callable") || d5_bad.contains("no admitted"));
}

#[test]
fn historical_append_semantics_are_already_d1_d4_derivable() {
    // Existing independent proof is kept as the semantic control:
    // crates/sens/tests/post_d4_append_derivation.rs.
    // This assertion guards that the evidence file still exists in this tree.
    assert!(std::path::Path::new("tests/post_d4_append_derivation.rs").exists()
        || std::path::Path::new("crates/sens/tests/post_d4_append_derivation.rs").exists());
}
