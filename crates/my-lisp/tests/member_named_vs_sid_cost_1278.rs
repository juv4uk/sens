//! #1278: real-shape example of a named-call vs. bare-SID cost gap, not
//! a synthetic wrapper. `lib/core.lisp`'s actual `member?` (line 407)
//! already writes `def`/`lambda`/`cond`/`atom`/`car`/`cdr` as bare SID
//! forms (`00001001`/`00001000`/`00000111`/`00000010`/`00000101`/
//! `00000110`) but its comparison is `equal?` by name — this test uses
//! the same shape with `eq` (atom-only membership, the common case for
//! symbol lists) instead of `equal?`, because of a genuine finding this
//! test surfaced first: **`equal?` (SID `00100010`) has an admitted
//! semantic identity but no native Rust mechanism at all** —
//! `(00100010 a b)` fails with "unknown semantic callable SID", since
//! `equal?` is a Lisp-defined function (built on `atom`/`eq`), not a
//! `canon::invoke_semantic_ref` case. Not every SID with a registry row
//! is bare-SID-callable; only native-mechanism primitives (`eq`, `atom`,
//! `cons`, `car`, `cdr`, `+`, `-`, ...) are. #1278's audit should treat
//! "callee has no native SID path at all" and "callee has one but the
//! caller spells it by name anyway" as two different findings.
//!
//! Observational evidence for #1278, not a change to `lib/core.lisp` in
//! this test — landing the SID-form variant is a separate, explicit
//! decision (readability cost per #997/#1254).

use my_lisp::{eval_program, load_core_library, Session};
use std::time::Instant;

const MEMBER_NAMED: &str = r#"
(def member-named?
  (lambda (item lst)
    (cond
      ((atom lst) (structural-kind empty-list) (quote ()))
      ((atom lst) (structural-kind pair)
       (cond
         ((eq item (car lst)) (identity-relation same) t)
         ((eq item (car lst)) (identity-relation distinct)
          (member-named? item (cdr lst))))))))
"#;

// Byte-identical except every `eq` call site is replaced by its own
// bare SID `00000011`.
const MEMBER_SID: &str = r#"
(def member-sid?
  (lambda (item lst)
    (cond
      ((atom lst) (structural-kind empty-list) (quote ()))
      ((atom lst) (structural-kind pair)
       (cond
         ((00000011 item (car lst)) (identity-relation same) t)
         ((00000011 item (car lst)) (identity-relation distinct)
          (member-sid? item (cdr lst))))))))
"#;

fn bench(def_source: &str, call_expr: &str, session: &mut Session) -> u128 {
    eval_program(def_source, session).expect("definition should load");
    let start = Instant::now();
    eval_program(call_expr, session).expect("lookup should evaluate");
    start.elapsed().as_nanos()
}

#[test]
fn equal_has_an_admitted_sid_but_no_native_callable_mechanism() {
    // The finding that shaped this file: equal? (SID 00100010) cannot be
    // invoked as a bare SID at all, unlike eq/atom/cons/car/cdr/+/-.
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    let bare_sid_call = eval_program("(00100010 5 5)", &mut session);
    assert!(
        bare_sid_call.is_err(),
        "equal? is Lisp-defined (built on atom/eq), not a native \
         canon::invoke_semantic_ref mechanism — this must keep failing \
         unless #1278/#997 deliberately wires a native fast path for it"
    );
}

#[test]
fn named_eq_call_and_bare_sid_call_agree_on_every_answer() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    eval_program(MEMBER_NAMED, &mut session).expect("member-named? should load");
    eval_program(MEMBER_SID, &mut session).expect("member-sid? should load");

    let list = "(quote (a b c d e f g h i j k l m n o p q r s t))";
    for (label, target) in [("hit", "j"), ("miss", "zz")] {
        let named = eval_program(
            &format!("(member-named? (quote {target}) {list})"),
            &mut session,
        )
        .unwrap_or_else(|e| panic!("member-named? failed on {label}: {e}"))
        .value
        .to_string();
        let sid = eval_program(
            &format!("(member-sid? (quote {target}) {list})"),
            &mut session,
        )
        .unwrap_or_else(|e| panic!("member-sid? failed on {label}: {e}"))
        .value
        .to_string();
        assert_eq!(named, sid, "{label} case must agree between the two forms");
    }
}

#[test]
fn repeated_lookups_through_a_real_shaped_member_cost_more_by_name_than_by_sid() {
    // A realistic workload: repeated membership checks against the same
    // list, the shape any real caller of member?/pd-member? actually
    // produces (not one isolated call, which would be noise-dominated).
    const ITERATIONS: u32 = 20_000;
    let list = "(quote (a b c d e f g h i j k l m n o p q r s t))";

    let mut named_session = Session::default();
    load_core_library(&mut named_session).expect("core library should load");
    let named_ns = bench(
        MEMBER_NAMED,
        &format!(
            r#"
            (def run-named
              (lambda (n)
                (cond
                  ((= n 0) 1 t)
                  ((= n 0) 0 (cond ((member-named? (quote j) {list}) (run-named (- n 1))) (t (run-named (- n 1))))))))
            (run-named {ITERATIONS})
            "#
        ),
        &mut named_session,
    );

    let mut sid_session = Session::default();
    load_core_library(&mut sid_session).expect("core library should load");
    let sid_ns = bench(
        MEMBER_SID,
        &format!(
            r#"
            (def run-sid
              (lambda (n)
                (cond
                  ((= n 0) 1 t)
                  ((= n 0) 0 (cond ((member-sid? (quote j) {list}) (run-sid (- n 1))) (t (run-sid (- n 1))))))))
            (run-sid {ITERATIONS})
            "#
        ),
        &mut sid_session,
    );

    let ratio = named_ns as f64 / sid_ns as f64;
    eprintln!(
        "member? via named eq: {named_ns} ns; via bare SID 00000011: {sid_ns} ns; ratio {ratio:.3}"
    );

    // Regression guard, not a tight performance contract: if this ever
    // flips (named becomes cheaper, or the two converge to noise), that
    // is itself news worth re-reading #1277/#1278 over, so fail loud
    // rather than silently accept a changed shape.
    assert!(
        ratio > 1.0,
        "expected the named-call form to cost measurably more than the \
         bare-SID form over {ITERATIONS} repeated lookups, per #1277's \
         benchmark methodology; got ratio {ratio:.3} (named={named_ns}ns, sid={sid_ns}ns)"
    );
}
