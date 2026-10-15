//! Root-scoped Zig 0.16 module for the sterile, host-neutral transport ABI.
//! The root module alone can @embedFile checked-in assets in lib/; Zig copies
//! exact bytes, never decides Lisp meaning or executable SENS identities.
const std = @import("std");
const abi = @import("research/zig-codecs/transport_abi.zig");

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

// A single opaque asset, not a symbol registry. The caller owns memory;
// capacity=0 queries exact byte length. -2 is fail-closed, no partial write.
const linter_asset = @embedFile("lib/linter.lisp");
pub export fn sens_zig_linter_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (linter_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(linter_asset.len);
    if (capacity < linter_asset.len) return -2;
    @memcpy(dst[0..linter_asset.len], linter_asset[0..linter_asset.len]);
    return @intCast(linter_asset.len);
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

test "opaque linter bytes cross Zig without partial writes or semantic registry" {
    const required = sens_zig_linter_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(linter_asset.len)), required);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2),
        sens_zig_linter_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var output: [linter_asset.len]u8 = undefined;
    try std.testing.expectEqual(required,
        sens_zig_linter_bytes_copy(&output, output.len));
    try std.testing.expectEqualSlices(u8, linter_asset[0..linter_asset.len], &output);
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
    try std.testing.expectEqual(@as(isize, -2),
        sens_zig_islands_manifest_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var output: [islands_manifest_asset.len]u8 = undefined;
    try std.testing.expectEqual(required,
        sens_zig_islands_manifest_bytes_copy(&output, output.len));
    try std.testing.expectEqualSlices(u8, islands_manifest_asset[0..islands_manifest_asset.len], &output);
}
