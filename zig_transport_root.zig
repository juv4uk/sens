//! Root-scoped Zig 0.16 module for the sterile, host-neutral transport ABI.
//! The root module alone can @embedFile checked-in assets in lib/; Zig copies
//! exact bytes, never decides Lisp meaning or executable SENS identities.
const std = @import("std");
const abi = @import("research/zig-codecs/transport_abi.zig");

test "Rust core READ has no direct OS input route" {
    // Перевіряємо саме місце колишнього обходу: успішний T5M roundtrip
    // сам собою не доводить відсутність читання ОС у Rust READ.
    const source = @embedFile("crates/sens/src/eval/special_forms/io.rs");
    try std.testing.expect(std.mem.indexOf(u8, source, "std::io") == null);
    try std.testing.expect(std.mem.indexOf(u8, source, "read_stdin_line") == null);
}

// Keep all existing public C exports reachable without re-implementing them.
comptime {
    _ = abi.sens_zig_codec_abi_version;
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

test "ukrainian SENS REPL T5M bytes cross Zig exactly, short buffer is untouched" {
    const expected: isize = @intCast(repl_core_t5m_asset.len);
    try std.testing.expectEqual(expected, sens_zig_repl_core_t5m_bytes_copy(undefined, 0));
    var small: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_repl_core_t5m_bytes_copy(&small, small.len));
    try std.testing.expectEqual(@as(u8, 0xA5), small[0]);
    var exact: [repl_core_t5m_asset.len]u8 = undefined;
    try std.testing.expectEqual(expected, sens_zig_repl_core_t5m_bytes_copy(&exact, exact.len));
    try std.testing.expectEqualSlices(u8, repl_core_t5m_asset[0..repl_core_t5m_asset.len], &exact);
}

test "Zig byte carrier refuses one-byte-short destinations without partial writes" {
    // Перевіряємо виключно байтову межу, не семантику Lisp чи коди доменів.
    var output: [repl_core_t5m_asset.len]u8 = undefined;
    @memset(output[0..], 0xA5);
    try std.testing.expectEqual(
        @as(isize, -2),
        sens_zig_repl_core_t5m_bytes_copy(&output, output.len - 1),
    );
    for (output) |byte| {
        try std.testing.expectEqual(@as(u8, 0xA5), byte);
    }
    const expected: isize = @intCast(repl_core_t5m_asset.len);
    try std.testing.expectEqual(expected, sens_zig_repl_core_t5m_bytes_copy(&output, output.len));
    try std.testing.expectEqualSlices(u8, repl_core_t5m_asset, &output);

    // Meta-eval так само передає лише фізичні T5M-байти.
    // Буфер із нестачею одного байта не може бути змінено навіть частково.
    var meta_out: [meta_eval_t5m_asset.len]u8 = undefined;
    @memset(meta_out[0..], 0xA5);
    try std.testing.expectEqual(
        @as(isize, -2),
        sens_zig_meta_eval_t5m_bytes_copy(&meta_out, meta_out.len - 1),
    );
    for (meta_out) |byte| {
        try std.testing.expectEqual(@as(u8, 0xA5), byte);
    }
    const meta_expected: isize = @intCast(meta_eval_t5m_asset.len);
    try std.testing.expectEqual(meta_expected, sens_zig_meta_eval_t5m_bytes_copy(&meta_out, meta_out.len));
    try std.testing.expectEqualSlices(u8, meta_eval_t5m_asset, &meta_out);
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

test "SENS meta-evaluator T5M bytes cross Zig exactly, short buffer is untouched" {
    const expected: isize = @intCast(meta_eval_t5m_asset.len);
    try std.testing.expectEqual(expected, sens_zig_meta_eval_t5m_bytes_copy(undefined, 0));
    var small: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_meta_eval_t5m_bytes_copy(&small, small.len));
    try std.testing.expectEqual(@as(u8, 0xA5), small[0]);
    var exact: [meta_eval_t5m_asset.len]u8 = undefined;
    try std.testing.expectEqual(expected, sens_zig_meta_eval_t5m_bytes_copy(&exact, exact.len));
    try std.testing.expectEqualSlices(u8, meta_eval_t5m_asset[0..meta_eval_t5m_asset.len], &exact);
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
test "Sanskrit surface Zig C ABI copies exact bytes and refuses short buffers" {
    const length = sens_zig_sanskrit_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(sanskrit_asset.len)), length);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_sanskrit_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var out: [sanskrit_asset.len]u8 = undefined;
    try std.testing.expectEqual(length, sens_zig_sanskrit_bytes_copy(&out, out.len));
    try std.testing.expectEqualSlices(u8, sanskrit_asset[0..sanskrit_asset.len], &out);
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
test "exact Ukrainian peer source, short copy refuses without writing" {
    const length = sens_zig_ukr_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(ukr_asset.len)), length);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_ukr_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var out: [ukr_asset.len]u8 = undefined;
    try std.testing.expectEqual(length, sens_zig_ukr_bytes_copy(&out, out.len));
    try std.testing.expectEqualSlices(u8, ukr_asset[0..ukr_asset.len], &out);
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
test "compact Ukrainian bytes copied exactly; short buffer is untouched" {
    const length = sens_zig_uk_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(uk_asset.len)), length);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_uk_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var output: [uk_asset.len]u8 = undefined;
    try std.testing.expectEqual(length, sens_zig_uk_bytes_copy(&output, output.len));
    try std.testing.expectEqualSlices(u8, uk_asset[0..uk_asset.len], &output);
}

