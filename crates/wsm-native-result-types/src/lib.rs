//! Side-by-side storage for producer-native kernel results.
//!
//! This crate deliberately has no universal result enum and performs no
//! cross-kernel reconstruction. Each field is owned by the kernel that
//! produced it. The artifact only keeps the four domains adjacent so sens
//! can observe/relate them later without replacing their native shapes.

use wsm_clips_kernel::ClipsExecutionResult;
use wsm_common_lisp_kernel::CommonLispResult;
use wsm_datalog_kernel::Database;
use wsm_prolog_kernel::PrologExecutionResult;


/// Mechanical producer slot inside one four-kernel observation.
///
/// This identifies where a producer-native result is stored. It does not
/// interpret, normalize, or copy that result.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum ProducerSlot {
    CommonLisp,
    Prolog,
    Clips,
    Datalog,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum ObservationCapability {
    NativeBytes,
    RelationCount,
    FiringCount,
    WorkingMemoryCounts,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ObservationCapabilityError {
    pub producer: ProducerSlot,
    pub capability: ObservationCapability,
}

impl std::fmt::Display for ObservationCapabilityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            formatter,
            "producer {:?} does not support observation capability {:?}",
            self.producer, self.capability
        )
    }
}

impl std::error::Error for ObservationCapabilityError {}

const COMMON_LISP_CAPABILITIES: &[ObservationCapability] =
    &[ObservationCapability::NativeBytes];
const PROLOG_CAPABILITIES: &[ObservationCapability] =
    &[ObservationCapability::NativeBytes];
const CLIPS_CAPABILITIES: &[ObservationCapability] = &[
    ObservationCapability::FiringCount,
    ObservationCapability::WorkingMemoryCounts,
];
const DATALOG_CAPABILITIES: &[ObservationCapability] =
    &[ObservationCapability::RelationCount];

/// Opaque address of one producer-owned result inside an observation.
///
/// Semantic graph relations may carry this value as ordinary data. Relation
/// meaning remains outside this crate, and dereferencing the reference never
/// changes the producer-native payload.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct NativeResultRef {
    pub observation_id: u64,
    pub producer: ProducerSlot,
}

/// Stable graph identity for one producer-owned native observation slot.
///
/// This is an identity/provenance record, not a semantic value and not a
/// normalized foreign result. The optional semantic id is opaque provenance
/// supplied by the caller.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct ObservationRef {
    pub observation_id: u64,
    pub producer: ProducerSlot,
    pub semantic_id: Option<u8>,
    pub native_slot: ProducerSlot,
    pub metadata_ref: Option<u64>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ObservationStorageError {
    ProducerSlotMismatch {
        producer: ProducerSlot,
        native_slot: ProducerSlot,
    },
    MissingNativePayload(NativeResultRef),
}

impl std::fmt::Display for ObservationStorageError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::ProducerSlotMismatch {
                producer,
                native_slot,
            } => write!(
                formatter,
                "observation-ref-slot-mismatch:{producer:?}:{native_slot:?}"
            ),
            Self::MissingNativePayload(reference) => write!(
                formatter,
                "observation-native-payload-missing:{}:{:?}",
                reference.observation_id, reference.producer
            ),
        }
    }
}

impl std::error::Error for ObservationStorageError {}

impl ObservationRef {
    /// Resolve this stable observation identity only to an available native
    /// storage handle. No producer payload is decoded or normalized here.
    pub fn resolve_native_ref(
        self,
        available: &[NativeResultRef],
    ) -> Result<NativeResultRef, ObservationStorageError> {
        if self.producer != self.native_slot {
            return Err(ObservationStorageError::ProducerSlotMismatch {
                producer: self.producer,
                native_slot: self.native_slot,
            });
        }

        let native = NativeResultRef {
            observation_id: self.observation_id,
            producer: self.native_slot,
        };

        if available.contains(&native) {
            Ok(native)
        } else {
            Err(ObservationStorageError::MissingNativePayload(native))
        }
    }
}

/// The narrow first provenance relation admitted by LIFE-1.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum ProvenanceEdgeType {
    ProjectedInto,
}

