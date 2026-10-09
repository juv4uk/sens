//! Compiler-facing execution roles derived from SENS-owned semantic laws.
//!
//! This module does not define domain meaning and does not name backend
//! mechanisms. It exposes only a verified abstract role that downstream
//! compilers may bind to their own private mechanism references.

use crate::CoreDomainIdentity;

/// Backend-neutral execution role admitted by the current compiler slice.
///
/// These variants describe what SENS has already established semantically.
/// They are not CML/SLOT-VM/CUDA/FPGA opcodes or mechanism identifiers.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CompilerExecutionRole {
    SelectorHead,
    SelectorTail,
    PairConstruct,
}

/// Backend-neutral compiler role for the complete current compiler-nucleus
/// semantic closure.  This type is representation only: production meaning is
/// derived by executing the SENS-owned structural law through
/// `compiler_lowering_role_from_sens`.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum CompilerLoweringRole {
    QuoteForm,
    AtomPredicate,
    SelectorTail,
    SelectorHead,
    AtomEquality,
    CondForm,
    PairConstruct,
    LambdaForm,
    DefineForm,
}

/// Differential/bootstrap oracle for the first compiler execution-role slice.\n///\n/// Production compiler consumers should use `compiler_execution_role_from_sens`,\n/// which executes the language-owned law. This Rust projection remains as an\n/// independent oracle while the cutover is being proved.\n///
/// The projection delegates to the production selector-law decoder used by the
/// evaluator. No second D3 bits-to-role table is maintained here. The first
/// compiler bridge is deliberately bounded to D3 selector roots; D4/D5
/// descendants and all non-selector/higher domains fail closed for now.
pub fn compiler_execution_role(
    identity: CoreDomainIdentity,
) -> Option<CompilerExecutionRole> {
    if let Some(selector_role) = crate::eval::selector_law::compiler_execution_role(identity) {
        return Some(selector_role);
    }

    match crate::eval::canon::domain_primitive_kind(identity) {
        Some(crate::eval::canon::DomainPrimitiveKind::PairConstruct) => {
            Some(CompilerExecutionRole::PairConstruct)
        }
        Some(crate::eval::canon::DomainPrimitiveKind::AtomPredicate)
        | Some(crate::eval::canon::DomainPrimitiveKind::AtomEquality)
        | Some(crate::eval::canon::DomainPrimitiveKind::Equal)
        | None => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Bija3, Bit3, Bit4, Bit5, Bit8, CoreD4, CoreD5, CoreD8};

    fn d3(raw: u8) -> CoreDomainIdentity {
        CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(raw).unwrap()))
    }

    #[test]
    fn compiler_slice_projects_selectors_and_pair_constructor_from_production_laws() {
        assert_eq!(
            compiler_execution_role(d3(0b100)),
            Some(CompilerExecutionRole::SelectorHead)
        );
        assert_eq!(
            compiler_execution_role(d3(0b011)),
            Some(CompilerExecutionRole::SelectorTail)
        );
        assert_eq!(
            compiler_execution_role(d3(0b111)),
            Some(CompilerExecutionRole::PairConstruct)
        );

        for raw in [0b000, 0b001, 0b010, 0b101, 0b110] {
            assert_eq!(compiler_execution_role(d3(raw)), None);
        }
    }

    #[test]
    fn wider_selector_descendants_and_d8_do_not_leak_into_first_slice() {
        let d4_head_head =
            CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(0b1000).unwrap()));
        let d5_tail_tail_tail =
            CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(0b01111).unwrap()));
        let d4_cons_payload =
            CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(0b0111).unwrap()));
        let d8_collision =
            CoreDomainIdentity::D8(CoreD8::from_word(Bit8::new(0b00000111).unwrap()));

        assert_eq!(compiler_execution_role(d4_head_head), None);
        assert_eq!(compiler_execution_role(d5_tail_tail_tail), None);
        assert_eq!(compiler_execution_role(d4_cons_payload), None);
        assert_eq!(compiler_execution_role(d8_collision), None);
    }
}