test "contract exact-byte copy and no partial output on a short buffer" {
    const length = sens_zig_contract_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(contract_asset.len)), length);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_contract_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var destination: [contract_asset.len]u8 = undefined;
    try std.testing.expectEqual(length, sens_zig_contract_bytes_copy(&destination, destination.len));
    try std.testing.expectEqualSlices(u8, contract_asset[0..contract_asset.len], &destination);
}

test "physical linter T5M crosses Zig without partial writes or semantic registry" {
    const required = sens_zig_linter_t5m_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(linter_t5m_asset.len)), required);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_linter_t5m_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var output: [linter_t5m_asset.len]u8 = undefined;
    try std.testing.expectEqual(required, sens_zig_linter_t5m_bytes_copy(&output, output.len));
    try std.testing.expectEqualSlices(u8, linter_t5m_asset[0..linter_t5m_asset.len], &output);
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

test "Ukrainian API docs exact Zig bytes and no partial short-buffer write" {
    const required = sens_zig_uk_docs_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(uk_docs_asset.len)), required);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_uk_docs_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var output: [uk_docs_asset.len]u8 = undefined;
    try std.testing.expectEqual(required, sens_zig_uk_docs_bytes_copy(&output, output.len));
    try std.testing.expectEqualSlices(u8, uk_docs_asset[0..uk_docs_asset.len], &output);
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

test "REPL unify source: exact Zig bytes and short buffer remains untouched" {
    const required = sens_zig_unify_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(unify_asset.len)), required);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_unify_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var output: [unify_asset.len]u8 = undefined;
    try std.testing.expectEqual(required, sens_zig_unify_bytes_copy(&output, output.len));
    try std.testing.expectEqualSlices(u8, unify_asset[0..unify_asset.len], &output);
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

test "reason SENS source via Zig exact byte ABI; short buffer untouched" {
    const length = sens_zig_reason_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(reason_asset.len)), length);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_reason_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var result: [reason_asset.len]u8 = undefined;
    try std.testing.expectEqual(length, sens_zig_reason_bytes_copy(&result, result.len));
    try std.testing.expectEqualSlices(u8, reason_asset[0..reason_asset.len], &result);
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

test "forward REPL source exact Zig C bytes; short buffer stays unchanged" {
    const required = sens_zig_forward_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(forward_asset.len)), required);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_forward_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var output: [forward_asset.len]u8 = undefined;
    try std.testing.expectEqual(required, sens_zig_forward_bytes_copy(&output, output.len));
    try std.testing.expectEqualSlices(u8, forward_asset[0..forward_asset.len], &output);
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

test "knowledge SENS source exact Zig C ABI bytes; no-clobber on short buffer" {
    const length = sens_zig_knowledge_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(knowledge_asset.len)), length);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_knowledge_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var output: [knowledge_asset.len]u8 = undefined;
    try std.testing.expectEqual(length, sens_zig_knowledge_bytes_copy(&output, output.len));
    try std.testing.expectEqualSlices(u8, knowledge_asset[0..knowledge_asset.len], &output);
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

test "islands release manifest exact bytes via Zig; short buffer not modified" {
    const required = sens_zig_islands_manifest_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(islands_manifest_asset.len)), required);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_islands_manifest_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var output: [islands_manifest_asset.len]u8 = undefined;
    try std.testing.expectEqual(required, sens_zig_islands_manifest_bytes_copy(&output, output.len));
    try std.testing.expectEqualSlices(u8, islands_manifest_asset[0..islands_manifest_asset.len], &output);
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

test "REPL persistent-map T5M bytes copy exactly and preserve short buffer" {
    const length = sens_zig_repl_persistent_map_t5m_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(repl_persistent_map_t5m_asset.len)), length);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_repl_persistent_map_t5m_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var full: [repl_persistent_map_t5m_asset.len]u8 = undefined;
    try std.testing.expectEqual(length, sens_zig_repl_persistent_map_t5m_bytes_copy(&full, full.len));
    try std.testing.expectEqualSlices(u8, repl_persistent_map_t5m_asset[0..repl_persistent_map_t5m_asset.len], &full);
}

