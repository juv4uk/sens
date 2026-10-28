//! Root-scoped Zig 0.16 module for the sterile, host-neutral transport ABI.
//! The root module alone can @embedFile checked-in assets in lib/; Zig copies
//! exact bytes, never decides Lisp meaning or executable SENS identities.
const std = @import("std");
const abi = @import("research/zig-codecs/transport_abi.zig");

// Keep all existing public C exports reachable without re-implementing them.
comptime {
    _ = abi.sens_zig_codec_abi_version;
    _ = abi.sens_zig_bitpack_fields;
    _ = abi.sens_zig_t5_validate;
    _ = abi.sens_zig_t5_validate_coordinates;
    _ = abi.sens_zig_t5_encode_be3;
    _ = abi.sens_zig_t5_decode_be3;
    _ = abi.sens_zig_e1_encode_be3;
    _ = abi.sens_zig_e1_decode_be3;
    _ = abi.sens_zig_f3c_pack;
    _ = abi.sens_zig_f3c_unpack;
}

// REPL receives the already encoded T5M pair; Zig only serves physical bytes.
const repl_core_t5m_asset = @embedFile("lib/repl-core.sens");

pub export fn sens_zig_repl_core_t5m_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (repl_core_t5m_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(repl_core_t5m_asset.len);
    if (capacity < repl_core_t5m_asset.len) return -2;
    @memcpy(dst[0..repl_core_t5m_asset.len], repl_core_t5m_asset[0..repl_core_t5m_asset.len]);
    return @intCast(repl_core_t5m_asset.len);
}

// SENS owns the metacircular evaluator; the REPL receives its physical T5M pair.
const meta_eval_t5m_asset = @embedFile("lib/meta-eval.sens");

pub export fn sens_zig_meta_eval_t5m_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (meta_eval_t5m_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(meta_eval_t5m_asset.len);
    if (capacity < meta_eval_t5m_asset.len) return -2;
    @memcpy(dst[0..meta_eval_t5m_asset.len], meta_eval_t5m_asset[0..meta_eval_t5m_asset.len]);
    return @intCast(meta_eval_t5m_asset.len);
}

// REPL reasoning modules are already physical T5M. Zig copies bytes only.
const repl_unify_t5m_asset = @embedFile("lib/unify.sens");
const repl_reason_t5m_asset = @embedFile("lib/reason.sens");
const repl_forward_t5m_asset = @embedFile("lib/forward.sens");
const repl_knowledge_t5m_asset = @embedFile("lib/knowledge.sens");
const f6_world_t5m_asset = @embedFile("lib/world.sens");
const f6_content_store_t5m_asset = @embedFile("lib/content-store.sens");
const f6_lisp_fs_t5m_asset = @embedFile("lib/lisp-fs.sens");
const f6_producer_witness_t5m_asset = @embedFile("tests/fixtures/wsm-fs-record-producer.sens");

fn copy_repl_t5m_asset(asset: []const u8, dst: [*]u8, capacity: usize) isize {
    if (asset.len == 0) return -1;
    if (capacity == 0) return @intCast(asset.len);
    if (capacity < asset.len) return -2;
    @memcpy(dst[0..asset.len], asset);
    return @intCast(asset.len);
}

pub export fn sens_zig_repl_unify_t5m_bytes_copy(dst: [*]u8, capacity: usize) isize {
    return copy_repl_t5m_asset(repl_unify_t5m_asset, dst, capacity);
}

pub export fn sens_zig_repl_reason_t5m_bytes_copy(dst: [*]u8, capacity: usize) isize {
    return copy_repl_t5m_asset(repl_reason_t5m_asset, dst, capacity);
}

pub export fn sens_zig_repl_forward_t5m_bytes_copy(dst: [*]u8, capacity: usize) isize {
    return copy_repl_t5m_asset(repl_forward_t5m_asset, dst, capacity);
}

pub export fn sens_zig_repl_knowledge_t5m_bytes_copy(dst: [*]u8, capacity: usize) isize {
    return copy_repl_t5m_asset(repl_knowledge_t5m_asset, dst, capacity);
}

pub export fn sens_zig_f6_world_t5m_bytes_copy(dst: [*]u8, capacity: usize) isize {
    return copy_repl_t5m_asset(f6_world_t5m_asset, dst, capacity);
}

