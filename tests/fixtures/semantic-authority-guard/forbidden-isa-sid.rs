fn semantic_for_opcode(mnemonic: &str, opcode: u8) -> SemanticId {
    match (mnemonic, opcode) {
        ("add", 0x01) => SemanticId::from(0b00001100),
        _ => SemanticId::from(0b00000000),
    }
}
