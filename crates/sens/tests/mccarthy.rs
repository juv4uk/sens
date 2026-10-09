use sens::{
    eval_program, parse, Environment, ErrorKind, Exactness, Expr, ExprKind, Rational, Session,
    Value,
};

/// Looks up `key` in a sens alist `((k1 . v1) (k2 . v2) ...)`, already
/// parsed as `Expr`s (data, not evaluated) — used by the two
/// `tests/fixtures/conformance.lisp`-consuming tests below, which read the
/// fixture file as reader-level data rather than executing it.
fn alist_str<'a>(entries: &'a [Expr], key: &str) -> Option<&'a str> {
    entries.iter().find_map(|entry| {
        let ExprKind::Pair(k, v) = &entry.kind else {
            return None;
        };
        let ExprKind::Symbol(name) = &k.kind else {
            return None;
        };
        if &**name != key {
            return None;
        }
        match &v.kind {
            ExprKind::String(s) => Some(s.as_ref()),
            _ => None,
        }
    })
}

/// Same as `alist_str`, but for a numeric field (e.g. `tier`).
fn alist_number(entries: &[Expr], key: &str) -> Option<f64> {
    entries.iter().find_map(|entry| {
        let ExprKind::Pair(k, v) = &entry.kind else {
            return None;
        };
        let ExprKind::Symbol(name) = &k.kind else {
            return None;
        };
        if &**name != key {
            return None;
        }
        match &v.kind {
            ExprKind::Number(n, _) => Some(*n),
            _ => None,
        }
    })
}

fn eval(source: &str) -> Value {
    eval_program(source, &mut Session::default()).unwrap().value
}

#[test]
fn division_is_an_exact_reduced_rational() {
    assert_eq!(
        eval("(/ 5 6 8 7)"),
        Value::Rational(Rational::new(5, 336).unwrap())
    );
    assert_eq!(eval("(/ 8 4)"), Value::Number(2.0, Exactness::Exact));
    assert_eq!(
        eval("(/ (/ 2 3))"),
        Value::Rational(Rational::new(3, 2).unwrap())
    );
}

#[test]
fn exact_arithmetic_handles_products_beyond_i64_range() {
    let result = eval_program("(* 3037000500 3037000500)", &mut Session::default()).unwrap();
    assert_eq!(result.value.to_string(), "9223372037000250000");
}

#[test]
fn bare_large_integer_literals_remain_exact() {
    let literal = "123456789012345678901234567890";
    assert_eq!(eval(literal).to_string(), literal);
    assert_eq!(
        eval(&format!("(+ {literal} 1)")).to_string(),
        "123456789012345678901234567891"
    );
}

/// The case that actually matters, more than any single large literal:
/// results *computed* via repeated exact arithmetic growing past the old
/// i64 ceiling. `(/ 1 1)` forces the exact path from the start (a bare
/// integer literal this large would itself parse as inexact f64 — see
/// docs/language-core.md — a separate, still-open question from whether
/// *arithmetic* stays exact past i64, which this answers: yes). Verified
/// against Python's `math.factorial(30)` by hand before writing this.
#[test]
fn arithmetic_promotes_exact_integers_and_preserves_inexact_numbers() {
    assert_eq!(
        eval("(+ (/ 1 3) (/ 1 3))"),
        Value::Rational(Rational::new(2, 3).unwrap())
    );
    assert_eq!(
        eval("(- 1 (/ 1 3))"),
        Value::Rational(Rational::new(2, 3).unwrap())
    );
    assert_eq!(
        eval("(* (/ 2 3) (/ 9 4))"),
        Value::Rational(Rational::new(3, 2).unwrap())
    );
    assert_eq!(
        eval("(- (/ 1 3))"),
        Value::Rational(Rational::new(-1, 3).unwrap())
    );
    assert_eq!(
        eval("(+ (/ 1 2) 0.25)"),
        Value::Rational(Rational::new(3, 4).unwrap())
    );
    assert_eq!(
        eval("(+ (/ 1 2) (/ 1 2))"),
        Value::Number(1.0, Exactness::Exact)
    );
}