pub export fn sens_zig_f6_content_store_t5m_bytes_copy(dst: [*]u8, capacity: usize) isize {
    return copy_repl_t5m_asset(f6_content_store_t5m_asset, dst, capacity);
}

pub export fn sens_zig_f6_lisp_fs_t5m_bytes_copy(dst: [*]u8, capacity: usize) isize {
    return copy_repl_t5m_asset(f6_lisp_fs_t5m_asset, dst, capacity);
}

pub export fn sens_zig_f6_producer_witness_t5m_bytes_copy(dst: [*]u8, capacity: usize) isize {
    return copy_repl_t5m_asset(f6_producer_witness_t5m_asset, dst, capacity);
}

// A single opaque asset, not a symbol registry. The caller owns memory;
// capacity=0 queries exact byte length. -2 is fail-closed, no partial write.
const linter_t5m_asset = @embedFile("lib/linter.sens");
pub export fn sens_zig_linter_t5m_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (linter_t5m_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(linter_t5m_asset.len);
    if (capacity < linter_t5m_asset.len) return -2;
    @memcpy(dst[0..linter_t5m_asset.len], linter_t5m_asset[0..linter_t5m_asset.len]);
    return @intCast(linter_t5m_asset.len);
}

// Contract source is an opaque byte asset, never a semantic registry.
const contract_asset = @embedFile("language-contract.lisp");
pub export fn sens_zig_contract_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (contract_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(contract_asset.len);
    if (capacity < contract_asset.len) return -2;
    @memcpy(dst[0..contract_asset.len], contract_asset[0..contract_asset.len]);
    return @intCast(contract_asset.len);
}
// SENS owns all Sanskrit surface definitions; Zig only copies the original bytes.
const sanskrit_asset = @embedFile("lib/surface/sa.lisp");
pub export fn sens_zig_sanskrit_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (sanskrit_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(sanskrit_asset.len);
    if (capacity < sanskrit_asset.len) return -2;
    @memcpy(dst[0..sanskrit_asset.len], sanskrit_asset[0..sanskrit_asset.len]);
    return @intCast(sanskrit_asset.len);
}
// Ukrainian peer surface is unchanged source bytes, not a code or name registry.
const ukr_asset = @embedFile("lib/surface/ukr.lisp");
pub export fn sens_zig_ukr_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (ukr_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(ukr_asset.len);
    if (capacity < ukr_asset.len) return -2;
    @memcpy(dst[0..ukr_asset.len], ukr_asset[0..ukr_asset.len]);
    return @intCast(ukr_asset.len);
}
// Transport, never interpretation of canonical Ukrainian identifiers.
const uk_asset = @embedFile("lib/surface/uk.lisp");
pub export fn sens_zig_uk_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (uk_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(uk_asset.len);
    if (capacity < uk_asset.len) return -2;
    @memcpy(dst[0..uk_asset.len], uk_asset[0..uk_asset.len]);
    return @intCast(uk_asset.len);
}
// Ukrainian API documentation is a SENS-owned source. Zig only copies bytes.
const uk_docs_asset = @embedFile("lib/surface/uk-docs.lisp");
pub export fn sens_zig_uk_docs_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (uk_docs_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(uk_docs_asset.len);
    if (capacity < uk_docs_asset.len) return -2;
    @memcpy(dst[0..uk_docs_asset.len], uk_docs_asset[0..uk_docs_asset.len]);
    return @intCast(uk_docs_asset.len);
}

// Джерело уніфікації належить SENS; Zig переносить тільки точні байти.
const unify_asset = @embedFile("lib/unify.lisp");
pub export fn sens_zig_unify_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (unify_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(unify_asset.len);
    if (capacity < unify_asset.len) return -2;
    @memcpy(dst[0..unify_asset.len], unify_asset[0..unify_asset.len]);
    return @intCast(unify_asset.len);
}

// SENS owns unification/reasoning semantics. Zig only copies exact source bytes.
const reason_asset = @embedFile("lib/reason.lisp");
pub export fn sens_zig_reason_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (reason_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(reason_asset.len);
    if (capacity < reason_asset.len) return -2;
    @memcpy(dst[0..reason_asset.len], reason_asset[0..reason_asset.len]);
    return @intCast(reason_asset.len);
}

