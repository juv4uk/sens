//! Exact-domain inventory for canonical visible-binary Contract source.
//!
//! This module is deliberately not a second reader. Contract source must first
//! pass `parse_canonical_binary`; inventory is then derived from the same
//! exact-width source words. D2 stays structural grammar. Every non-D2 word is
//! retained as an exact domain-qualified coordinate, including D3:000 EMPTY.

use crate::{
    parse_binary_source_words, parse_canonical_binary, BinarySourceWord, DomainIdentity,
    LanguageError,
};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BinaryContractInventory {
    residents: BTreeMap<usize, BTreeSet<u16>>,
    d2_structure: BTreeSet<u16>,
}

impl BinaryContractInventory {
    /// Exact semantic coordinates observed in the canonical Contract source,
    /// grouped by domain width. D2 is excluded because it owns grammar here.
    pub fn residents(&self) -> &BTreeMap<usize, BTreeSet<u16>> {
        &self.residents
    }

    /// Exact D2 structural words observed while parsing the Contract source.
    pub fn d2_structure(&self) -> &BTreeSet<u16> {
        &self.d2_structure
    }

    pub fn contains_exact(&self, width: usize, packed_bits: u16) -> bool {
        self.residents
            .get(&width)
            .is_some_and(|values| values.contains(&packed_bits))
    }

    pub fn has_complete_d2_structure(&self) -> bool {
        self.d2_structure == BTreeSet::from([0, 1, 2, 3])
    }

    /// Stable width/payload projection for generators and ratchets.
    pub fn ordered_coordinates(&self) -> Vec<(usize, u16)> {
        self.residents
            .iter()
            .flat_map(|(width, values)| values.iter().map(move |value| (*width, *value)))
            .collect()
    }
}

/// Parse canonical Contract source and return every non-D2 exact identity in
/// source order. This preserves D3:000 as an exact D3 contract resident even
/// though the evaluator-facing AST law renders that word as structural EMPTY.
pub fn parse_binary_contract_identities(
    source: &str,
) -> Result<Vec<DomainIdentity>, LanguageError> {
    // Mandatory language reader gate: inventory never accepts a second syntax.
    parse_canonical_binary(source)?;

    let tokens = parse_binary_source_words(source)?;
    Ok(tokens
        .into_iter()
        .filter_map(|token| match token.word {
            BinarySourceWord::W2(_) => None,
            word => Some(word.domain_identity()),
        })
        .collect())
}

/// Build a unique exact-domain inventory while retaining the complete D2
/// structural vocabulary separately.
pub fn inventory_binary_contract(
    source: &str,
) -> Result<BinaryContractInventory, LanguageError> {
    // Mandatory language reader gate.
    parse_canonical_binary(source)?;
    let tokens = parse_binary_source_words(source)?;

    let mut residents: BTreeMap<usize, BTreeSet<u16>> = BTreeMap::new();
    let mut d2_structure = BTreeSet::new();

    for token in tokens {
        match token.word {
            BinarySourceWord::W2(word) => {
                d2_structure.insert(word.packed_bits() as u16);
            }
            word => {
                residents
                    .entry(word.width())
                    .or_default()
                    .insert(word.packed_bits());
            }
        }
    }

    Ok(BinaryContractInventory {
        residents,
        d2_structure,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn contract_inventory_requires_the_canonical_reader() {
        let error = inventory_binary_contract("10 001")
            .expect_err("unterminated D2 structure must fail before inventory");
        assert_eq!(error.kind, crate::ErrorKind::Parse);
    }

    #[test]
    fn equal_payloads_remain_distinct_across_exact_domains() {
        let source =
            "1 00 001 00 0001 00 00001 00 000001 00 0000001 00 00000001 00 000000001";
        let inventory = inventory_binary_contract(source).expect("canonical contract source");

        for width in [1usize, 3, 4, 5, 6, 7, 8, 9] {
            assert!(inventory.contains_exact(width, 1), "missing D{width}:1");
        }

        let identities =
            parse_binary_contract_identities(source).expect("exact contract identities");
        let ones = identities
            .iter()
            .filter(|identity| identity.packed_bits() == 1)
            .map(|identity| identity.width())
            .collect::<Vec<_>>();
        assert_eq!(ones, vec![1, 3, 4, 5, 6, 7, 8, 9]);
    }

    #[test]
    fn d3_zero_survives_contract_inventory_as_exact_resident() {
        let inventory = inventory_binary_contract("000").expect("D3 EMPTY source");
        assert!(inventory.contains_exact(3, 0));

        let identities =
            parse_binary_contract_identities("000").expect("D3 EMPTY contract identity");
        assert_eq!(identities.len(), 1);
        assert_eq!((identities[0].width(), identities[0].packed_bits()), (3, 0));
    }

    #[test]
    fn d2_is_grammar_not_a_duplicate_resident_payload() {
        let source = "10 1 00 001 11 000000001 01";
        let inventory = inventory_binary_contract(source).expect("canonical D2 structure");

        assert!(inventory.has_complete_d2_structure());
        assert!(!inventory.residents().contains_key(&2));
        assert!(inventory.contains_exact(1, 1));
        assert!(inventory.contains_exact(3, 1));
        assert!(inventory.contains_exact(9, 1));
    }
}
