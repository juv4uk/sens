fn admit_prolog_operator(operator: &str) -> SemanticId {
    match operator {
        "ancestor" => SemanticId::from(0b10101000),
        _ => SemanticId::from(0b00000000),
    }
}