// The SENS forward-chaining program is opaque to Zig. Copy exact source bytes.
const forward_asset = @embedFile("lib/forward.lisp");
pub export fn sens_zig_forward_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (forward_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(forward_asset.len);
    if (capacity < forward_asset.len) return -2;
    @memcpy(dst[0..forward_asset.len], forward_asset[0..forward_asset.len]);
    return @intCast(forward_asset.len);
}

// Original SENS knowledge library; Zig copies bytes and never defines meaning.
const knowledge_asset = @embedFile("lib/knowledge.lisp");
pub export fn sens_zig_knowledge_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (knowledge_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(knowledge_asset.len);
    if (capacity < knowledge_asset.len) return -2;
    @memcpy(dst[0..knowledge_asset.len], knowledge_asset[0..knowledge_asset.len]);
    return @intCast(knowledge_asset.len);
}

// Release-islands manifest is opaque distribution data. Zig transports
// exact checked-in bytes; Rust validates the JSON protocol, not the wire.
const islands_manifest_asset = @embedFile("packaging/islands-manifest-v1.json");
pub export fn sens_zig_islands_manifest_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (islands_manifest_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(islands_manifest_asset.len);
    if (capacity < islands_manifest_asset.len) return -2;
    @memcpy(dst[0..islands_manifest_asset.len], islands_manifest_asset[0..islands_manifest_asset.len]);
    return @intCast(islands_manifest_asset.len);
}

// External source-asset adapter: Zig copies opaque bytes; only SENS assigns meaning.
// Path/provenance policy belongs to the build and harness, never the physical codec.
const persistent_map_asset = @embedFile("lib/persistent-map.lisp");
pub export fn sens_zig_persistent_map_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (persistent_map_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(persistent_map_asset.len);
    if (capacity < persistent_map_asset.len) return -2;
    @memcpy(dst[0..persistent_map_asset.len], persistent_map_asset[0..persistent_map_asset.len]);
    return @intCast(persistent_map_asset.len);
}

const repl_persistent_map_t5m_asset = @embedFile("lib/persistent-map.sens");
pub export fn sens_zig_repl_persistent_map_t5m_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (repl_persistent_map_t5m_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(repl_persistent_map_t5m_asset.len);
    if (capacity < repl_persistent_map_t5m_asset.len) return -2;
    @memcpy(dst[0..repl_persistent_map_t5m_asset.len], repl_persistent_map_t5m_asset[0..repl_persistent_map_t5m_asset.len]);
    return @intCast(repl_persistent_map_t5m_asset.len);
}

// Root-only F6 World source carrier: opaque bytes, never semantic admission.
const world_asset = @embedFile("lib/world.lisp");
pub export fn sens_zig_world_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (world_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(world_asset.len);
    if (capacity < world_asset.len) return -2;
    @memcpy(dst[0..world_asset.len], world_asset[0..world_asset.len]);
    return @intCast(world_asset.len);
}

// F6 Content Store is SENS-owned; Zig transfers opaque bytes only.
const content_store_asset = @embedFile("lib/content-store.lisp");
pub export fn sens_zig_content_store_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (content_store_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(content_store_asset.len);
    if (capacity < content_store_asset.len) return -2;
    @memcpy(dst[0..content_store_asset.len], content_store_asset[0..content_store_asset.len]);
    return @intCast(content_store_asset.len);
}
// Exact REPL prerequisite bytes. Zig copies; SENS decides semantics.

const repl_persistent_vector_t5m_asset = @embedFile("lib/persistent-vector.sens");
pub export fn sens_zig_repl_persistent_vector_t5m_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (repl_persistent_vector_t5m_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(repl_persistent_vector_t5m_asset.len);
    if (capacity < repl_persistent_vector_t5m_asset.len) return -2;
    @memcpy(dst[0..repl_persistent_vector_t5m_asset.len], repl_persistent_vector_t5m_asset[0..repl_persistent_vector_t5m_asset.len]);
    return @intCast(repl_persistent_vector_t5m_asset.len);
}
const d9_string_append_asset = @embedFile("tests/semantic/d9-string-append-physical.lisp");
pub export fn sens_zig_d9_string_append_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (d9_string_append_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(d9_string_append_asset.len);
    if (capacity < d9_string_append_asset.len) return -2;
    @memcpy(dst[0..d9_string_append_asset.len], d9_string_append_asset[0..d9_string_append_asset.len]);
    return @intCast(d9_string_append_asset.len);
}