#[test]
fn print_appends_to_output_and_returns_its_argument() {
    let result = eval_program("(print \"radio\")", &mut Session::default()).unwrap();
    assert_eq!(result.value, Value::String("radio".into()));
    assert_eq!(result.output, vec!["\"radio\"".to_string()]);
}

#[test]
fn print_composes_inside_expressions_and_accumulates_in_order() {
    let result = eval_program("(+ (print 1) (print 2))", &mut Session::default()).unwrap();
    assert_eq!(result.value, Value::Number(3.0, Exactness::Exact));
    assert_eq!(result.output, vec!["1".to_string(), "2".to_string()]);
}

#[test]
fn read_parses_text_into_data_without_evaluating_it() {
    assert_eq!(
        eval(r#"(read "(+ 1 2)")"#),
        Value::list([
            Value::Symbol("+".into()),
            Value::Number(1.0, Exactness::Exact),
            Value::Number(2.0, Exactness::Exact),
        ])
    );
    assert_eq!(eval(r#"(read "radio")"#), Value::Symbol("radio".into()));
    assert_eq!(
        eval(r#"(read "42")"#),
        Value::Number(42.0, Exactness::Exact)
    );
}

#[test]
fn read_rejects_non_string_arguments_and_multi_expression_input() {
    let non_string = eval_program("(read 42)", &mut Session::default()).unwrap_err();
    assert_eq!(non_string.kind, ErrorKind::Type);

    let two_expressions = eval_program(r#"(read "1 2")"#, &mut Session::default()).unwrap_err();
    assert_eq!(two_expressions.kind, ErrorKind::InvalidForm);

    let too_many_args = eval_program(r#"(read "1" "2")"#, &mut Session::default()).unwrap_err();
    assert_eq!(too_many_args.kind, ErrorKind::Arity);
}

#[test]
fn print_inside_a_closure_shares_the_root_sessions_output() {
    // Environment::child() must share the parent's output sink (not start a
    // fresh one per call frame), or `print` inside a lambda body would be
    // invisible to the caller's EvalResult.output.
    let source = "((lambda () (print (quote inside)) (quote done)))";
    let result = eval_program(source, &mut Session::default()).unwrap();
    assert_eq!(result.value, Value::Symbol("done".into()));
    assert_eq!(result.output, vec!["inside".to_string()]);
}

#[test]
fn tail_recursion_uses_constant_rust_stack() {
    let depth = 5_000;
    let mut definitions = (0..depth - 1)
        .map(|index| format!("(def step-{index} (lambda () (step-{})))", index + 1))
        .collect::<Vec<_>>();
    definitions.push(format!("(def step-{} (lambda () (quote done)))", depth - 1));
    let source = format!("{} (step-0)", definitions.join(" "));
    assert_eq!(eval(&source), Value::Symbol("done".into()));
}

#[test]
fn reader_supports_unicode_comments_and_quote_sugar() {
    let expressions = parse("; коментар\n'радіо").unwrap();
    assert_eq!(expressions.len(), 1);
    assert_eq!(eval("(quote радіо)"), Value::Symbol("радіо".into()));
}

#[test]
fn reports_structured_errors_with_source_spans() {
    let error = eval_program("(car (quote ()))", &mut Session::default()).unwrap_err();
    assert_eq!(error.kind, ErrorKind::Type);
    assert_eq!((error.span.start, error.span.end), (0, 16));

    let parse_error = parse("(cons 'a").unwrap_err();
    assert_eq!(parse_error.kind, ErrorKind::Parse);
    assert_eq!(parse_error.span.start, 0);
}

#[test]
fn lexical_child_reads_parent_without_mutating_it() {
    let parent = sens::Environment::root();
    let child = parent.child();
    child.define("station", Value::Symbol("UR5ABC".into()));
    assert_eq!(parent.get("station"), None);
}

#[test]
fn lambda_captures_lexical_environment_and_keeps_parameters_local() {
    let mut session = Session::default();
    session
        .environment
        .define("station", Value::Symbol("radio".into()));

    let result = eval_program(
        "((lambda (suffix) (cons station suffix)) (quote (antenna)))",
        &mut session,
    )
    .unwrap();

    assert_eq!(
        result.value,
        Value::list([
            Value::Symbol("radio".into()),
            Value::Symbol("antenna".into())
        ])
    );
    assert_eq!(session.environment.get("suffix"), None);
}

#[test]
fn print_escapes_embedded_quotes_and_backslashes_so_read_can_reconstruct_the_string() {
    // A string value containing a literal " and \, built via sens source
    // escaping — the *value* itself is `(eq? "radio" "radio")`, 22 chars,
    // no backslashes in the value, just in how it's written here.
    let source = r#""(eq? \"radio\" \"radio\")""#;
    let value = eval_program(source, &mut Session::default()).unwrap().value;
    // `to_string()` is now valid sens source for that same string literal
    // — parsing it again (not? wrapping in another layer of quoting) should
    // reconstruct the identical value.
    let printed = value.to_string();
    let reread = eval_program(&printed, &mut Session::default())
        .unwrap()
        .value;
    assert_eq!(
        reread, value,
        "printed text should read back to the same string value"
    );
}

/// `princ` — the `princ`/`display` half of the classic Lisp print-function
/// pair `print` (fixed above) is the other half of: raw text, no quotes or
/// escapes, for output meant for a person or reassembled as literal source
/// text (e.g. a tool generating new .my files), never re-parsed as data.
/// `princ` — «princ»/«display»-polovyna klasychnoi Lisp-pary funktsii druku,
/// druhu polovynu yakoi skladaie polahodzhenyi vyshche `print`: syryi tekst, bez
/// lapok i ekranuvannia, dlia vyvodu, pryznachenoho liudyni chy povtornomu
/// skladanniu yak bukvalnyi syrtsevyi tekst (napr. instrument, shcho heneruie
/// novyi `.my`-fail), nikoly ne dlia povtornoho parsynhu yak danykh.
#[test]
fn list_is_a_sens_function_in_core_my_not_a_rust_builtin() {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    let result = eval_program("(list 1 2 3)", &mut session).unwrap();
    assert_eq!(
        result.value,
        Value::list(vec![
            Value::Number(1.0, Exactness::Exact),
            Value::Number(2.0, Exactness::Exact),
            Value::Number(3.0, Exactness::Exact)
        ])
    );
    // Without core.my loaded, "list" is an ordinary unbound symbol now —
    // regression-tests that it really did leave the Rust special-form table.
    let unbound = eval_program("(list 1 2 3)", &mut Session::default()).unwrap_err();
    assert!(matches!(unbound.kind, ErrorKind::UnknownSymbol | ErrorKind::Type));
}

/// The echo fallback is an *interaction policy of the interactive REPL*, not
/// language semantics — the evaluator itself must still report an unknown
/// standalone symbol as `UnknownSymbol`, exactly the same as inside any form.
/// (The REPL catches the same error and rewrites *only its own greeting*.)
/// Echo-fallback — tse *polityka vzaiemodii interaktyvnoho REPL*, ne semantyka
/// movy: sam evaluator musi yak ranishe vidpovidaty nevidomym symvolom
/// `UnknownSymbol`, tochno tak samo, yak vseredyni bud-yakoi formy. (REPL
/// lohyt toi samyi error i perepysuie lyshe *vlasne vitannia*.)
#[test]
fn conformance_fixture_exprs_parse_as_single_form() {
    let forms = parse(include_str!("../../../tests/fixtures/conformance.lisp"))
        .expect("conformance.lisp should parse as valid sens source");

    for form in &forms {
        let ExprKind::List(entries) = &form.kind else {
            panic!("each top-level form in conformance.lisp should be an alist: {form:?}");
        };
        // Historical truthiness belongs to archaeology, not the current domain reader.
        if alist_str(entries, "role") == Some("historical-compatibility") {
            continue;
        }
        let expr = alist_str(entries, "expr").expect("fixture needs an \"expr\" string");
        let expected_error = alist_str(entries, "error");

        let parsed = parse(expr);
        match (parsed, expected_error) {
            (Ok(exprs), None) => {
                assert!(
                    !exprs.is_empty(),
                    "fixture expr with expected value must parse as at least one form: {expr}"
                );
            }
            (Ok(exprs), Some("NumericOverflow")) => {
                assert!(
                    !exprs.is_empty(),
                    "fixture expr expecting NumericOverflow must parse as at least one form: {expr}"
                );
            }
            (Err(e), Some("NumericOverflow")) => {
                assert_eq!(
                    e.kind,
                    ErrorKind::NumericOverflow,
                    "fixture expr expecting NumericOverflow must fail with NumericOverflow, got {:?}: {expr}",
                    e.kind
                );
            }
            (Err(e), Some(expected)) => {
                panic!(
                    "fixture expr expecting error {expected} failed to parse with {:?}: {expr}",
                    e.kind
                );
            }
            (Ok(exprs), Some(expected)) => {
                assert_eq!(
                    exprs.len(),
                    1,
                    "fixture expr expecting error {expected} must parse as exactly one form, got {}: {expr}",
                    exprs.len()
                );
            }
            (Err(e), None) => {
                panic!(
                    "fixture expr with expected value failed to parse with {:?}: {expr}",
                    e.kind
                );
            }
        }
    }
}

#[test]
fn macro_conformance_tests_from_my() {
    let forms = parse(include_str!("../../../tests/fixtures/macro-conformance.lisp"))
        .expect("macro-conformance.lisp should parse as valid sens source");

    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("lib/core.my should load before macro-conformance fixtures run");

    for form in &forms {
        let ExprKind::List(entries) = &form.kind else {
            panic!("each top-level form in macro-conformance.lisp should be an alist: {form:?}");
        };
        let expr = alist_str(entries, "expr").expect("fixture needs an \"expr\" string");

        // Capability fixtures (e.g. the tcp-connect type-error entry) are only
        // meaningful when a host layer is installed; this core-side runner
        // deliberately installs none, so such entries are skipped here and
        // verified in crates/sens-host/tests instead. Skipping - not
        // re-baselining - keeps the fixture itself the single contract.
        if let Some(head) = expr
            .strip_prefix('(')
            .and_then(|rest| rest.split_whitespace().next())
        {
            if !sens::capability_installed(head) {
                continue;
            }
        }

        if let Some(expected_error) = alist_str(entries, "error") {
            let error = eval_program(expr, &mut session).expect_err(&format!(
                "expected an error but evaluation succeeded: {expr}"
            ));
            assert_eq!(
                format!("{:?}", error.kind),
                expected_error,
                "wrong error kind for expression: {expr}"
            );
            continue;
        }

        let expected = alist_str(entries, "expected")
            .expect("fixture needs an \"expected\" string (or an \"error\" string)");
        let actual = eval_program(expr, &mut session)
            .unwrap_or_else(|e| panic!("fixture failed: {e}\nexpr: {expr}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "Failed on expression: {}", expr);
    }
}

#[test]
fn linter_tests_from_my() {
    let forms = parse(include_str!("../../../tests/fixtures/linter.lisp"))
        .expect("linter.my should parse as valid sens source");

    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("lib/core.my should load before linter fixtures run");
    eval_program(include_str!("../../../lib/linter.lisp"), &mut session)
        .expect("lib/linter.my should load before linter fixtures run");

    for form in &forms {
        let ExprKind::List(entries) = &form.kind else {
            panic!("each top-level form in linter.my should be an alist: {form:?}");
        };
        let expr = alist_str(entries, "expr").expect("fixture needs an \"expr\" string");

        let expected = alist_str(entries, "expected")
            .expect("fixture needs an \"expected\" string (or an \"error\" string)");
        let actual = eval_program(expr, &mut session)
            .unwrap_or_else(|e| panic!("fixture failed: {e}\nexpr: {expr}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "Failed on expression: {}", expr);
    }
}

// Minimal symbol/string introspection this project held off on for a long
// time (CLAUDE.md: don't grow the Rust surface) — added deliberately when
// lib/clips-import.lisp's Step 2 needed to strip CLIPS's `?` prefix off a
// variable symbol, which is impossible from within sens itself without
// some way to look at a symbol's characters.

#[test]
fn string_slice_rejects_non_integer_or_negative_indices() {
    for source in [
        r#"(string-slice "abc" 1.5 2)"#,
        r#"(string-slice "abc" -1 2)"#,
        r#"(string-slice "abc" "1" 2)"#,
    ] {
        assert_eq!(
            eval_program(source, &mut Session::default())
                .unwrap_err()
                .kind,
            ErrorKind::Type,
            "source: {source}"
        );
    }
}

#[test]
fn symbol_predicate_is_not_a_host_builtin() {
    // An uninstalled language-level function cannot acquire host semantics.
    assert_eq!(
        eval_program("(symbol? (quote hello))", &mut Session::default())
            .unwrap_err()
            .kind,
        ErrorKind::Type
    );
}

#[test]
fn a_multi_element_dotted_list_reads_as_nested_pairs() {
    assert_eq!(eval("(quote (a b . c))").to_string(), "(a b . c)");
    assert_eq!(eval("(car (quote (a b . c)))").to_string(), "a");
    assert_eq!(eval("(car (cdr (quote (a b . c))))").to_string(), "b");
    assert_eq!(eval("(cdr (cdr (quote (a b . c))))").to_string(), "c");
}

#[test]
fn a_dotted_pair_used_directly_as_code_is_an_invalid_form() {
    // Only meaningful as data (inside `quote`, or via `read`) — a dotted
    // pair is not a valid call form, the same way `(1 2 3)` isn't.
    let error = eval_program("(p . 0)", &mut Session::default())
        .expect_err("expected an InvalidForm error");
    assert_eq!(error.kind, ErrorKind::InvalidForm);
}

/// `my-lisp-constitution.lisp` is a *generated projection* over
/// `tests/fixtures/conformance.lisp` (`scripts/build-constitution.lisp`
/// regenerates it) — the same one-source-plus-projection shape
/// `lib/knowledge.my`'s `*knowledge-journal*` uses for runtime state,
/// applied here to documentation instead. This test is the CI-enforced
/// half of that pattern: if someone appends a fixture to `conformance.lisp`
/// and forgets to rerun the generator, the two files silently drift — this
/// test turns that into a loud, immediate failure instead. Both files are
/// sens data now (2026-08-09, moved off JSON), so this test parses them
/// the same way `conformance_tests_from_my` does above, not via serde_json.
/// `my-lisp-constitution.lisp` — tse *zhenerovana proektsiia* nad
/// `tests/fixtures/conformance.lisp` (perehenerovuie `scripts/build-constitution.lisp`)
/// — ta sama forma "odne dzherelo + proektsiia", yaku `*knowledge-journal*`
/// z `lib/knowledge.my` vykorystovuie dlia rantaim-stanu, zastosovana tut do
/// dokumentatsii. Tsei test — prymusova CI-polovyna toho paternu: yakshcho khtos
/// dodast fiksturu v `conformance.lisp` i zabude pereheneruvaty, tsi dva
/// faily movchky roziidutsia — tsei test peretvoriuie tse na nehainyi, huchnyi
/// proval. Obydva faily teper sens-dani (2026-08-09, pereneseno z JSON),
/// tozh tsei test parsyt yikh tak samo, yak `conformance_tests_from_my` vyshche,
/// ne cherez `serde_json`.
#[test]
fn constitution_my_stays_in_sync_with_conformance_my() {
    let conformance = parse(include_str!("../../../tests/fixtures/conformance.lisp"))
        .expect("conformance.lisp should parse as valid sens source");

    let constitution_forms = parse(include_str!("../../../my-lisp-constitution.lisp"))
        .expect("my-lisp-constitution.lisp should parse as valid sens source");
    let fixtures: Vec<&[Expr]> = constitution_forms
        .iter()
        .filter_map(|form| {
            let ExprKind::List(items) = &form.kind else {
                return None;
            };
            // `(print (cons (quote fixture) fixture))` in build-constitution.lisp
            // prints as `(fixture (expr . ...) (expected . ...) ...)` — the
            // fixture alist's own entries spliced in as `cons`'s tail, not
            // wrapped in a nested list, since `fixture` here is already a
            // proper list and `(a . (b c))` prints flat as `(a b c)`.
            let (head, entries) = items.split_first()?;
            let ExprKind::Symbol(name) = &head.kind else {
                return None;
            };
            if &**name != "fixture" {
                return None;
            }
            Some(entries)
        })
        .collect();

    assert_eq!(
        conformance.len(),
        fixtures.len(),
        "my-lisp-constitution.lisp has a different fixture count than conformance.lisp — \
         run `cargo run -p sens-cli -- scripts/build-constitution.lisp > my-lisp-constitution.lisp` to regenerate it"
    );

    for (i, (fact_form, tagged_entries)) in conformance.iter().zip(fixtures.iter()).enumerate() {
        let ExprKind::List(fact_entries) = &fact_form.kind else {
            panic!("conformance.lisp fixture #{} should be an alist", i + 1);
        };
        for key in ["expr", "expected", "error"] {
            assert_eq!(
                alist_str(fact_entries, key),
                alist_str(tagged_entries, key),
                "fixture #{} field \"{key}\" drifted between conformance.lisp and \
                 my-lisp-constitution.lisp — regenerate it",
                i + 1
            );
        }
    }
}

/// Project principle 3 ("build the reasoning machine") deliberately has no
/// G/S axiom counterpart in `docs/language-core-axioms.md` — an axiom is a
/// claim about the language, this principle is a claim about why the
/// project exists, and those are different categories on purpose. But that
/// leaves nothing in the language contract itself that would notice if
/// `lib/unify.my`/`lib/reason.my` were quietly deleted, or Tier 3 coverage
/// thinned out over time — the erosion would only be caught by whoever
/// happened to remember to look. This test is a process guard, not a
/// semantic one: it doesn't test what `unify`/`reason` mean (that's
/// `tests/unify.rs`/`tests/reason.rs`), only that they still exist, still
/// load, still prove one real fact, and that Tier 3 hasn't silently shrunk
/// below a floor. If the floor is intentionally being lowered, lower this
/// assertion explicitly — don't let it drift unnoticed.
/// Pryntsyp proiektu 3 ("realizuvaty rozumnu mashynu") svidomo ne maie
/// vidpovidnyka sered G/S aksiom u `docs/language-core-axioms.md` — aksioma
/// tse tverdzhennia pro movu, tsei pryntsyp — tverdzhennia pro te, chomu proiekt
/// isnuie, i tse rizni katehorii navmysno. Ale tse oznachaie, shcho nishcho v samomu
/// movnomu kontrakti ne pomityt, yakshcho `lib/unify.my`/`lib/reason.my` tykho
/// vydaliat, abo pokryttia Rivnia 3 z chasom zmenshytsia — eroziiu vpiimaie lyshe
/// toi, khto vypadkovo zhadaie podyvytys. Tsei test — protsesna harantiia, ne
/// semantychna: vin ne pereviriaie, shcho oznachaiut `unify`/`reason` (tse robliat
/// `tests/unify.rs`/`tests/reason.rs`), lyshe shcho vony y dosi isnuiut,
/// zavantazhuiutsia, dovodiat odyn realnyi fakt, i shcho Riven 3 movchky ne
/// prosiv nyzhche mezhi. Yakshcho mezhu svidomo znyzhuiut — znyzyty tsiu perevirku
/// yavno, ne daty yii rozmytys nepomichenoiu.
#[test]
fn cons_respects_an_opt_in_resource_limit_and_fails_named_not_silently() {
    let mut session = Session {
        environment: Environment::root().with_cons_limit(2),
    };
    eval_program("(cons 1 2)", &mut session).expect("first cons should succeed");
    eval_program("(cons 3 4)", &mut session).expect("second cons should succeed");
    let error =
        eval_program("(cons 5 6)", &mut session).expect_err("third cons should hit the limit");
    assert_eq!(error.kind, ErrorKind::OutOfMemory);
}

#[test]
fn cons_stays_unbounded_by_default_matching_every_conformance_fixture() {
    // The default Session::default() (what conformance_tests_from_my uses)
    // never opts into a limit — confirms OutOfMemory is reachable only when
    // a session deliberately asks for it, not a new default restriction.
    let mut session = Session::default();
    for _ in 0..10_000 {
        eval_program("(cons 1 2)", &mut session).expect("unbounded session should never run out");
    }
}

/// Same shape as the `cons` limit above, for `S1`'s own named example
/// (`NumericOverflow`) instead of `S3`'s (`OutOfMemory`) — an opt-in
/// bit-length cap on exact arithmetic results. Never falls back to an
/// inexact approximation past the limit (that would violate S1, not
/// satisfy it) — it fails named instead.
/// Ta sama forma, shcho y mezha `cons` vyshche, dlia vlasnoho nazvanoho prykladu
/// `S1` (`NumericOverflow`) zamist `S3` (`OutOfMemory`) — optsiina mezha v
/// bitakh na rezultaty tochnoi aryfmetyky. Nikoly ne vidkochuietsia do
/// netochnoho nablyzhennia za mezheiu (tse porushylo b S1, ne zadovolnylo b
/// yoho) — natomist provaliuietsia nazvano.
#[test]
fn arithmetic_respects_an_opt_in_numeric_bit_limit_and_fails_named_not_silently() {
    let mut session = Session {
        environment: Environment::root().with_numeric_bit_limit(8), // fits up to 255
    };
    eval_program("(+ 100 100)", &mut session).expect("200 fits in 8 bits");
    let error = eval_program("(+ 200 200)", &mut session)
        .expect_err("400 exceeds an 8-bit limit and must not silently approximate");
    assert_eq!(error.kind, ErrorKind::NumericOverflow);
}

#[test]
fn division_respects_the_same_opt_in_numeric_bit_limit() {
    let mut session = Session {
        environment: Environment::root().with_numeric_bit_limit(8),
    };
    let error = eval_program("(/ 1 1000)", &mut session)
        .expect_err("a denominator past the bit limit must fail named");
    assert_eq!(error.kind, ErrorKind::NumericOverflow);
}

#[test]
fn string_append_concatenates_two_strings() {
    assert_eq!(
        eval(r#"(string-append "hello, " "world")"#),
        Value::String("hello, world".into())
    );
}

#[test]
fn string_append_rejects_a_non_string_first_argument() {
    let error = eval_program(r#"(string-append 1 "x")"#, &mut Session::default())
        .expect_err("a non-string first argument must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn string_append_rejects_a_non_string_second_argument() {
    let error = eval_program(r#"(string-append "x" 1)"#, &mut Session::default())
        .expect_err("a non-string second argument must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn string_append_wrong_arity_is_an_arity_error() {
    let error = eval_program(r#"(string-append "only-one")"#, &mut Session::default())
        .expect_err("string-append with one argument must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Arity);
}

// --- string<? (PLAN.md item 15 — the one primitive its persistent-map
// design needed) --------------------------------------------------------
// Власник, 2026-09-26: string<? визначено мовою в lib/core.lisp поверх
// примітивів string-first/string-rest/string->codepoint — тести з ядром.

fn core_session() -> Session {
    let mut session = Session::default();
    sens::load_core_library(&mut session).expect("core library should load");
    session
}

#[test]
fn string_less_than_rejects_non_string_arguments() {
    let left = eval_program(r#"(string<? 1 "a")"#, &mut core_session())
        .expect_err("a non-string left argument must fail named, not panic");
    assert_eq!(left.kind, ErrorKind::Type);

    let right = eval_program(r#"(string<? "a" 1)"#, &mut core_session())
        .expect_err("a non-string right argument must fail named, not panic");
    assert_eq!(right.kind, ErrorKind::Type);
}

#[test]
fn string_less_than_wrong_arity_is_an_arity_error() {
    let error = eval_program(r#"(string<? "only-one")"#, &mut core_session())
        .expect_err("string<? with one argument must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Arity);
}