test "F6 persistent-map carrier: exact Zig bytes and unchanged short buffer" {
    const required = sens_zig_persistent_map_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(persistent_map_asset.len)), required);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_persistent_map_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var output: [persistent_map_asset.len]u8 = undefined;
    try std.testing.expectEqual(required, sens_zig_persistent_map_bytes_copy(&output, output.len));
    try std.testing.expectEqualSlices(u8, persistent_map_asset[0..persistent_map_asset.len], &output);
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

test "F6 World carrier: exact Zig bytes and unchanged short buffer" {
    const required = sens_zig_world_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(world_asset.len)), required);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_world_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var output: [world_asset.len]u8 = undefined;
    try std.testing.expectEqual(required, sens_zig_world_bytes_copy(&output, output.len));
    try std.testing.expectEqualSlices(u8, world_asset[0..world_asset.len], &output);
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
test "F6 Content Store exact Zig source and unchanged short buffer" {
    const required = sens_zig_content_store_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(content_store_asset.len)), required);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_content_store_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var output: [content_store_asset.len]u8 = undefined;
    try std.testing.expectEqual(required, sens_zig_content_store_bytes_copy(&output, output.len));
    try std.testing.expectEqualSlices(u8, content_store_asset[0..content_store_asset.len], &output);
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
test "REPL persistent-vector T5M bytes copy exactly and preserve short buffer" {
    const length = sens_zig_repl_persistent_vector_t5m_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(repl_persistent_vector_t5m_asset.len)), length);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_repl_persistent_vector_t5m_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var full: [repl_persistent_vector_t5m_asset.len]u8 = undefined;
    try std.testing.expectEqual(length, sens_zig_repl_persistent_vector_t5m_bytes_copy(&full, full.len));
    try std.testing.expectEqualSlices(u8, repl_persistent_vector_t5m_asset[0..repl_persistent_vector_t5m_asset.len], &full);
}

const d9_witness_asset = @embedFile("tests/semantic/d9-four-uk-projections-laws.lisp");
pub export fn sens_zig_d9_witness_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (d9_witness_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(d9_witness_asset.len);
    if (capacity < d9_witness_asset.len) return -2;
    @memcpy(dst[0..d9_witness_asset.len], d9_witness_asset[0..d9_witness_asset.len]);
    return @intCast(d9_witness_asset.len);
}

test "D9 witness source crosses Zig byte-exact, short buffer is untouched" {
    const length = sens_zig_d9_witness_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(d9_witness_asset.len)), length);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_d9_witness_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var full: [d9_witness_asset.len]u8 = undefined;
    try std.testing.expectEqual(length, sens_zig_d9_witness_bytes_copy(&full, full.len));
    try std.testing.expectEqualSlices(u8, d9_witness_asset[0..d9_witness_asset.len], &full);
}

const repl_epistemic_t5m_asset = @embedFile("lib/epistemic.sens");
pub export fn sens_zig_repl_epistemic_t5m_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (repl_epistemic_t5m_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(repl_epistemic_t5m_asset.len);
    if (capacity < repl_epistemic_t5m_asset.len) return -2;
    @memcpy(dst[0..repl_epistemic_t5m_asset.len], repl_epistemic_t5m_asset[0..repl_epistemic_t5m_asset.len]);
    return @intCast(repl_epistemic_t5m_asset.len);
}
test "REPL epistemic T5M bytes copy exactly and preserve short buffer" {
    const length = sens_zig_repl_epistemic_t5m_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(repl_epistemic_t5m_asset.len)), length);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_repl_epistemic_t5m_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var full: [repl_epistemic_t5m_asset.len]u8 = undefined;
    try std.testing.expectEqual(length, sens_zig_repl_epistemic_t5m_bytes_copy(&full, full.len));
    try std.testing.expectEqualSlices(u8, repl_epistemic_t5m_asset[0..repl_epistemic_t5m_asset.len], &full);
}

const lisp_fs_asset = @embedFile("lib/lisp-fs.lisp");
pub export fn sens_zig_lisp_fs_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (lisp_fs_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(lisp_fs_asset.len);
    if (capacity < lisp_fs_asset.len) return -2;
    @memcpy(dst[0..lisp_fs_asset.len], lisp_fs_asset[0..lisp_fs_asset.len]);
    return @intCast(lisp_fs_asset.len);
}
test "F6 lisp_fs exact bytes and unchanged short buffer" {
    const required = sens_zig_lisp_fs_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(lisp_fs_asset.len)), required);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_lisp_fs_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var full: [lisp_fs_asset.len]u8 = undefined;
    try std.testing.expectEqual(required, sens_zig_lisp_fs_bytes_copy(&full, full.len));
    try std.testing.expectEqualSlices(u8, lisp_fs_asset[0..lisp_fs_asset.len], &full);
}