/// Explicit provenance edge between producer-native observations.
///
/// The bridge contract reference is deliberately opaque text; this type does
/// not interpret bridge semantics or claim result equivalence.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ProvenanceEdge {
    pub edge_id: u64,
    pub edge_type: ProvenanceEdgeType,
    pub from_observation: ObservationRef,
    pub bridge_contract_ref: String,
    pub to_observation: ObservationRef,
}

/// One observation from each autonomous execution kernel.
///
/// The concrete field types are the boundary: Common Lisp stays a Common Lisp
/// process result, Prolog stays a Prolog execution result, CLIPS stays its
/// working-memory/agenda observation, and Datalog stays its relation database
/// with generations and derivations.
#[derive(Clone, Debug)]
pub struct FourKernelObservation {
    pub common_lisp: CommonLispResult,
    pub prolog: PrologExecutionResult,
    pub clips: ClipsExecutionResult,
    pub datalog: Database,
}

impl FourKernelObservation {
    pub fn new(
        common_lisp: CommonLispResult,
        prolog: PrologExecutionResult,
        clips: ClipsExecutionResult,
        datalog: Database,
    ) -> Self {
        Self {
            common_lisp,
            prolog,
            clips,
            datalog,
        }
    }


    /// Return graph-safe references to the four producer-owned result slots.
    ///
    /// The caller chooses the observation identity. This crate only couples
    /// that identity with a mechanical producer slot; it does not assign any
    /// semantic relation to the references.
    pub const fn result_refs(observation_id: u64) -> [NativeResultRef; 4] {
        [
            NativeResultRef { observation_id, producer: ProducerSlot::CommonLisp },
            NativeResultRef { observation_id, producer: ProducerSlot::Prolog },
            NativeResultRef { observation_id, producer: ProducerSlot::Clips },
            NativeResultRef { observation_id, producer: ProducerSlot::Datalog },
        ]
    }

    /// Return stable graph identities for the four producer-native observation slots.
    ///
    /// All four refs share one observation id; each retains its producer slot.
    pub const fn observation_refs(
        observation_id: u64,
        semantic_id: Option<u8>,
    ) -> [ObservationRef; 4] {
        [
            ObservationRef {
                observation_id,
                producer: ProducerSlot::CommonLisp,
                semantic_id,
                native_slot: ProducerSlot::CommonLisp,
                metadata_ref: None,
            },
            ObservationRef {
                observation_id,
                producer: ProducerSlot::Prolog,
                semantic_id,
                native_slot: ProducerSlot::Prolog,
                metadata_ref: None,
            },
            ObservationRef {
                observation_id,
                producer: ProducerSlot::Clips,
                semantic_id,
                native_slot: ProducerSlot::Clips,
                metadata_ref: None,
            },
            ObservationRef {
                observation_id,
                producer: ProducerSlot::Datalog,
                semantic_id,
                native_slot: ProducerSlot::Datalog,
                metadata_ref: None,
            },
        ]
    }

    /// Producer identities are structural: each slot has a distinct concrete
    /// type rather than a tag inside one normalized universal value.
    pub const fn producer_names() -> [&'static str; 4] {
        ["common-lisp", "prolog", "clips", "datalog"]
    }

