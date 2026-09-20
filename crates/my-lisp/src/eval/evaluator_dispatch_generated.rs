// GENERATED — DO NOT EDIT BY HAND.
// Authority: lib/evaluator-dispatch.lisp
// Generator: scripts/generate-rust-evaluator-dispatch.lisp

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum EvaluatorMechanism {
    EmptyListGround,
    QuoteForm,
    AtomPrimitive,
    EqPrimitive,
    ConsPrimitive,
    CarPrimitive,
    CdrPrimitive,
    CondForm,
    LambdaForm,
    DefineForm,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct EvaluatorDispatchRow {
    pub(crate) semantic_id: u8,
    pub(crate) mechanism: EvaluatorMechanism,
}

pub(crate) const EVALUATOR_DISPATCH: &[EvaluatorDispatchRow] = &[
    EvaluatorDispatchRow { semantic_id: 0b00000000, mechanism: EvaluatorMechanism::EmptyListGround },
    EvaluatorDispatchRow { semantic_id: 0b00000001, mechanism: EvaluatorMechanism::QuoteForm },
    EvaluatorDispatchRow { semantic_id: 0b00000010, mechanism: EvaluatorMechanism::AtomPrimitive },
    EvaluatorDispatchRow { semantic_id: 0b00000011, mechanism: EvaluatorMechanism::EqPrimitive },
    EvaluatorDispatchRow { semantic_id: 0b00000100, mechanism: EvaluatorMechanism::ConsPrimitive },
    EvaluatorDispatchRow { semantic_id: 0b00000101, mechanism: EvaluatorMechanism::CarPrimitive },
    EvaluatorDispatchRow { semantic_id: 0b00000110, mechanism: EvaluatorMechanism::CdrPrimitive },
    EvaluatorDispatchRow { semantic_id: 0b00000111, mechanism: EvaluatorMechanism::CondForm },
    EvaluatorDispatchRow { semantic_id: 0b00001000, mechanism: EvaluatorMechanism::LambdaForm },
    EvaluatorDispatchRow { semantic_id: 0b00001001, mechanism: EvaluatorMechanism::DefineForm },
    EvaluatorDispatchRow { semantic_id: 0b00001011, mechanism: EvaluatorMechanism::DefineForm },
];
