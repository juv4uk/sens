use wsm_common_lisp_kernel::CommonLispKernel;
use wsm_kernel_host::{
    AvailabilityState, KernelAvailabilityObservation, KernelRouter,
};

fn record_probe(
    router: &mut KernelRouter,
    producer: &str,
    probe: Result<String, String>,
) {
    let observation = match probe {
        Ok(detail) => KernelAvailabilityObservation::available(producer, Some(detail)),
        Err(detail) => KernelAvailabilityObservation::unavailable(producer, Some(detail)),
    };
    router.record_availability(observation);
}

#[test]
fn missing_external_runtime_is_named_unavailable_without_start_or_semantic_mutation() {
    let missing = CommonLispKernel::new("__wsm_definitely_missing_runtime__")
        .version()
        .map(|result| String::from_utf8_lossy(&result.stdout).trim().to_string())
        .map_err(|error| error.to_string());

    let mut router = KernelRouter::new();
    record_probe(&mut router, "common-lisp", missing);

    let observation = router
        .availability("common-lisp")
        .expect("bounded availability observation");
    assert_eq!(observation.state, AvailabilityState::Unavailable);
    assert!(!observation.started);
    assert!(
        observation
            .detail
            .as_deref()
            .is_some_and(|detail| detail.contains("failed to start Common Lisp runtime"))
    );

    // Availability is execution metadata only. No runtime was registered or started.
    assert!(router.registered_kernels().is_empty());
}

#[test]
#[cfg(feature = "native-clips")]
fn four_real_kernels_share_one_availability_observation_path_before_invocation() {
    use wsm_clips_kernel::ClipsKernel;
    use wsm_prolog_kernel::PrologKernel;

    let mut router = KernelRouter::new();

    record_probe(
        &mut router,
        "common-lisp",
        CommonLispKernel::default()
            .version()
            .map(|result| String::from_utf8_lossy(&result.stdout).trim().to_string())
            .map_err(|error| error.to_string()),
    );
    record_probe(
        &mut router,
        "prolog",
        PrologKernel::default()
            .version()
            .map(|result| String::from_utf8_lossy(&result.stdout).trim().to_string())
            .map_err(|error| error.to_string()),
    );
    record_probe(
        &mut router,
        "clips",
        ClipsKernel::discover()
            .map(|_| "native-clips-discovered".to_string())
            .map_err(|error| error.to_string()),
    );

    // Datalog is the in-process kernel; constructing its database is the bounded
    // execution-availability probe and performs no semantic query.
    let _datalog = wsm_datalog_kernel::Database::new();
    record_probe(
        &mut router,
        "datalog",
        Ok("in-process-datalog-kernel".to_string()),
    );

    for producer in ["common-lisp", "prolog", "clips", "datalog"] {
        let observation = router
            .availability(producer)
            .unwrap_or_else(|| panic!("missing availability observation for {producer}"));
        assert_eq!(
            observation.state,
            AvailabilityState::Available,
            "{producer}: {:?}",
            observation.detail
        );
        assert!(!observation.started);
    }

    // Probing availability must not invoke or implicitly register any island.
    assert!(router.registered_kernels().is_empty());
}
