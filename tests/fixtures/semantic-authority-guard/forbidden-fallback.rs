fn resolve_or_default(id: SemanticId) -> CanonicalIdentity {
    canonical_lookup(id).unwrap_or_else(|| CanonicalIdentity::Unknown)
}
