use wsm_clips_kernel::{ClipsExecutionResult, LegacyAbiSemanticId as ClipsLegacyAbiSemanticId};
use wsm_common_lisp_kernel::{CommonLispResult, LegacyAbiSemanticId as CommonLispLegacyAbiSemanticId};
use wsm_datalog_kernel::{Database, Value};
use wsm_native_result_types::{
    FourKernelObservation, ObservationCapability, ObservationCapabilityError, ProducerSlot,
};
use wsm_prolog_kernel::{PrologExecutionResult, LegacyAbiSemanticId as PrologLegacyAbiSemanticId};

fn observation() -> FourKernelObservation {
    let mut datalog = Database::new();
    datalog.add_fact("path", vec![Value::sym("a"), Value::sym("b")]);
    datalog.add_fact("path", vec![Value::sym("a"), Value::sym("c")]);

    FourKernelObservation::new(
        CommonLispResult {
            semantic_id: CommonLispLegacyAbiSemanticId(5),
            stdout: b"LEFT\n".to_vec(),
            stderr: Vec::new(),
        },
        PrologExecutionResult {
            semantic_id: PrologLegacyAbiSemanticId(0b1000_0111),
            stdout: b"[bob,dave,carol]\n".to_vec(),
            stderr: Vec::new(),
        },
        ClipsExecutionResult::new(Some(ClipsLegacyAbiSemanticId(0b0111_1011)), 2, 1, 3),
        datalog,
    )
}

#[test]
fn producer_capability_sets_remain_distinct() {
    assert_eq!(
        FourKernelObservation::capabilities(ProducerSlot::Prolog),
        &[ObservationCapability::NativeBytes]
    );
    assert_eq!(
        FourKernelObservation::capabilities(ProducerSlot::Datalog),
        &[ObservationCapability::RelationCount]
    );
    assert_eq!(
        FourKernelObservation::capabilities(ProducerSlot::Clips),
        &[
            ObservationCapability::FiringCount,
            ObservationCapability::WorkingMemoryCounts,
        ]
    );
    assert_eq!(
        FourKernelObservation::capabilities(ProducerSlot::CommonLisp),
        &[ObservationCapability::NativeBytes]
    );
}

#[test]
fn supported_operations_inspect_native_domains_without_normalization() {
    let observation = observation();

    assert_eq!(
        observation
            .native_bytes(ProducerSlot::Prolog)
            .expect("Prolog native bytes"),
        b"[bob,dave,carol]\n"
    );
    assert_eq!(
        observation
            .native_bytes(ProducerSlot::CommonLisp)
            .expect("Common Lisp native bytes"),
        b"LEFT\n"
    );
    assert_eq!(
        observation
            .relation_count(ProducerSlot::Datalog, "path")
            .expect("Datalog relation count"),
        2
    );
    assert_eq!(
        observation
            .firing_count(ProducerSlot::Clips)
            .expect("CLIPS firing count"),
        2
    );
    assert_eq!(
        observation
            .working_memory_counts(ProducerSlot::Clips)
            .expect("CLIPS working-memory counts"),
        (1, 3)
    );
}

#[test]
fn unsupported_operation_is_named_not_false_or_empty() {
    let observation = observation();

    assert_eq!(
        observation.relation_count(ProducerSlot::Prolog, "path"),
        Err(ObservationCapabilityError {
            producer: ProducerSlot::Prolog,
            capability: ObservationCapability::RelationCount,
        })
    );
    assert_eq!(
        observation.native_bytes(ProducerSlot::Datalog),
        Err(ObservationCapabilityError {
            producer: ProducerSlot::Datalog,
            capability: ObservationCapability::NativeBytes,
        })
    );
}
