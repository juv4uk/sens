//! Integration witness for Issue #746 [P0][LANGUAGE-SIMPLIFY-1].
//!
//! Acceptance criterion 5:
//! "Demonstrate one program that mixes local Lisp evaluation with at least two island calls."
//!
//! Acceptance criterion 6:
//! "No semantic authority moves into Rust or a kernel as a side effect of simplification."
//!
//! This witness demonstrates that my-lisp acts as a small, honest semantic/coordination
//! language. Local Lisp evaluation handles data structure composition, while heavy
//! reasoning or relational queries are delegated to autonomous islands via opaque byte
//! transport. The native results remain intact and are composed in pure Lisp data.

use std::sync::Mutex;
use my_lisp::{
    eval_expr, parse, register_capability, unregister_capability,
    Environment, ErrorKind, Expr, LanguageError, Span, Value,
};
use wsm_kernel_host::{KernelDriver, KernelHostError, KernelId, KernelRouter};

static TEST_ROUTER: Mutex<Option<KernelRouter>> = Mutex::new(None);

fn evaluate_island_exchange(
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if arguments.len() != 2 {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            "island-exchange requires 2 arguments: (island-exchange target payload)",
            span,
        ));
    }

    let target_val = eval_expr(&arguments[0], environment)?;
    let payload_val = eval_expr(&arguments[1], environment)?;

    let target_str = match target_val {
        Value::String(ref s) => s.to_string(),
        Value::Symbol(ref s) => s.to_string(),
        _ => {
            return Err(LanguageError::new(
                ErrorKind::Type,
                "target must be a string or symbol",
                span,
            ))
        }
    };

    let payload_bytes = match payload_val {
        Value::String(ref s) => s.as_bytes().to_vec(),
        _ => {
            return Err(LanguageError::new(
                ErrorKind::Type,
                "payload must be a string",
                span,
            ))
        }
    };

    let mut guard = TEST_ROUTER.lock().unwrap();
    let router = guard.as_mut().ok_or_else(|| {
        LanguageError::new(
            ErrorKind::InvalidForm,
            "TEST_ROUTER not initialized",
            span,
        )
    })?;

    let response_bytes = router
        .exchange(&target_str, &payload_bytes, b"my-lisp-orchestrator")
        .map_err(|err| {
            LanguageError::new(
                ErrorKind::InvalidForm,
                format!("island exchange failed: {err}"),
                span,
            )
        })?;

    let response_str = String::from_utf8_lossy(&response_bytes).to_string();
    Ok(Value::String(response_str.into()))
}

struct MockDatalogIsland {
    id: KernelId,
    running: bool,
}

impl MockDatalogIsland {
    fn new() -> Self {
        Self {
            id: KernelId::new("datalog"),
            running: false,
        }
    }
}

impl KernelDriver for MockDatalogIsland {
    fn id(&self) -> KernelId {
        self.id.clone()
    }

    fn start(&mut self) -> Result<(), KernelHostError> {
        self.running = true;
        Ok(())
    }

    fn exchange(&mut self, payload: &[u8]) -> Result<Vec<u8>, KernelHostError> {
        if !self.running {
            return Err(KernelHostError::NotRunning);
        }
        let query = String::from_utf8_lossy(payload);
        // Simulate Datalog relational closure: base facts + derived fixpoint
        let output = format!("datalog-closure:ancestors_of({query})=[parent(alice,bob),parent(bob,carol),ancestor(alice,carol)]");
        Ok(output.into_bytes())
    }

    fn snapshot(&self) -> Result<Vec<u8>, KernelHostError> {
        Ok(b"datalog:stratified_relational_snapshot".to_vec())
    }

    fn stop(&mut self) -> Result<(), KernelHostError> {
        self.running = false;
        Ok(())
    }
}

struct MockPrologIsland {
    id: KernelId,
    running: bool,
}

impl MockPrologIsland {
    fn new() -> Self {
        Self {
            id: KernelId::new("prolog"),
            running: false,
        }
    }
}

impl KernelDriver for MockPrologIsland {
    fn id(&self) -> KernelId {
        self.id.clone()
    }

    fn start(&mut self) -> Result<(), KernelHostError> {
        self.running = true;
        Ok(())
    }

    fn exchange(&mut self, payload: &[u8]) -> Result<Vec<u8>, KernelHostError> {
        if !self.running {
            return Err(KernelHostError::NotRunning);
        }
        let query = String::from_utf8_lossy(payload);
        // Simulate Prolog SLD resolution: backtrackable substitution answers
        let output = format!("prolog-answers:unify({query})=[Subst(X=carol),Subst(X=dave)]");
        Ok(output.into_bytes())
    }