const repl_epistemic_t5m_asset = @embedFile("lib/epistemic.sens");
pub export fn sens_zig_repl_epistemic_t5m_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (repl_epistemic_t5m_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(repl_epistemic_t5m_asset.len);
    if (capacity < repl_epistemic_t5m_asset.len) return -2;
    @memcpy(dst[0..repl_epistemic_t5m_asset.len], repl_epistemic_t5m_asset[0..repl_epistemic_t5m_asset.len]);
    return @intCast(repl_epistemic_t5m_asset.len);
}
const lisp_fs_asset = @embedFile("lib/lisp-fs.lisp");
pub export fn sens_zig_lisp_fs_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (lisp_fs_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(lisp_fs_asset.len);
    if (capacity < lisp_fs_asset.len) return -2;
    @memcpy(dst[0..lisp_fs_asset.len], lisp_fs_asset[0..lisp_fs_asset.len]);
    return @intCast(lisp_fs_asset.len);
}
// Domain projection tables cross the corridor as opaque bytes. SENS parses
// and interprets them; the index selects only which checked-in asset to copy.
const domain_projection_assets = @import("domain_projection_assets.zig");
const domain_table_assets = domain_projection_assets.tables;

pub export fn sens_zig_domain_table_bytes_copy(domain: u8, dst: [*]u8, capacity: usize) isize {
    return domain_projection_assets.copy(domain, dst, capacity);
}

const compiler_nucleus_asset = @embedFile("lib/compiler-nucleus.lisp");
const compiler_identity_corpus_asset =
    @embedFile("contracts/compiler-nucleus-identity-corpus-v1.tsv");
const compiler_contract_asset = @embedFile("language-contract.lisp");
const compiler_d3_projection_asset =
    @embedFile("knowledge/bija3-l1-l5-structure-projection.json");
const compiler_d3_authority_asset = @embedFile("contracts/bija3-l1-l5-ratification.lisp");
const compiler_d4_projection_asset =
    @embedFile("knowledge/d4-bootstrap-compiler-structure-projection.json");
const compiler_d4_authority_asset = @embedFile("contracts/d4-bootstrap-ratification.lisp");

fn copy_compiler_asset(asset: []const u8, dst: [*]u8, capacity: usize) isize {
    if (asset.len == 0) return -1;
    if (capacity == 0) return @intCast(asset.len);
    if (capacity < asset.len) return -2;
    @memcpy(dst[0..asset.len], asset);
    return @intCast(asset.len);
}

pub export fn sens_zig_compiler_nucleus_bytes_copy(dst: [*]u8, capacity: usize) isize {
    return copy_compiler_asset(compiler_nucleus_asset, dst, capacity);
}

pub export fn sens_zig_compiler_identity_corpus_bytes_copy(
    dst: [*]u8,
    capacity: usize,
) isize {
    return copy_compiler_asset(compiler_identity_corpus_asset, dst, capacity);
}

pub export fn sens_zig_compiler_contract_bytes_copy(dst: [*]u8, capacity: usize) isize {
    return copy_compiler_asset(compiler_contract_asset, dst, capacity);
}

pub export fn sens_zig_compiler_d3_projection_bytes_copy(dst: [*]u8, capacity: usize) isize {
    return copy_compiler_asset(compiler_d3_projection_asset, dst, capacity);
}

pub export fn sens_zig_compiler_d3_authority_bytes_copy(dst: [*]u8, capacity: usize) isize {
    return copy_compiler_asset(compiler_d3_authority_asset, dst, capacity);
}

pub export fn sens_zig_compiler_d4_projection_bytes_copy(dst: [*]u8, capacity: usize) isize {
    return copy_compiler_asset(compiler_d4_projection_asset, dst, capacity);
}

pub export fn sens_zig_compiler_d4_authority_bytes_copy(dst: [*]u8, capacity: usize) isize {
    return copy_compiler_asset(compiler_d4_authority_asset, dst, capacity);
}