    pub fn capabilities(producer: ProducerSlot) -> &'static [ObservationCapability] {
        match producer {
            ProducerSlot::CommonLisp => COMMON_LISP_CAPABILITIES,
            ProducerSlot::Prolog => PROLOG_CAPABILITIES,
            ProducerSlot::Clips => CLIPS_CAPABILITIES,
            ProducerSlot::Datalog => DATALOG_CAPABILITIES,
        }
    }

    pub fn supports(
        producer: ProducerSlot,
        capability: ObservationCapability,
    ) -> bool {
        Self::capabilities(producer).contains(&capability)
    }

    fn require(
        producer: ProducerSlot,
        capability: ObservationCapability,
    ) -> Result<(), ObservationCapabilityError> {
        if Self::supports(producer, capability) {
            Ok(())
        } else {
            Err(ObservationCapabilityError {
                producer,
                capability,
            })
        }
    }

    /// Producer-native byte observation.
    ///
    /// Common Lisp and Prolog each keep their own byte protocol. This method
    /// does not parse, normalize, or claim equivalence between those payloads.
    pub fn native_bytes(
        &self,
        producer: ProducerSlot,
    ) -> Result<&[u8], ObservationCapabilityError> {
        Self::require(producer, ObservationCapability::NativeBytes)?;
        match producer {
            ProducerSlot::CommonLisp => Ok(&self.common_lisp.stdout),
            ProducerSlot::Prolog => Ok(&self.prolog.stdout),
            ProducerSlot::Clips | ProducerSlot::Datalog => unreachable!(
                "capability table admitted NativeBytes for a producer without a byte inspector"
            ),
        }
    }

    /// Count tuples in one producer-native Datalog relation.
    pub fn relation_count(
        &self,
        producer: ProducerSlot,
        relation: &str,
    ) -> Result<usize, ObservationCapabilityError> {
        Self::require(producer, ObservationCapability::RelationCount)?;
        match producer {
            ProducerSlot::Datalog => Ok(self.datalog.relation(relation).len()),
            ProducerSlot::CommonLisp | ProducerSlot::Prolog | ProducerSlot::Clips => unreachable!(
                "capability table admitted RelationCount for a non-Datalog producer"
            ),
        }
    }

    /// Return CLIPS' native agenda firing count without mapping it to truth.
    pub fn firing_count(
        &self,
        producer: ProducerSlot,
    ) -> Result<i64, ObservationCapabilityError> {
        Self::require(producer, ObservationCapability::FiringCount)?;
        match producer {
            ProducerSlot::Clips => Ok(self.clips.fired),
            ProducerSlot::CommonLisp | ProducerSlot::Prolog | ProducerSlot::Datalog => unreachable!(
                "capability table admitted FiringCount for a non-CLIPS producer"
            ),
        }
    }

    /// Return CLIPS' native before/after fact counts as their original C-domain type.
    pub fn working_memory_counts(
        &self,
        producer: ProducerSlot,
    ) -> Result<(std::ffi::c_ulong, std::ffi::c_ulong), ObservationCapabilityError> {
        Self::require(producer, ObservationCapability::WorkingMemoryCounts)?;
        match producer {
            ProducerSlot::Clips => Ok((self.clips.facts_before, self.clips.facts_after)),
            ProducerSlot::CommonLisp | ProducerSlot::Prolog | ProducerSlot::Datalog => unreachable!(
                "capability table admitted WorkingMemoryCounts for a non-CLIPS producer"
            ),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use sens::{Bija3, Bit3, CoreDomainIdentity};
    use wsm_clips_kernel::SemanticId as ClipsSemanticId;
    use wsm_prolog_kernel::SemanticId as PrologSemanticId;

    #[test]
    fn artifact_preserves_four_concrete_producer_types() {
        let observation = FourKernelObservation::new(
            CommonLispResult {
                identity: CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(0b101).unwrap())),
                stdout: b"LEFT\n".to_vec(),
                stderr: Vec::new(),
            },
            PrologExecutionResult {
                semantic_id: PrologSemanticId(3),
                stdout: b"[bob,dave,carol]\n".to_vec(),
                stderr: Vec::new(),
            },
            ClipsExecutionResult::new(Some(ClipsSemanticId(6)), 1, 1, 2),
            Database::new(),
        );

        assert_eq!(FourKernelObservation::producer_names(),
            ["common-lisp", "prolog", "clips", "datalog"]);
        assert_eq!(observation.common_lisp.stdout, b"LEFT\n");
        assert_eq!(observation.prolog.stdout, b"[bob,dave,carol]\n");
        assert_eq!(observation.clips.fired, 1);
        assert_eq!(observation.clips.facts_before, 1);
        assert_eq!(observation.clips.facts_after, 2);
        assert_eq!(observation.datalog.generation_count(), 0);

        let refs = FourKernelObservation::result_refs(17);
        assert_eq!(refs[0].observation_id, 17);
        assert_eq!(refs[0].producer, ProducerSlot::CommonLisp);
        assert_eq!(refs[1].producer, ProducerSlot::Prolog);
        assert_eq!(refs[2].producer, ProducerSlot::Clips);
        assert_eq!(refs[3].producer, ProducerSlot::Datalog);
    }
}
