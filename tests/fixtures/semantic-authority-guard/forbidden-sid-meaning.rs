use std::collections::HashMap;

fn meaning_table() -> HashMap<u8, &'static str> {
    let mut table = HashMap::new();
    table.insert(0b00001100, "add");
    table.insert(0b00001101, "sub");
    table
}
fn meaning(id: SemanticId) -> CanonicalIdentity {
    match id { _ => CanonicalIdentity::Unknown, }
}
