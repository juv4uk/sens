//! Integration witness for Issue #746 [P0][LANGUAGE-SIMPLIFY-1].
//!
//! This witness deliberately uses the real `sens` evaluator for every Lisp
//! operation. Rust owns only mock island drivers plus the mechanical router.
//! There is no shadow parser, Value model, closure model, or evaluator here.

use sens::{eval_program, load_core_library, Session};
use wsm_kernel_host::{KernelDriver, KernelHostError, KernelId, KernelRouter};

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
        Ok(format!(
            "datalog-closure:ancestors_of({query})=[parent(alice,bob),parent(bob,carol),ancestor(alice,carol)]"
        )
        .into_bytes())
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
        Ok(format!(
            "prolog-answers:unify({query})=[Subst(X=carol),Subst(X=dave)]"
        )
        .into_bytes())
    }

    fn snapshot(&self) -> Result<Vec<u8>, KernelHostError> {
        Ok(b"prolog:choice_point_stack_snapshot".to_vec())
    }

    fn stop(&mut self) -> Result<(), KernelHostError> {
        self.running = false;
        Ok(())
    }
}

fn escape_lisp_string(value: &str) -> String {
    value.replace('\\', "\\\\").replace('"', "\\\"")
}

#[test]
fn real_sens_composes_local_evaluation_with_two_autonomous_island_calls() {
    let mut router = KernelRouter::new();
    router.register(Box::new(MockDatalogIsland::new()));
    router.register(Box::new(MockPrologIsland::new()));

    let mut session = Session::default();
    load_core_library(&mut session).expect("real sens core library");

    let local = eval_program(
        "(cons \"query-target\" \"person(alice)\")",
        &mut session,
    )
    .expect("real sens local evaluation")
    .value
    .to_string();

    let datalog = router
        .exchange("datalog", b"person(alice)", b"sens-orchestrator")
        .expect("mechanical Datalog island exchange");
    let prolog = router
        .exchange("prolog", b"person(alice)", b"sens-orchestrator")
        .expect("mechanical Prolog island exchange");

    let datalog = String::from_utf8(datalog).expect("mock Datalog output is UTF-8");
    let prolog = String::from_utf8(prolog).expect("mock Prolog output is UTF-8");

    let composition = format!(
        "(cons (cons \"local\" \"{}\")
               (cons (cons \"datalog-evidence\" \"{}\")
                     (cons (cons \"prolog-evidence\" \"{}\") ())))",
        escape_lisp_string(&local),
        escape_lisp_string(&datalog),
        escape_lisp_string(&prolog),
    );

    let final_value = eval_program(&composition, &mut session)
        .expect("real sens composes island observations")
        .value
        .to_string();

    assert!(final_value.contains("query-target"));
    assert!(final_value.contains("datalog-evidence"));
    assert!(final_value.contains("datalog-closure:ancestors_of(person(alice))"));
    assert!(final_value.contains("prolog-evidence"));
    assert!(final_value.contains("prolog-answers:unify(person(alice))"));
}
