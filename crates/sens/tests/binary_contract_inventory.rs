use sens::inventory_binary_contract;
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::PathBuf;

fn foundation_path() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../knowledge/d1-d9-foundation.json")
}

#[test]
fn current_d1_d9_exact_coordinates_round_trip_through_binary_contract_inventory() {
    let raw = fs::read_to_string(foundation_path()).expect("current D1-D9 foundation");
    let foundation: Value = serde_json::from_str(&raw).expect("foundation JSON");
    assert_eq!(foundation["status"], "owner-ratified");

    let domains = foundation["domains"].as_object().expect("domains object");
    let mut expected: BTreeMap<usize, BTreeSet<u16>> = BTreeMap::new();
    let mut words = Vec::new();

    for width in 1usize..=9 {
        let key = format!("D{width}");
        let domain = domains.get(&key).unwrap_or_else(|| panic!("missing {key}"));
        assert_eq!(domain["width"].as_u64(), Some(width as u64));

        let residents = domain["residents"]
            .as_object()
            .unwrap_or_else(|| panic!("{key} residents"));

        if width == 2 {
            let structural = residents
                .keys()
                .map(|bits| u16::from_str_radix(bits, 2).expect("D2 bits"))
                .collect::<BTreeSet<_>>();
            assert_eq!(structural, BTreeSet::from([0, 1, 2, 3]));
            continue;
        }

        let set = expected.entry(width).or_default();
        for bits in residents.keys() {
            assert_eq!(bits.len(), width, "{key}:{bits} wrong width");
            let packed = u16::from_str_radix(bits, 2).expect("resident bits");
            assert!(set.insert(packed), "{key}:{bits} duplicate");
            words.push(bits.clone());
        }
    }

    // Exercise every D2 structural word without adding any coordinate outside
    // the already-ratified sets: OPEN D1:1 SEP D3:001 DOT D9:1 CLOSE.
    let mut source = String::from("10 1 00 001 11 000000001 01");
    for word in words {
        source.push_str(" 00 ");
        source.push_str(&word);
    }

    let inventory = inventory_binary_contract(&source).expect("canonical binary Contract corpus");

    assert!(inventory.has_complete_d2_structure());
    assert!(!inventory.residents().contains_key(&2));
    assert_eq!(inventory.residents(), &expected);

    assert_eq!(inventory.residents().get(&1).map(BTreeSet::len), Some(2));
    assert_eq!(inventory.residents().get(&3).map(BTreeSet::len), Some(8));
    assert_eq!(inventory.residents().get(&4).map(BTreeSet::len), Some(16));
    assert_eq!(inventory.residents().get(&5).map(BTreeSet::len), Some(32));
    assert_eq!(inventory.residents().get(&6).map(BTreeSet::len), Some(64));
    assert_eq!(inventory.residents().get(&7).map(BTreeSet::len), Some(126));
    assert_eq!(inventory.residents().get(&8).map(BTreeSet::len), Some(256));
    assert_eq!(inventory.residents().get(&9).map(BTreeSet::len), Some(512));

    let total = inventory.residents().values().map(BTreeSet::len).sum::<usize>();
    assert_eq!(total, 1016);
}
