//! #3468 — current D4 APPEND / D5 CAAAR coordinate witness.
//! Test-only: verifies current exact-domain placement; changes no semantic authority.

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
fn current_d4_append_and_d5_caar_coordinates_do_not_alias() {
    let d4_append = DomainIdentity::D4(CoreD4::from_word(Bit4::new(0b1111).unwrap()));
    let d5_caaar = DomainIdentity::D5(CoreD5::from_word(Bit5::new(0b10000).unwrap()));

    let cases = [
        ("empty-empty", "'() '()", "(append (quote ()) (quote ()))"),
        ("empty-list", "'() '(a b)", "(append (quote ()) (quote (a b)))"),
        ("list-empty", "'(a b) '()", "(append (quote (a b)) (quote ()))"),
        ("proper", "'(a b) '(c d)", "(append (quote (a b)) (quote (c d)))"),
        ("nested", "'((a b) c) '(d)", "(append (quote ((a b) c)) (quote (d)))"),
        ("dotted-right", "'(a b) '(c . d)", "(append (quote (a b)) (quote (c . d)))"),
    ];

    for (name, args, surface_source) in cases {
        let exact =
            run_exact(d4_append, args).unwrap_or_else(|e| panic!("{name}: D4 failed: {e}"));
        let surface = run_surface(surface_source)
            .unwrap_or_else(|e| panic!("{name}: surface failed: {e}"));
        assert_eq!(exact, surface, "{name}: D4 and surface APPEND diverged");
        println!("APPEND-CURRENT case={name} result={exact}");
    }

    let caaar = run_exact(d5_caaar, "'(((a) b) c)")
        .unwrap_or_else(|e| panic!("D5:10000 CAAAR failed: {e}"));
    assert_eq!(caaar, "a", "D5:10000 must execute current CAAAR semantics");

    let not_append = run_exact(d5_caaar, "'(a b) '(c d)")
        .expect_err("D5:10000 must not accept APPEND's two-argument call shape");
    assert!(
        not_append.contains("expects 1 argument") && not_append.contains("received 2"),
        "unexpected D5:10000 non-alias error: {not_append}"
    );

    let d4_bad =
        run_exact(d4_append, "'(a . b) '(c)").expect_err("D4 must reject improper left spine");
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
}

#[test]
fn historical_append_semantics_are_already_d1_d4_derivable() {
    // Existing independent proof is kept as the semantic control:
    // crates/sens/tests/post_d4_append_derivation.rs.
    // This assertion guards that the evidence file still exists in this tree.
    assert!(std::path::Path::new("tests/post_d4_append_derivation.rs").exists()
        || std::path::Path::new("crates/sens/tests/post_d4_append_derivation.rs").exists());
}
