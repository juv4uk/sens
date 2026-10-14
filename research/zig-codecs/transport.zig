//! SENS transport CLI, Zig 0.17.0. The production T5/F3C *mechanism*
//! lives in Zig; the existing SENS reader/evaluator remains sole semantic owner.
//! Commands never execute a program and never guess the physical profile.
//! The filesystem adapter is libc-hosted; the codec itself does not do I/O.
const std = @import("std");
const t5 = @import("t5/t5.zig");
const f3c = @import("f3c/f3c.zig");

const CFile = opaque {};
extern "c" fn fopen([*:0]const u8, [*:0]const u8) ?*CFile;
extern "c" fn fclose(*CFile) c_int;
extern "c" fn fseek(*CFile, c_long, c_int) c_int;
extern "c" fn ftell(*CFile) c_long;
extern "c" fn fread([*]u8, usize, usize, *CFile) usize;
extern "c" fn fwrite([*]const u8, usize, usize, *CFile) usize;
extern "c" fn fflush(*CFile) c_int;
extern "c" fn remove([*:0]const u8) c_int;

const Error = error{
    Usage,
    WrongExtension,
    InputReadFailed,
    InputTooLarge,
    OutputExistsOrUnavailable,
    OutputWriteFailed,
    InputEqualsOutput,
    NotSmallerThanT5,
    CanonicalRoundtripMismatch,
};

fn requireExtension(path: []const u8, ext: []const u8) !void {
    if (!std.mem.endsWith(u8, path, ext)) return Error.WrongExtension;
}

fn readFile(allocator: std.mem.Allocator, path: []const u8) ![]u8 {
    const zpath = try allocator.dupeZ(u8, path);
    defer allocator.free(zpath);
    const file = fopen(zpath.ptr, "rb") orelse return Error.InputReadFailed;
    defer _ = fclose(file);
    if (fseek(file, 0, 2) != 0) return Error.InputReadFailed;
    const end = ftell(file);
    if (end < 0) return Error.InputReadFailed;
    if (@as(u64, @intCast(end)) > t5.MAX_PHYSICAL_BYTES + 1)
        return Error.InputTooLarge;
    if (fseek(file, 0, 0) != 0) return Error.InputReadFailed;
    const bytes = try allocator.alloc(u8, @intCast(end));
    errdefer allocator.free(bytes);
    if (bytes.len > 0 and fread(bytes.ptr, 1, bytes.len, file) != bytes.len)
        return Error.InputReadFailed;
    return bytes;
}

/// "wbx" means create exclusively, no existing-file overwrite.
/// If output verification fails, the newly created file is deleted.
fn writeFileNew(allocator: std.mem.Allocator, path: []const u8, body: []const u8) !void {
    const zpath = try allocator.dupeZ(u8, path);
    defer allocator.free(zpath);
    const file = fopen(zpath.ptr, "wbx") orelse return Error.OutputExistsOrUnavailable;
    var failed = true;
    defer {
        _ = fclose(file);
        if (failed) _ = remove(zpath.ptr);
    }
    if (body.len != 0 and fwrite(body.ptr, 1, body.len, file) != body.len)
        return Error.OutputWriteFailed;
    if (fflush(file) != 0) return Error.OutputWriteFailed;
    // The exact physical output must exist and be verified before success;
    // fclose is intentionally explicit before reading again via the caller.
    failed = false;
}

fn produce(allocator: std.mem.Allocator, command: []const u8, source: []const u8) ![]u8 {
    if (std.mem.eql(u8, command, "t5-roundtrip")) {
        const words = try t5.decode(allocator, source);
        defer allocator.free(words);
        return try t5.encode(allocator, words);
    }
    if (std.mem.eql(u8, command, "f3c-pack")) {
        return (try f3c.encode(allocator, source)) orelse Error.NotSmallerThanT5;
    }
    if (std.mem.eql(u8, command, "f3c-unpack")) {
        return try f3c.decode(allocator, source);
    }
    return Error.Usage;
}

fn check(allocator: std.mem.Allocator, command: []const u8, source: []const u8) !void {
    if (std.mem.eql(u8, command, "t5-check")) {
        const words = try t5.decode(allocator, source);
        defer allocator.free(words);
        return;
    }
    if (std.mem.eql(u8, command, "f3c-check")) {
        const t5_data = try f3c.decode(allocator, source);
        defer allocator.free(t5_data);
        return;
    }
    return Error.Usage;
}

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();
    const args = try init.minimal.args.toSlice(allocator);
    if (args.len < 3 or args.len > 4) return Error.Usage;
    const command = args[1];
    const source_path = args[2];
    const check_only = std.mem.eql(u8, command, "t5-check") or
        std.mem.eql(u8, command, "f3c-check");
    if (check_only and args.len != 3) return Error.Usage;
    if (!check_only and args.len != 4) return Error.Usage;

    const input_is_t5 =
        std.mem.eql(u8, command, "t5-check") or
        std.mem.eql(u8, command, "t5-roundtrip") or
        std.mem.eql(u8, command, "f3c-pack");
    const input_is_f3c = std.mem.eql(u8, command, "f3c-check") or
        std.mem.eql(u8, command, "f3c-unpack");
    if (!input_is_t5 and !input_is_f3c) return Error.Usage;
    try requireExtension(source_path, if (input_is_t5) ".sens" else ".senc");

    const original = try readFile(allocator, source_path);
    defer allocator.free(original);
    if (check_only) {
        try check(allocator, command, original);
        return;
    }
    const dest_path = args[3];
    if (std.mem.eql(u8, dest_path, source_path)) return Error.InputEqualsOutput;
    const dest_is_f3c = std.mem.eql(u8, command, "f3c-pack");
    try requireExtension(dest_path, if (dest_is_f3c) ".senc" else ".sens");
    const output = try produce(allocator, command, original);
    defer allocator.free(output);

    // Mandatory exact physical Zig roundtrip before touching the destination.
    if (dest_is_f3c) {
        const restored = try f3c.decode(allocator, output);
        defer allocator.free(restored);
        if (!std.mem.eql(u8, restored, original))
            return Error.CanonicalRoundtripMismatch;
    } else if (std.mem.eql(u8, command, "f3c-unpack")) {
        const recompressed = (try f3c.encode(allocator, output)) orelse
            return Error.CanonicalRoundtripMismatch;
        defer allocator.free(recompressed);
        if (!std.mem.eql(u8, recompressed, original))
            return Error.CanonicalRoundtripMismatch;
    } else if (!std.mem.eql(u8, original, output)) {
        return Error.CanonicalRoundtripMismatch;
    }

    try writeFileNew(allocator, dest_path, output);
    const reopened = try readFile(allocator, dest_path);
    defer allocator.free(reopened);
    if (!std.mem.eql(u8, reopened, output)) {
        const zpath = try allocator.dupeZ(u8, dest_path);
        defer allocator.free(zpath);
        _ = remove(zpath.ptr);
        return Error.CanonicalRoundtripMismatch;
    }
}
