//! Opaque checked-in byte assets exposed by the ROOT Zig transport module.
//! Not part of the nine canonical transport_abi.zig ABI-v2 codec functions.
//! Rust does not embed or interpret either SENS source; ownership stays Zig.
//! Root exports are implemented in zig_transport_root.zig, built via build.rs.
unsafe extern "C" {
    pub(super) fn sens_zig_guard_reference_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_linter_t5m_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_contract_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_repl_core_t5m_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_meta_eval_t5m_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_repl_persistent_vector_t5m_bytes_copy(
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    pub(super) fn sens_zig_repl_epistemic_t5m_bytes_copy(output: *mut u8, capacity: usize)
        -> isize;
    pub(super) fn sens_zig_repl_persistent_map_t5m_bytes_copy(
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    pub(super) fn sens_zig_f6_world_t5m_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_f6_content_store_t5m_bytes_copy(
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    pub(super) fn sens_zig_f6_lisp_fs_t5m_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_f6_producer_witness_t5m_bytes_copy(
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    pub(super) fn sens_zig_repl_unify_t5m_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_repl_reason_t5m_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_repl_forward_t5m_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_repl_knowledge_t5m_bytes_copy(output: *mut u8, capacity: usize)
        -> isize;
    pub(super) fn sens_zig_d9_string_append_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_sanskrit_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    #[cfg(test)]
    pub(super) fn sens_zig_ukr_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    #[cfg(test)]
    pub(super) fn sens_zig_uk_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_islands_manifest_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_uk_docs_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_unify_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_reason_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_forward_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_knowledge_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_persistent_map_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_world_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_content_store_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_lisp_fs_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_domain_table_bytes_copy(
        domain: u8,
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    pub(super) fn sens_zig_compiler_nucleus_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_compiler_identity_corpus_bytes_copy(
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    pub(super) fn sens_zig_compiler_contract_bytes_copy(output: *mut u8, capacity: usize) -> isize;
    pub(super) fn sens_zig_compiler_d3_projection_bytes_copy(
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    pub(super) fn sens_zig_compiler_d3_authority_bytes_copy(
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    pub(super) fn sens_zig_compiler_d4_projection_bytes_copy(
        output: *mut u8,
        capacity: usize,
    ) -> isize;
    pub(super) fn sens_zig_compiler_d4_authority_bytes_copy(
        output: *mut u8,
        capacity: usize,
    ) -> isize;
}
