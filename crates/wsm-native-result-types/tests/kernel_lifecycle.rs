use std::path::PathBuf;

use wsm_kernel_host::{
    KernelDriver, KernelHandle, KernelHostError, KernelId, KernelLifecycleState, KernelRouter,
};
use wsm_prolog_kernel::{LegacyAbiSemanticId, PrologKernel, PrologQuery, PrologRequest};

const UNIFY_SID: u8 = 0b1000_0111;

struct PrologLifecycleDriver {
    kernel: PrologKernel,
    program: PathBuf,
    running: bool,
}

impl PrologLifecycleDriver {
    fn new() -> Self {
        Self {
            kernel: PrologKernel::default(),
            program: PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .join("../wsm-prolog-kernel/tests/fixtures/family.pl"),
            running: false,
        }
    }
}

impl KernelDriver for PrologLifecycleDriver {
    fn id(&self) -> KernelId {
        KernelId::new("prolog")
    }

    fn start(&mut self) -> Result<(), KernelHostError> {
        self.kernel
            .version()
            .map_err(|error| KernelHostError::Driver(error.to_string()))?;
        self.running = true;
        Ok(())
    }

    fn exchange(&mut self, payload: &[u8]) -> Result<Vec<u8>, KernelHostError> {
        if !self.running {
            return Err(KernelHostError::NotRunning);
        }
        let goal = std::str::from_utf8(payload)
            .map_err(|error| KernelHostError::Driver(error.to_string()))?;
        let request = PrologRequest::new(
            LegacyAbiLegacyAbiSemanticId(UNIFY_SID),
            PrologQuery::new(goal, "X"),
        );
        let result = self
            .kernel
            .execute(&self.program, &request)
            .map_err(|error| KernelHostError::Driver(error.to_string()))?;
        if result.semantic_id != LegacyAbiSemanticId(UNIFY_SID) {
            return Err(KernelHostError::Driver(
                "Prolog lifecycle witness changed opaque semantic provenance".into(),
            ));
        }
        Ok(result.stdout)
    }

    fn snapshot(&self) -> Result<Vec<u8>, KernelHostError> {
        Ok(Vec::new())
    }

    fn stop(&mut self) -> Result<(), KernelHostError> {
        self.running = false;
        Ok(())
    }
}

fn swipl_available() -> bool {
    PrologKernel::default().version().is_ok()
}

fn state(router: &KernelRouter, handle: KernelHandle) -> KernelLifecycleState {
    router
        .lifecycle(handle)
        .expect("lifecycle observation")
        .state
}

#[test]
fn real_prolog_runs_through_explicit_load_start_invoke_stop_unload_lifecycle() {
    if !swipl_available() {
        eprintln!("SKIP: swipl is not installed on this machine");
        return;
    }

    let mut router = KernelRouter::new();
    let handle = router.load(Box::new(PrologLifecycleDriver::new()));
    assert_eq!(state(&router, handle), KernelLifecycleState::Loaded);

    router.start_handle(handle).expect("start real Prolog");
    assert_eq!(state(&router, handle), KernelLifecycleState::Started);

    let response = router
        .invoke_handle(handle, b"ancestor(alice, X)", &[UNIFY_SID])
        .expect("invoke real Prolog through explicit handle");
    assert_eq!(
        String::from_utf8_lossy(&response.payload).trim(),
        "[bob,dave,carol]"
    );
    assert_eq!(
        response.provenance,
        vec![UNIFY_SID],
        "lifecycle transport must preserve opaque SID provenance"
    );

    router.stop_handle(handle).expect("stop real Prolog");
    assert_eq!(state(&router, handle), KernelLifecycleState::Stopped);

    router.unload_handle(handle).expect("unload real Prolog");
    assert_eq!(state(&router, handle), KernelLifecycleState::Unloaded);
    assert!(!router.is_registered("prolog"));
}
