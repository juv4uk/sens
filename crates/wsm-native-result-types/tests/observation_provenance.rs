use wsm_native_result_types::{
    FourKernelObservation, ObservationRef, ProducerSlot, ProvenanceEdge, ProvenanceEdgeType,
};

#[test]
fn observation_refs_preserve_producer_identity_and_native_slot() {
    let refs = FourKernelObservation::observation_refs(42, Some(0b1010_1000));

    assert_eq!(refs.len(), 4);
    assert_eq!(refs[0].producer, ProducerSlot::CommonLisp);
    assert_eq!(refs[1].producer, ProducerSlot::Prolog);
    assert_eq!(refs[2].producer, ProducerSlot::Clips);
    assert_eq!(refs[3].producer, ProducerSlot::Datalog);

    for reference in refs {
        assert_eq!(reference.observation_id, 42);
        assert_eq!(reference.semantic_id, Some(0b1010_1000));
        assert_eq!(reference.producer, reference.native_slot);
        assert_eq!(reference.metadata_ref, None);
    }
}

#[test]
fn projection_edge_connects_observations_without_normalizing_results() {
    let refs = FourKernelObservation::observation_refs(42, Some(0b1010_1000));
    let edge = ProvenanceEdge {
        edge_id: 7,
        edge_type: ProvenanceEdgeType::ProjectedInto,
        from_observation: refs[1],
        bridge_contract_ref: "prolog-substitutions-to-datalog-facts".to_string(),
        to_observation: refs[3],
    };

    assert_eq!(edge.edge_id, 7);
    assert_eq!(edge.edge_type, ProvenanceEdgeType::ProjectedInto);
    assert_eq!(edge.from_observation.producer, ProducerSlot::Prolog);
    assert_eq!(edge.to_observation.producer, ProducerSlot::Datalog);
    assert_eq!(
        edge.from_observation.semantic_id,
        edge.to_observation.semantic_id
    );
    assert_eq!(
        edge.bridge_contract_ref,
        "prolog-substitutions-to-datalog-facts"
    );
}

#[test]
fn native_result_refs_remain_source_compatible() {
    let refs: [ObservationRef; 4] = FourKernelObservation::observation_refs(99, None);
    let native = FourKernelObservation::result_refs(99);

    for (observation, native) in refs.into_iter().zip(native) {
        assert_eq!(observation.observation_id, native.observation_id);
        assert_eq!(observation.producer, native.producer);
        assert_eq!(observation.native_slot, native.producer);
    }
}