// This live host-data file intentionally remains reloadable without rebuilding
// the CLI. Rust receives bytes only through this Zig-owned, fixed-path adapter.
const CFile = opaque {};
extern "c" fn fopen([*:0]const u8, [*:0]const u8) ?*CFile;
extern "c" fn fclose(*CFile) c_int;
extern "c" fn fseek(*CFile, c_long, c_int) c_int;
extern "c" fn ftell(*CFile) c_long;
extern "c" fn fread([*]u8, usize, usize, *CFile) usize;

const guard_reference_path: [*:0]const u8 = "knowledge/guard-reference.lisp";
const guard_reference_crate_relative_path: [*:0]const u8 = "../../knowledge/guard-reference.lisp";
const guard_reference_read_limit: usize = 8 * 1024 * 1024;

pub export fn sens_zig_guard_reference_bytes_copy(dst: [*]u8, capacity: usize) isize {
    const file = fopen(guard_reference_path, "rb") orelse
        fopen(guard_reference_crate_relative_path, "rb") orelse return -1;
    defer _ = fclose(file);
    if (fseek(file, 0, 2) != 0) return -1;
    const end = ftell(file);
    if (end <= 0) return -1;
    const len: usize = @intCast(end);
    if (len > guard_reference_read_limit) return -3;
    if (capacity == 0) return @intCast(len);
    if (capacity < len) return -2;
    if (fseek(file, 0, 0) != 0) return -1;

    const temporary = std.heap.page_allocator.alloc(u8, len) catch return -4;
    defer std.heap.page_allocator.free(temporary);
    if (fread(temporary.ptr, 1, len, file) != len) return -1;
    @memcpy(dst[0..len], temporary);
    return @intCast(len);
}

fn expectOpaqueAssetCopy(copy_fn: anytype) !void {
    const allocator = std.testing.allocator;
    var short = [_]u8{0xa5};
    const required = copy_fn(short[0..].ptr, 0);
    try std.testing.expect(required > 1);
    try std.testing.expectEqual(@as(isize, -2), copy_fn(short[0..].ptr, short.len));
    try std.testing.expectEqual(@as(u8, 0xa5), short[0]);

    const len: usize = @intCast(required);
    const bytes = try allocator.alloc(u8, len);
    defer allocator.free(bytes);
    try std.testing.expectEqual(required, copy_fn(bytes.ptr, bytes.len));
}

fn expectDomainProjectionCopy(domain: u8) !void {
    const allocator = std.testing.allocator;
    var short = [_]u8{0xa5};
    const required = sens_zig_domain_table_bytes_copy(domain, short[0..].ptr, 0);
    try std.testing.expect(required > 1);
    try std.testing.expectEqual(
        @as(isize, -2),
        sens_zig_domain_table_bytes_copy(domain, short[0..].ptr, short.len),
    );
    try std.testing.expectEqual(@as(u8, 0xa5), short[0]);

    const len: usize = @intCast(required);
    const bytes = try allocator.alloc(u8, len);
    defer allocator.free(bytes);
    try std.testing.expectEqual(
        required,
        sens_zig_domain_table_bytes_copy(domain, bytes.ptr, bytes.len),
    );
}

test "Rust core READ T5M assets use bounded caller-owned copies" {
    try expectOpaqueAssetCopy(sens_zig_f6_lisp_fs_t5m_bytes_copy);
    try expectOpaqueAssetCopy(sens_zig_f6_producer_witness_t5m_bytes_copy);
}

test "Rust build domain projections copy D1 and D11 without inventing indexes" {
    var probe = [_]u8{0xa5};
    try std.testing.expectEqual(
        @as(isize, -1),
        sens_zig_domain_table_bytes_copy(0, probe[0..].ptr, 0),
    );
    try std.testing.expectEqual(
        @as(isize, -1),
        sens_zig_domain_table_bytes_copy(12, probe[0..].ptr, 0),
    );
    try expectDomainProjectionCopy(1);
    try expectDomainProjectionCopy(11);
}

test "Rust bootstrap slot checks copy nonempty SENS-owned T5M assets" {
    try expectOpaqueAssetCopy(sens_zig_repl_core_t5m_bytes_copy);
    try expectOpaqueAssetCopy(sens_zig_meta_eval_t5m_bytes_copy);
    try expectOpaqueAssetCopy(sens_zig_linter_t5m_bytes_copy);
}