// Domain projection tables cross the corridor as opaque bytes. SENS parses
// and interprets them; the index selects only which checked-in asset to copy.
const domain_table_assets = [_][]const u8{
    @embedFile("lib/domains/d1.lisp"),
    @embedFile("lib/domains/d2.lisp"),
    @embedFile("lib/domains/d3.lisp"),
    @embedFile("lib/domains/d4.lisp"),
    @embedFile("lib/domains/d5.lisp"),
    @embedFile("lib/domains/d6.lisp"),
    @embedFile("lib/domains/d7.lisp"),
    @embedFile("lib/domains/d8.lisp"),
    @embedFile("lib/domains/d9.lisp"),
    @embedFile("lib/domains/d10.lisp"),
    @embedFile("lib/domains/d11.lisp"),
};

pub export fn sens_zig_domain_table_bytes_copy(domain: u8, dst: [*]u8, capacity: usize) isize {
    if (domain == 0 or domain > domain_table_assets.len) return -1;
    const asset = domain_table_assets[@as(usize, domain) - 1];
    if (asset.len == 0) return -1;
    if (capacity == 0) return @intCast(asset.len);
    if (capacity < asset.len) return -2;
    @memcpy(dst[0..asset.len], asset);
    return @intCast(asset.len);
}

test "domain projection tables cross Zig byte-exact and refuse short writes" {
    const allocator = std.testing.allocator;
    for (domain_table_assets, 0..) |asset, index| {
        const domain: u8 = @intCast(index + 1);
        const required = sens_zig_domain_table_bytes_copy(domain, undefined, 0);
        try std.testing.expectEqual(@as(isize, @intCast(asset.len)), required);
        var short: [1]u8 = .{0xA5};
        try std.testing.expectEqual(
            @as(isize, -2),
            sens_zig_domain_table_bytes_copy(domain, &short, short.len),
        );
        try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
        const output = try allocator.alloc(u8, @intCast(required));
        defer allocator.free(output);
        try std.testing.expectEqual(
            required,
            sens_zig_domain_table_bytes_copy(domain, output.ptr, output.len),
        );
        try std.testing.expectEqualSlices(u8, asset, output);
    }
    try std.testing.expectEqual(
        @as(isize, -1),
        sens_zig_domain_table_bytes_copy(0, undefined, 0),
    );
    try std.testing.expectEqual(
        @as(isize, -1),
        sens_zig_domain_table_bytes_copy(12, undefined, 0),
    );
}

const compiler_nucleus_asset = @embedFile("lib/compiler-nucleus.lisp");
const compiler_identity_corpus_asset =
    @embedFile("contracts/compiler-nucleus-identity-corpus-v1.tsv");

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

test "compiler export assets cross Zig byte-exact without partial writes" {
    const assets = [_][]const u8{
        compiler_nucleus_asset,
        compiler_identity_corpus_asset,
    };
    inline for (assets, 0..) |asset, index| {
        // Експортовані функції мають C ABI: при виборі з двох адрес
        // використовуємо явний покажчик, а не comptime-only fn.
        const copy: *const fn ([*]u8, usize) callconv(.c) isize = if (index == 0)
            &sens_zig_compiler_nucleus_bytes_copy
        else
            &sens_zig_compiler_identity_corpus_bytes_copy;
        const required = copy(undefined, 0);
        try std.testing.expectEqual(@as(isize, @intCast(asset.len)), required);
        var short: [1]u8 = .{0xA5};
        try std.testing.expectEqual(@as(isize, -2), copy(&short, short.len));
        try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
        const output = try std.testing.allocator.alloc(u8, @intCast(required));
        defer std.testing.allocator.free(output);
        try std.testing.expectEqual(required, copy(output.ptr, output.len));
        try std.testing.expectEqualSlices(u8, asset, output);
    }
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

test "Guard reference source is read through Zig and a short buffer is untouched" {
    const required = sens_zig_guard_reference_bytes_copy(undefined, 0);
    try std.testing.expect(required > 0);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2), sens_zig_guard_reference_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    const allocator = std.testing.allocator;
    const actual = try allocator.alloc(u8, @intCast(required));
    defer allocator.free(actual);
    try std.testing.expectEqual(required, sens_zig_guard_reference_bytes_copy(actual.ptr, actual.len));
    try std.testing.expect(std.mem.startsWith(u8, actual, "; Guard reference bureau"));
    try std.testing.expect(std.mem.indexOf(u8, actual, "*guard-reference-directory*") != null);
}