    fn snapshot(&self) -> Result<Vec<u8>, KernelHostError> {
        Ok(b"prolog:choice_point_stack_snapshot".to_vec())
    }

    fn stop(&mut self) -> Result<(), KernelHostError> {
        self.running = false;
        Ok(())
    }
}

#[test]
fn program_mixes_local_lisp_evaluation_with_two_autonomous_island_calls() {
    // 1. Setup multi-kernel router with Datalog and Prolog autonomous islands
    let mut router = KernelRouter::new();
    router.register(Box::new(MockDatalogIsland::new()));
    router.register(Box::new(MockPrologIsland::new()));

    {
        let mut guard = TEST_ROUTER.lock().unwrap();
        *guard = Some(router);
    }

    // 2. Install mechanical island-exchange capability in my-lisp
    register_capability("island-exchange", evaluate_island_exchange);

    // 3. Define the orchestrating program in pure my-lisp:
    // It uses:
    // - Canon 0 ()
    // - Local McCarthy-7 operations (define, cons, car, cdr)
    // - Two island calls: Datalog (relational closure) and Prolog (unification search)
    // - Composes an honest Lisp observation data structure without domain collapse.
    let program = r#"
        (define pair (lambda (a b) (cons a b)))

        (define orchestrate-inquiry
          (lambda (entity)
            ((lambda (req)
               ((lambda (datalog-facts)
                  ((lambda (prolog-proof)
                     (pair (pair "request" req)
                           (pair (pair "datalog-evidence" datalog-facts)
                                 (pair (pair "prolog-evidence" prolog-proof)
                                       ()))))
                   (island-exchange "prolog" entity)))
                (island-exchange "datalog" entity)))
             (pair "query-target" entity))))

        (orchestrate-inquiry "person(alice)")
    "#;

    let env = Environment::root();
    let exprs = parse(program).expect("program must parse");

    let mut final_value = Value::Nil;
    for expr in exprs {
        final_value = eval_expr(&expr, &env).expect("evaluation must succeed");
    }

    // Clean up capability
    unregister_capability("island-exchange");

    // 4. Verify the resulting Lisp data structure:
    // Expected structure:
    // (("request" . ("query-target" . "person(alice)"))
    //  ("datalog-evidence" . "datalog-closure:ancestors_of(person(alice))=[parent(alice,bob),parent(bob,carol),ancestor(alice,carol)]")
    //  ("prolog-evidence" . "prolog-answers:unify(person(alice))=[Subst(X=carol),Subst(X=dave)]"))
    match &final_value {
        Value::Pair(entry1, rest1) => {
            // First entry: ("request" . ("query-target" . "person(alice)"))
            match &**entry1 {
                Value::Pair(k, v) => {
                    assert_eq!(**k, Value::String("request".into()));
                    match &**v {
                        Value::Pair(rk, rv) => {
                            assert_eq!(**rk, Value::String("query-target".into()));
                            assert_eq!(**rv, Value::String("person(alice)".into()));
                        }
                        _ => panic!("expected nested request pair"),
                    }
                }
                _ => panic!("expected pair for entry1"),
            }

            // Second entry: ("datalog-evidence" . ...)
            match &**rest1 {
                Value::Pair(entry2, rest2) => {
                    match &**entry2 {
                        Value::Pair(k, v) => {
                            assert_eq!(**k, Value::String("datalog-evidence".into()));
                            assert!(match &**v {
                                Value::String(ref s) => s.contains("datalog-closure:ancestors_of(person(alice))"),
                                _ => false,
                            });
                        }
                        _ => panic!("expected pair for entry2"),
                    }

                    // Third entry: ("prolog-evidence" . ...)
                    match &**rest2 {
                        Value::Pair(entry3, rest3) => {
                            match &**entry3 {
                                Value::Pair(k, v) => {
                                    assert_eq!(**k, Value::String("prolog-evidence".into()));
                                    assert!(match &**v {
                                        Value::String(ref s) => s.contains("prolog-answers:unify(person(alice))"),
                                        _ => false,
                                    });
                                }
                                _ => panic!("expected pair for entry3"),
                            }
                            // Terminates with Canon 0 ()
                            assert_eq!(**rest3, Value::Nil);
                        }
                        _ => panic!("expected pair for rest2"),
                    }
                }
                _ => panic!("expected pair for rest1"),
            }
        }
        other => panic!("expected nested Lisp pairs, got {:?}", other),
    }
}
