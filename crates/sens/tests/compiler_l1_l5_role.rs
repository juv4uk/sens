        symbol("compiler-domain-shape"),
        symbol(MECHANISM_NAME),
        domain(d3(0)),
    ]);
    let result = eval_parsed_expressions(&[expression], &mut session)
        .expect("D3:000 shape decomposition must remain representational")
        .value;

    let Value::Pair(width, rest) = &result else {
        panic!("D3:000 decomposition must be a two-element list, got {result:?}");
    };
    assert!(matches!(
        width.as_ref(),
        Value::Number(value, Exactness::Exact) if *value == 3.0
    ));
    let Value::Pair(bits, tail) = rest.as_ref() else {
        panic!("D3:000 shape bits missing: {rest:?}");
    };
    assert!(matches!(tail.as_ref(), Value::Nil));
    assert_eq!(format!("{}", bits), "000");
}

#[test]
fn sens_l1_l5_derivation_matches_rust_oracle_for_all_d3_identities() {
    let mut session = session();

    for raw in 0u8..=0b111 {
        let identity = d3(raw);