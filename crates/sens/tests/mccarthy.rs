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
fn native_binary_value_round_trips_through_eval_and_print() {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("core library loads");
    let first = eval_program("00000101", &mut session)
        .expect("SID value evaluates");
    assert_eq!(first.value.to_string(), "00000101");

    let printed = first.value.to_string();
    let second = eval_program(&printed, &mut session)
        .expect("printed SID reads again");
    assert_eq!(second.value, first.value);
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
fn division_by_zero_has_the_contract_3_named_error() {
    for source in ["(/ 1 0)", "(/ 1 0.0)"] {
        assert_eq!(
            eval_program(source, &mut Session::default())
                .unwrap_err()
                .kind,
            ErrorKind::DivisionByZero,
            "source: {source}"
        );
    }

    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    for source in ["(quotient 5 0)", "(mod 5 0)"] {
        assert_eq!(
            eval_program(source, &mut session).unwrap_err().kind,
            ErrorKind::DivisionByZero,
            "source: {source}"
        );
    }
}

/// `Rational` used to be `i64`-bounded and this exact expression overflowed
/// (`ErrorKind::InvalidForm`) — deliberately kept *out* of
/// tests/fixtures/conformance.json at the time (see that file's README)
/// because whether a future bignum-capable implementation should still
/// overflow here was an open scope question, not yet a decided contract.
/// `crates/sens/src/bignum.rs` answered it: `Rational` is now backed by
/// a hand-rolled arbitrary-precision integer (no crate dependency — see
/// its header comment for why), so this now computes the exact product
/// instead of erroring. Kept as a Rust-only regression test, still not
/// promoted to the shared contract, since a future C or HDL implementation
/// might reasonably choose a different (or still bounded) representation.
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
fn exact_arithmetic_computes_factorials_past_i64_range() {
    let source = r#"
        (def fact
          (lambda (n acc)
            (cond
              ((eq? n 0) acc)
              ((тотожне? n n) (fact (- n 1) (* acc n))))))
        (fact 30 (/ 1 1))
    "#;
    let result = eval_program(source, &mut Session::default()).unwrap();
    assert_eq!(
        result.value.to_string(),
        "265252859812191058636308480000000"
    );
}

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
fn numeric_comparisons_return_exact_predicate_bits() {
    assert_eq!(eval("(< 2 3)").as_predicate_bit(), Some(true));
    assert_eq!(eval("(< 3 2)").as_predicate_bit(), Some(false));
    assert_eq!(eval("(> 3 2)").as_predicate_bit(), Some(true));
    assert_eq!(eval("(= 3 3)").as_predicate_bit(), Some(true));
    assert_eq!(eval("(= 3 4)").as_predicate_bit(), Some(false));
}

#[test]
fn comparison_with_no_arguments_is_an_arity_error() {
    let error = eval_program("(<)", &mut Session::default()).unwrap_err();
    assert_eq!(error.kind, ErrorKind::Arity);
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
fn eval_closes_the_read_eval_loop_by_hand() {
    assert_eq!(
        eval(r#"(eval (read "(+ 1 2)"))"#),
        Value::Number(3.0, Exactness::Exact)
    );
    assert_eq!(
        eval("(eval (quote (+ 1 2)))"),
        Value::Number(3.0, Exactness::Exact)
    );
}

#[test]
fn eval_looks_up_a_quoted_symbol_in_the_calling_environment() {
    let mut session = Session::default();
    eval_program("(def x 5)", &mut session).unwrap();
    let result = eval_program("(eval (quote x))", &mut session).unwrap();
    assert_eq!(result.value, Value::Number(5.0, Exactness::Exact));
}

#[test]
fn eval_treats_closures_and_macros_as_self_evaluating() {
    let mut session = Session::default();
    let closure = eval_program("(eval (lambda (x) x))", &mut session).unwrap();
    assert!(matches!(closure.value, Value::Closure(_)));
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
fn bootstrap_library_is_written_and_executed_in_sens() {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    assert_eq!(
        eval_program("(second (quote (radio antenna)))", &mut session)
            .unwrap()
            .value,
        Value::Symbol("antenna".into())
    );
}

#[test]
fn bootstrap_library_provides_list_utilities() {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    let run = |source: &str, session: &mut Session| {
        eval_program(source, session).unwrap().value.to_string()
    };
    assert_eq!(
        run("(length (quote (radio antenna signal)))", &mut session),
        "3"
    );
    assert_eq!(run("(length (quote ()))", &mut session), "0");
    assert_eq!(run("(reverse (quote (1 2 3)))", &mut session), "(3 2 1)");
    assert_eq!(
        run("(append (quote (1 2)) (quote (3 4)))", &mut session),
        "(1 2 3 4)"
    );
    assert_eq!(
        run("(map (lambda (x) (+ x 1)) (quote (1 2 3)))", &mut session),
        "(2 3 4)"
    );
    assert_eq!(
        run(
            "(filter (lambda (x) (eq? x 2)) (quote (1 2 3 2)))",
            &mut session
        ),
        "(2 2)"
    );
    assert_eq!(
        run(
            "(reduce (lambda (acc x) (+ acc x)) 0 (quote (1 2 3 4)))",
            &mut session
        ),
        "10"
    );
}

#[test]
fn bootstrap_library_provides_let_and_let_star() {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    let run = |source: &str, session: &mut Session| {
        eval_program(source, session).unwrap().value.to_string()
    };
    assert_eq!(run("(let ((x 1) (y 2)) (+ x y))", &mut session), "3");
    assert_eq!(run("(let () 42)", &mut session), "42");
    // Parallel, not sequential: y's value expression can't see x yet.
    let parallel_shadowing_fails =
        eval_program("(let ((x 1) (y x)) (+ x y))", &mut session).unwrap_err();
    assert_eq!(parallel_shadowing_fails.kind, ErrorKind::UnknownSymbol);
    // A let binding shadows an outer def without mutating it.
    assert_eq!(run("(def z 100) (let ((z 1)) z)", &mut session), "1");
    assert_eq!(run("z", &mut session), "100");
    // let* threads each binding's value through to the ones after it.
    assert_eq!(
        run(
            "(let* ((x 1) (y (+ x 1)) (z (+ y 1))) (list x y z))",
            &mut session
        ),
        "(1 2 3)"
    );
    assert_eq!(run("(let* () 7)", &mut session), "7");
}

#[test]
fn reader_supports_unicode_comments_and_quote_sugar() {
    let expressions = parse("; коментар\n'радіо").unwrap();
    assert_eq!(expressions.len(), 1);
    assert_eq!(eval("(quote радіо)"), Value::Symbol("радіо".into()));
}

#[test]
fn implements_mccarthys_seven_primitives() {
    assert_eq!(eval("(quote radio)"), Value::Symbol("radio".into()));
    assert_eq!(
        eval("(car (quote (radio antenna)))"),
        Value::Symbol("radio".into())
    );
    assert_eq!(
        eval("(cdr (quote (radio antenna)))"),
        Value::list([Value::Symbol("antenna".into())])
    );
    assert_eq!(
        eval("(cons (quote radio) (quote (antenna)))"),
        Value::list([
            Value::Symbol("radio".into()),
            Value::Symbol("antenna".into())
        ])
    );
    assert_eq!(
        eval("(за-умовою (() (як-є wrong)) ((тотожне? (як-є x) (як-є x)) (як-є right)))"),
        Value::Symbol("right".into())
    );
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
    assert_eq!(child.get("t"), Some(Value::Symbol("t".into())));
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
fn lambda_is_a_first_class_value() {
    assert_eq!(
        eval("((lambda (apply-once) (apply-once (quote radio))) (lambda (x) (cons x (quote ()))))"),
        Value::list([Value::Symbol("radio".into())])
    );
}

#[test]
fn lambda_reports_invalid_parameters_and_arity() {
    let duplicate = eval_program("(lambda (x x) x)", &mut Session::default()).unwrap_err();
    assert_eq!(duplicate.kind, ErrorKind::InvalidForm);
    assert!(duplicate.message.contains("povtornyi parametr"));

    let invalid = eval_program("(lambda (1) 1)", &mut Session::default()).unwrap_err();
    assert_eq!(invalid.kind, ErrorKind::InvalidForm);

    let arity = eval_program("((lambda (x) x))", &mut Session::default()).unwrap_err();
    assert_eq!(arity.kind, ErrorKind::Arity);
}

/// Variadic parameters (2026-08-09, PLAN.md item 8's follow-on): three
/// shapes shared across the Lisp family, not one dialect's `&rest`
/// keyword — `(a b . rest)` (dotted list, reusing the same reader support
/// added earlier for data literals), a bare symbol (zero fixed params,
/// every argument), and the existing `(a b)` (exact arity, unchanged).
/// Variatyvni parametry (2026-08-09, prodovzhennia punktu 8 z PLAN.md): try
/// formy, spilni dlia rodyny Lisp, ne kliuchove slovo `&rest` odnoho
/// dialektu — `(a b . rest)` (dotted-spysok, ta sama pidtrymka readera,
/// dodana ranishe dlia literaliv danykh), holyi symvol (nul fiksovanykh
/// parametriv, kozhen arhument), i naiavnyi `(a b)` (tochna arnist, bez zmin).
#[test]
fn dotted_lambda_list_binds_extra_arguments_as_a_rest_list() {
    assert_eq!(
        eval("((lambda (a b . rest) rest) 1 2 3 4 5)"),
        Value::list(vec![
            Value::Number(3.0, Exactness::Exact),
            Value::Number(4.0, Exactness::Exact),
            Value::Number(5.0, Exactness::Exact)
        ])
    );
    assert_eq!(
        eval("((lambda (a . rest) a) 1 2 3)"),
        Value::Number(1.0, Exactness::Exact)
    );
}

#[test]
fn bare_symbol_lambda_list_binds_every_argument_as_one_list() {
    assert_eq!(
        eval("((lambda args args) 1 2 3)"),
        Value::list(vec![
            Value::Number(1.0, Exactness::Exact),
            Value::Number(2.0, Exactness::Exact),
            Value::Number(3.0, Exactness::Exact)
        ])
    );
    assert_eq!(eval("((lambda args args))"), Value::Nil);
}

#[test]
fn variadic_lambda_still_requires_its_fixed_parameters() {
    let error = eval_program("((lambda (a b . rest) a) 1)", &mut Session::default()).unwrap_err();
    assert_eq!(error.kind, ErrorKind::Arity);
    assert!(error.message.contains("at least"));
}

#[test]
fn variadic_defmacro_binds_unevaluated_rest_arguments() {
    let mut session = Session::default();
    let result = eval_program(
        "(defmacro my-list items (cons (quote quote) (cons items (quote ())))) (my-list 1 2 3)",
        &mut session,
    )
    .unwrap();
    assert_eq!(
        result.value,
        Value::list(vec![
            Value::Number(1.0, Exactness::Exact),
            Value::Number(2.0, Exactness::Exact),
            Value::Number(3.0, Exactness::Exact)
        ])
    );
}

/// `Display`/`print` previously wrote `"{value}"` with no escaping at all —
/// a string containing a literal `"` broke `read ∘ print = identity`
/// silently (the printed text wasn't valid to read back: it would close
/// early on the embedded quote). Found 2026-08-09 while building tooling
/// that prints fixture data containing real quotes. Fixed by giving
/// `print` real `prin1`/`write` semantics (Common Lisp/Scheme's own
/// convention for the "read-back-safe" print function): escape `"`, `\`,
/// `\n`, `\t`.
/// `Display`/`print` ranishe pysaly `"{value}"` bez zhodnoho ekranuvannia —
/// riadok z bukvalnoiu `"` movchky lamav `read ∘ print = identity`
/// (nadrukovanyi tekst ne chytavsia nazad korektno: zakryvavsia zarano na
/// vbudovanii laptsi). Znaideno 2026-08-09 pid chas napysannia tulinhu, shcho
/// drukuie dani fikstur iz realnymy lapkamy. Vypravleno nadanniam `print`
/// spravzhnoi semantyky `prin1`/`write` (vlasna konventsiia Common
/// Lisp/Scheme dlia "bezpechnoi dlia read" funktsii druku): ekranuvaty `"`,
/// `\`, `\n`, `\t`.
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
fn princ_outputs_a_string_raw_without_quotes_or_escapes() {
    let mut session = Session::default();
    let result = eval_program(r#"(princ "(eq? \"radio\" \"radio\")")"#, &mut session).unwrap();
    assert_eq!(result.output, vec![r#"(eq? "radio" "radio")"#.to_string()]);
    // princ still returns the string value itself, just like print does —
    // composes the same way, only the transcript text differs.
    assert_eq!(
        result.value,
        Value::String(r#"(eq? "radio" "radio")"#.into())
    );
}

#[test]
fn princ_and_print_render_symbols_and_numbers_identically() {
    assert_eq!(
        eval_program("(princ (quote radio))", &mut Session::default())
            .unwrap()
            .output,
        vec!["radio".to_string()]
    );
    assert_eq!(
        eval_program("(princ 42)", &mut Session::default())
            .unwrap()
            .output,
        vec!["42".to_string()]
    );
}

/// `list` used to be a Rust special form; moved to `lib/core.my` the same
/// day variadic lambda parameters were added, since `(def list (lambda
/// args args))` expresses it exactly — G4/G5's own filter ("can the
/// existing core already say this?") applied to the Rust surface itself,
/// not just to `.my` code.
/// `list` ranishe buv spetsialnoiu formoiu Rust; pereneseno v `lib/core.my`
/// toho samoho dnia, koly dodano variatyvni parametry lambda, bo `(def list
/// (lambda args args))` vyrazhaie tse tochno — toi samyi filtr G4/G5 ("chy
/// naiavne yadro vzhe mozhe tse skazaty?"), zastosovanyi do samoho Rust-sharu,
/// ne lyshe do `.my`-kodu.
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
fn evaluator_still_errors_on_a_lone_unknown_symbol() {
    let error = eval_program("пустота", &mut Session::default()).unwrap_err();
    assert_eq!(error.kind, ErrorKind::UnknownSymbol);

    let error = eval_program("hello", &mut Session::default()).unwrap_err();
    assert_eq!(error.kind, ErrorKind::UnknownSymbol);
}

#[test]
fn non_strict_comparisons_are_sens_functions_not_rust_builtins() {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    assert_eq!(
        eval_program("(<=)", &mut session).unwrap_err().kind,
        ErrorKind::Arity
    );
    assert_eq!(
        eval_program("(<= 1 2)", &mut Session::default())
            .unwrap_err()
            .kind,
        ErrorKind::Type
    );
}

/// tests/fixtures/conformance.lisp is the implementation-independent contract
/// (see CLAUDE.md): any future sens implementation — C, HDL, whatever —
/// should reproduce these results once it gets the seven primitives and
/// lambda/def/defmacro right, since everything above that (lib/core.my
/// included) is plain sens source, not Rust. Preloading core.my here lets
/// fixtures exercise it directly instead of duplicating stdlib coverage.
/// Written as sens data (2026-08-09, moved off JSON), so this test reads
/// it via `parse` — the same reader every sens program goes through —
/// not `serde_json`; the fixture file no longer needs a foreign format to
/// stay implementation-independent, it needs sens's own reader, which
/// every conforming implementation already has by definition.
/// tests/fixtures/conformance.lisp — nezalezhnyi vid realizatsii kontrakt
/// (dyv. CLAUDE.md): bud-yaka maibutnia realizatsiia sens — C, HDL, shcho
/// zavhodno — maie vidtvoriuvaty tsi rezultaty, shchoino pravylno realizuie sim
/// prymityviv i lambda/def/defmacro, bo vse, shcho nad nymy (vkliuchno z
/// lib/core.my), — zvychainyi sens-kod, ne Rust. Poperednie zavantazhennia
/// core.my tut dozvoliaie fiksturam napriamu yoho vykorystovuvaty zamist
/// dubliuvannia pokryttia stdlib. Zapysano yak sens-dani (2026-08-09,
/// pereneseno z JSON), tozh tsei test chytaie fail cherez `parse` — toi samyi
/// reader, kriz yakyi prokhodyt bud-yaka sens-prohrama — ne cherez
/// `serde_json`; failu fikstur bilshe ne potriben chuzhyi format, shchob
/// lyshatys nezalezhnym vid realizatsii, yomu potriben vlasnyi reader
/// sens, yakyi bud-yaka konformna realizatsiia vzhe maie za vyznachenniam.
#[test]
fn conformance_tests_from_my() {
    let forms = parse(include_str!("../../../tests/fixtures/conformance.lisp"))
        .expect("conformance.lisp should parse as valid sens source");

    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("lib/core.my should load before conformance fixtures run");
    eval_program(include_str!("../../../lib/unify.lisp"), &mut session)
        .expect("lib/unify.my should load before conformance fixtures run");
    eval_program(include_str!("../../../lib/reason.lisp"), &mut session)
        .expect("lib/reason.my should load before conformance fixtures run");
    eval_program(include_str!("../../../lib/understand.lisp"), &mut session)
        .expect("lib/understand.my should load before conformance fixtures run");
    eval_program(include_str!("../../../lib/narrate.lisp"), &mut session)
        .expect("lib/narrate.my should load before conformance fixtures run");
    eval_program(include_str!("../../../lib/persistent-map.lisp"), &mut session)
        .expect("lib/persistent-map.my should load before conformance fixtures run");

    for form in &forms {
        let ExprKind::List(entries) = &form.kind else {
            panic!("each top-level form in conformance.lisp should be an alist: {form:?}");
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
fn conformance_fixture_exprs_parse_as_single_form() {
    let forms = parse(include_str!("../../../tests/fixtures/conformance.lisp"))
        .expect("conformance.lisp should parse as valid sens source");

    for form in &forms {
        let ExprKind::List(entries) = &form.kind else {
            panic!("each top-level form in conformance.lisp should be an alist: {form:?}");
        };
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

// Simple LCG for property tests
struct Lcg {
    state: u64,
}
impl Lcg {
    fn new(seed: u64) -> Self {
        Self { state: seed }
    }
    fn next(&mut self) -> u64 {
        self.state = self.state.wrapping_mul(6364136223846793005).wrapping_add(1);
        self.state
    }
    fn next_int(&mut self) -> i64 {
        self.next() as i64
    }
    fn next_string(&mut self, max_len: usize) -> String {
        let len = (self.next() as usize) % max_len;
        let mut s = String::with_capacity(len);
        for _ in 0..len {
            let c = (b'a' + (self.next() % 26) as u8) as char;
            s.push(c);
        }
        s
    }
    fn next_list(&mut self, max_len: usize) -> Value {
        let len = (self.next() as usize) % max_len;
        let mut items = Vec::with_capacity(len);
        for _ in 0..len {
            items.push(Value::Number(self.next_int() as f64, Exactness::Exact));
        }
        Value::list(items)
    }
    fn next_string_list(&mut self, max_len: usize) -> Value {
        let len = (self.next() as usize) % max_len;
        let mut items = Vec::with_capacity(len);
        for _ in 0..len {
            items.push(Value::String(self.next_string(10).into()));
        }
        Value::list(items)
    }
}

fn alist_list<'a>(entries: &'a [Expr], key: &str) -> Option<&'a [Expr]> {
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
        if let ExprKind::List(list) = &v.kind {
            return Some(&**list);
        }
        let mut items = Vec::new();
        let mut current = v;
        while let ExprKind::Pair(head, tail) = &current.kind {
            items.push(head.as_ref().clone());
            current = tail;
        }
        Some(items.leak() as &[Expr]) // Leak for simple test usage
    })
}

#[test]
fn property_tests_from_my() {
    let forms = parse(include_str!("../../../tests/fixtures/properties.lisp"))
        .expect("properties.my should parse as valid sens source");

    let mut lcg = Lcg::new(42);

    for form in &forms {
        let ExprKind::List(entries) = &form.kind else {
            panic!("each top-level form in properties.my should be an alist: {form:?}");
        };
        let name = alist_str(entries, "name").expect("fixture needs a \"name\"");
        let expr_str = alist_str(entries, "expr").expect("fixture needs an \"expr\"");
        let types = alist_list(entries, "types").expect("fixture needs \"types\"");
        let type_strings: Vec<&str> = types
            .iter()
            .map(|e| {
                if let ExprKind::String(s) = &e.kind {
                    s.as_ref()
                } else {
                    panic!("type must be string")
                }
            })
            .collect();

        println!("type_strings = {:?}", type_strings);
        let param_names = ["x", "y", "z", "w", "v"];

        for iteration in 0..100 {
            let mut session = Session::default();
            eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
            eval_program(include_str!("../../../lib/forward.lisp"), &mut session).unwrap();
            eval_program(include_str!("../../../lib/persistent-map.lisp"), &mut session).unwrap();
            eval_program(include_str!("../../../lib/knowledge.lisp"), &mut session).unwrap();
            eval_program(include_str!("../../../lib/world.lisp"), &mut session).unwrap();
            eval_program(
                include_str!("../../../tests/fixtures/properties-helpers.lisp"),
                &mut session,
            )
            .unwrap();

            for (i, &t) in type_strings.iter().enumerate() {
                let val = match t {
                    "int" => Value::Number(lcg.next_int() as f64, Exactness::Exact),
                    "string" => Value::String(lcg.next_string(10).into()),
                    "list" => lcg.next_list(10),
                    "string-list" => lcg.next_string_list(10),
                    _ => panic!("Unknown type: {}", t),
                };
                session.environment.define(param_names[i], val);
            }

            let result = eval_program(expr_str, &mut session)
                .unwrap_or_else(|e| panic!("property {name} failed on iteration {iteration}: {e}"));
            // Truthiness, not exact identity: different properties check
            // equality with different predicates (`eq` -> Symbol("t")/Nil,
            // numeric `=` -> Value::Bool -- both untouched here on purpose,
            // see Value::truth), so a property "holding" only ever means
            // "truthy", never one specific Value shape.
            assert!(
                result.value.is_truthy(),
                "Property {name} failed on iteration {iteration}: got {:?}",
                result.value
            );
        }
    }
}

// Minimal symbol/string introspection this project held off on for a long
// time (CLAUDE.md: don't grow the Rust surface) — added deliberately when
// lib/clips-import.lisp's Step 2 needed to strip CLIPS's `?` prefix off a
// variable symbol, which is impossible from within sens itself without
// some way to look at a symbol's characters.

#[test]
fn symbol_to_string_and_back_round_trips() {
    assert_eq!(
        eval("(symbol->string (quote planet))").to_string(),
        "\"planet\""
    );
    assert_eq!(
        eval("(string->symbol (symbol->string (quote planet)))").to_string(),
        "planet"
    );
}

#[test]
fn string_first_returns_a_one_character_string() {
    assert_eq!(
        eval("(string-first (symbol->string (quote ?x)))").to_string(),
        "\"?\""
    );
}

#[test]
fn string_rest_drops_exactly_the_first_character() {
    assert_eq!(
        eval("(string-rest (symbol->string (quote ?x)))").to_string(),
        "\"x\""
    );
}

#[test]
fn string_slice_uses_character_indices_and_clamps_bounds() {
    assert_eq!(eval(r#"(string-slice "привіт" 1 3)"#).to_string(), "\"ри\"");
    assert_eq!(eval(r#"(string-slice "abc" 2 9)"#).to_string(), "\"c\"");
    assert_eq!(eval(r#"(string-slice "abc" 4 9)"#).to_string(), "\"\"");
    assert_eq!(eval(r#"(string-slice "abc" 2 1)"#).to_string(), "\"\"");
}

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
fn read_all_parses_every_top_level_form_as_data() {
    // Unlike `read`, which errors unless the string holds exactly one
    // form, `read-all` returns every top-level form as a list of data.
    assert_eq!(
        eval("(read-all \"(a b) (c d) 5\")").to_string(),
        "((a b) (c d) 5)"
    );
}

#[test]
fn read_all_rejects_a_non_string() {
    let error = eval_program("(read-all (quote (a b)))", &mut Session::default())
        .expect_err("expected a Type error");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn string_predicate_distinguishes_strings_from_other_atoms() {
    assert_eq!(eval("(string? \"hello\")").as_predicate_bit(), Some(true));
    assert_eq!(
        eval("(string? (quote hello))").as_predicate_bit(),
        Some(false)
    );
    assert_eq!(eval("(string? 5)").as_predicate_bit(), Some(false));
}

#[test]
fn symbol_predicate_is_a_sens_function_not_a_rust_builtin() {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    assert_eq!(
        eval_program("(symbol? (quote hello))", &mut session)
            .unwrap()
            .value,
        Value::Symbol("t".into())
    );
    assert_eq!(
        eval_program("(symbol? 5)", &mut session).unwrap().value,
        Value::Nil
    );
    assert_eq!(
        eval_program("(symbol? \"hello\")", &mut session)
            .unwrap()
            .value,
        Value::Nil
    );
    assert_eq!(
        eval_program("(symbol? (quote (hello)))", &mut session)
            .unwrap()
            .value,
        Value::Nil
    );
    assert_eq!(
        eval_program(
            "(symbol? (string->symbol \"strange symbol\"))",
            &mut session
        )
        .unwrap()
        .value,
        Value::Symbol("t".into())
    );
    assert_eq!(
        eval_program("(symbol? (quote hello))", &mut Session::default())
            .unwrap_err()
            .kind,
        ErrorKind::Type
    );
}

#[test]
fn symbol_to_string_rejects_a_non_symbol() {
    let error = eval_program(
        "(symbol->string \"already a string\")",
        &mut Session::default(),
    )
    .expect_err("expected a Type error");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn string_rest_rejects_an_empty_string() {
    let error = eval_program(
        r#"(string-rest (symbol->string (string->symbol "")))"#,
        &mut Session::default(),
    )
    .expect_err("expected a Type error on an empty string");
    assert_eq!(error.kind, ErrorKind::Type);
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
fn symbolic_reasoning_layer_stays_loaded_and_tested() {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("lib/core.my should load before the symbolic layer");
    eval_program(include_str!("../../../lib/unify.lisp"), &mut session)
        .expect("lib/unify.my should load — the symbolic reasoning layer must stay present");
    eval_program(include_str!("../../../lib/reason.lisp"), &mut session)
        .expect("lib/reason.my should load — the symbolic reasoning layer must stay present");

    let result = eval_program(
        "(let ((rules (quote (((parent alice bob)))))) (reason (quote (parent alice bob)) rules))",
        &mut session,
    )
    .expect("reason should still actually prove a fact, not just load without error");
    assert_eq!(
        result.value.to_string(),
        "((() (proved (parent alice bob) (parent alice bob) ())))"
    );

    let forms = parse(include_str!("../../../tests/fixtures/conformance.lisp"))
        .expect("conformance.lisp should parse as valid sens source");
    let tier3_count = forms
        .iter()
        .filter(|form| {
            let ExprKind::List(entries) = &form.kind else {
                return false;
            };
            alist_number(entries, "tier") == Some(3.0)
        })
        .count();
    assert!(
        tier3_count >= 20,
        "Tier 3 (ECOSYSTEM CONFORMANCE, which includes unify/reason) fixture count dropped to \
         {tier3_count} — project principle 3 names symbolic reasoning a project goal, not an \
         optional add-on; if this floor is intentionally being lowered, lower this assertion \
         explicitly instead of letting coverage drift down unnoticed"
    );
}

/// S3 named `OutOfMemory` in its own prose before the category existed in
/// code (found during the 2026-08-09 pre-ratification axiom audit) — this
/// makes it real: an opt-in cons-cell cap, simulating a genuinely bounded
/// heap (S3's own example, "4096 cons cells on an FPGA") without needing
/// real hardware to verify the claim "bounded implementations fail named,
/// never silently redefine `cons`'s meaning." The default session (every
/// `conformance.lisp` fixture) stays unbounded — this is opt-in, not a new
/// default limit on the reference implementation.
/// S3 nazvav `OutOfMemory` u vlasnomu teksti do toho, yak katehoriia
/// isnuvala v kodi (znaideno pid chas audytu aksiom pered ratyfikatsiieiu,
/// 2026-08-09) — tsei test robyt yii realnoiu: optsiina mezha na kilkist
/// cons-komirok, shcho imituie spravdi obmezhenu kupu (vlasnyi pryklad S3,
/// "4096 cons-komirok na FPGA") bez potreby v realnomu zalizi, shchob
/// pereviryty tverdzhennia "obmezheni realizatsii provaliuiutsia nazvano,
/// nikoly ne pereoznachaiut sens `cons` movchky". Typova sesiia (kozhna
/// fikstura `conformance.lisp`) lyshaietsia neobmezhenoiu — tse optsiino, ne nova
/// typova mezha dlia etalonnoi realizatsii.
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
fn arithmetic_stays_unbounded_by_default_matching_every_conformance_fixture() {
    let mut session = Session::default();
    eval_program(
        "(def big (lambda (n acc) (cond ((eq? n 0) acc) ((тотожне? n n) (big (- n 1) (* acc 2)))))) (big 100 1)",
        &mut session,
    )
    .expect("unbounded session should compute a 100-bit result without a limit error");
}

// --- string-append (PLAN.md item 14) -------------------------------------

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

fn eval_core(source: &str) -> Value {
    eval_program(source, &mut core_session()).unwrap().value
}

#[test]
fn string_less_than_orders_strings_lexicographically() {
    assert_eq!(eval_core(r#"(string<? "a" "b")"#), Value::truth(true));
    assert_eq!(eval_core(r#"(string<? "b" "a")"#), Value::truth(false));
    assert_eq!(eval_core(r#"(string<? "a" "a")"#), Value::truth(false));
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

#[test]
fn si_defining_constants_exact_rationals() {
    let mut session = Session::default();
    let si_source = std::fs::read_to_string("lib/si.lisp")
        .or_else(|_| std::fs::read_to_string("../../lib/si.lisp"))
        .expect("lib/si.my must exist and be readable");
    eval_program(&si_source, &mut session).expect("lib/si.my must evaluate cleanly");

    // 1. delta-nu-cs = 9 192 631 770 Hz
    let cs = eval_program("delta-nu-cs", &mut session).unwrap().value;
    assert_eq!(cs, Value::Number(9192631770.0, Exactness::Exact));

    // 2. c = 299 792 458 m/s
    let c = eval_program("c", &mut session).unwrap().value;
    assert_eq!(c, Value::Number(299792458.0, Exactness::Exact));

    // 3. h = 132521403 / 200000000000000000000000000000000000000000 J s
    let h = eval_program("h", &mut session).unwrap().value;
    let expected_h = Rational::from_literal(
        "132521403",
        "200000000000000000000000000000000000000000",
    )
    .unwrap();
    assert_eq!(h, Value::Rational(expected_h.clone()));
    assert_eq!(
        format!("{}", expected_h),
        "132521403/200000000000000000000000000000000000000000"
    );

    // Exact rational arithmetic: (* 2 h) simplifies denominator by 2
    let two_h = eval_program("(* 2 h)", &mut session).unwrap().value;
    let expected_2h = Rational::from_literal(
        "132521403",
        "100000000000000000000000000000000000000000",
    )
    .unwrap();
    assert_eq!(two_h, Value::Rational(expected_2h));

    // 4. e = 801088317 / 5000000000000000000000000000 C
    let e = eval_program("e", &mut session).unwrap().value;
    let expected_e = Rational::from_literal("801088317", "5000000000000000000000000000").unwrap();
    assert_eq!(e, Value::Rational(expected_e.clone()));
    assert_eq!(
        format!("{}", expected_e),
        "801088317/5000000000000000000000000000"
    );

    // 5. k = 1380649 / 100000000000000000000000000000 J/K
    let k = eval_program("k", &mut session).unwrap().value;
    let expected_k = Rational::from_literal("1380649", "100000000000000000000000000000").unwrap();
    assert_eq!(k, Value::Rational(expected_k.clone()));
    assert_eq!(
        format!("{}", expected_k),
        "1380649/100000000000000000000000000000"
    );

    // 6. n-a = 602214076000000000000000 mol^-1
    let na = eval_program("n-a", &mut session).unwrap().value;
    let expected_na = Rational::from_literal("602214076000000000000000", "1").unwrap();
    assert_eq!(na, Value::Rational(expected_na.clone()));
    assert_eq!(format!("{}", expected_na), "602214076000000000000000");

    // 7. k-cd = 683 lm/W
    let k_cd = eval_program("k-cd", &mut session).unwrap().value;
    assert_eq!(k_cd, Value::Number(683.0, Exactness::Exact));

    // Prefixed namespace si: aliases
    assert_eq!(eval_program("si:c", &mut session).unwrap().value, c);
    assert_eq!(eval_program("si:h", &mut session).unwrap().value, h);
    assert_eq!(eval_program("si:e", &mut session).unwrap().value, e);
    assert_eq!(eval_program("si:k", &mut session).unwrap().value, k);
    assert_eq!(eval_program("si:n-a", &mut session).unwrap().value, na);
    assert_eq!(eval_program("si:k-cd", &mut session).unwrap().value, k_cd);
    assert_eq!(eval_program("si:delta-nu-cs", &mut session).unwrap().value, cs);
}

#[test]
fn meta_eval_lambda_witness_env_capture_and_application() {
    // Independent witness pass for Lambda Genealogy (ADR-004 diagnostic pass):
    // Demonstrates the two exact points where evaluator semantics enter:
    // Witness A: Lexical environment capture (env enters closure data structure)
    // Witness B: Operator-position application (my-apply unpacks closure, binds params, evaluates in frame)
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    sens::load_meta_evaluator_library(&mut session).unwrap();

    // 1. Witness A: Explicit environment capture
    // Surface syntax (lambda (x) outer) does NOT mention witness-env.
    // In my-eval: ((eq (car expr) (quote lambda)) (list (quote closure) (second expr) (cdr (cdr expr)) env))
    // The evaluator injects the active lexical frame into the 4-element tagged list.
    let setup = r#"
        (def witness-env (cons (cons (quote outer) 7) (quote ())))
        (def closure-val (my-eval (quote (lambda (x) outer)) witness-env))
    "#;
    eval_program(setup, &mut session).unwrap();
    let closure = eval_program("closure-val", &mut session).unwrap().value;
    assert_eq!(closure.to_string(), "(closure (x) (outer) ((outer . 7)))");

    // 2. Witness B: Operator application through my-apply
    // my-apply unpacks params (x), body ((outer)), and captured env ((outer . 7)),
    // binds x -> 42 using bind-params, and evaluates body in extended frame.
    let app = r#"
        (my-apply closure-val (cons 42 (quote ())))
    "#;
    let result = eval_program(app, &mut session).unwrap().value;
    assert_eq!(result.to_string(), "7");

    // 3. Witness C: Argument binding and lexical frame shadowing
    // Proves that parameter bindings extend the captured environment without mutating it.
    let shadow = r#"
        (def shadow-closure (my-eval (quote (lambda (outer) outer)) witness-env))
        (my-apply shadow-closure (cons 99 (quote ())))
    "#;
    let shadow_res = eval_program(shadow, &mut session).unwrap().value;
    assert_eq!(shadow_res.to_string(), "99");

    // Proves original witness-env remained untouched (7)
    let original_res = eval_program("(my-apply closure-val (cons 0 (quote ())))", &mut session).unwrap().value;
    assert_eq!(original_res.to_string(), "7");
}
