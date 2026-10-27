//! SENS transport CLI, Zig 0.16.0. The production T5/F3C *mechanism*
//! lives in Zig; the existing SENS reader/evaluator remains sole semantic owner.
//! Commands never execute a program and never guess the physical profile.
//! The filesystem adapter is libc-hosted; the codec itself does not do I/O.
const std = @import("std");
const builtin = @import("builtin");
const t5 = @import("t5/t5.zig");
const t5m = @import("t5m.zig");
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
extern "c" fn mkstemp([*:0]u8) c_int;
extern "c" fn fdopen(c_int, [*:0]const u8) ?*CFile;
extern "c" fn close(c_int) c_int;
extern "c" fn link([*:0]const u8, [*:0]const u8) c_int;
// Linux-only anonymous staging: fall back to mkstemp on other systems.
extern "c" fn open([*:0]const u8, c_int, c_uint) c_int;
extern "c" fn linkat(c_int, [*:0]const u8, c_int, [*:0]const u8, c_int) c_int;
extern "c" fn fsync(c_int) c_int;
extern "c" fn fileno(*CFile) c_int;
const CDir = opaque {};
extern "c" fn opendir([*:0]const u8) ?*CDir;
extern "c" fn dirfd(*CDir) c_int;
extern "c" fn closedir(*CDir) c_int;

const Error = error{
    Usage,
    WrongExtension,
    InputReadFailed,
    InputTooLarge,
    OutputExistsOrUnavailable,
    OutputWriteFailed,
    OutputSyncFailed,
    InputEqualsOutput,
    NotSmallerThanT5,
    CanonicalRoundtripMismatch,
    InvalidTrit,
    InvalidTritBoundary,
    InvalidT5MWord,
};

fn requireExtension(path: []const u8, ext: []const u8) !void {
    if (!std.mem.endsWith(u8, path, ext)) return Error.WrongExtension;
}

fn readFile(allocator: std.mem.Allocator, path: []const u8, max_bytes: usize) ![]u8 {
    const zpath = try allocator.dupeZ(u8, path);
    defer allocator.free(zpath);
    const file = fopen(zpath.ptr, "rb") orelse return Error.InputReadFailed;
    defer _ = fclose(file);
    if (fseek(file, 0, 2) != 0) return Error.InputReadFailed;
    const end = ftell(file);
    if (end < 0) return Error.InputReadFailed;
    if (@as(u64, @intCast(end)) > @as(u64, @intCast(max_bytes)))
        return Error.InputTooLarge;
    if (fseek(file, 0, 0) != 0) return Error.InputReadFailed;
    const bytes = try allocator.alloc(u8, @intCast(end));
    errdefer allocator.free(bytes);
    if (bytes.len > 0 and fread(bytes.ptr, 1, bytes.len, file) != bytes.len)
        return Error.InputReadFailed;
    return bytes;
}

/// Create a private stage in the destination directory. Verification failures
/// remove ONLY this stage, never a public destination owned by another writer.
fn createVerifiedStage(
    allocator: std.mem.Allocator,
    dest_path: []const u8,
    body: []const u8,
    expected: []const u8,
) ![:0]u8 {
    const suffix = ".tmp.XXXXXX";
    const stage = try allocator.allocSentinel(u8, dest_path.len + suffix.len, 0);
    errdefer allocator.free(stage);
    @memcpy(stage[0..dest_path.len], dest_path);
    @memcpy(stage[dest_path.len..stage.len], suffix);

    // Unique, exclusive 0600 file on the SAME filesystem as the final name.
    const fd = mkstemp(stage.ptr);
    if (fd < 0) return Error.OutputWriteFailed;
    errdefer _ = remove(stage.ptr);
    const file = fdopen(fd, "wb") orelse {
        _ = close(fd);
        return Error.OutputWriteFailed;
    };
    var file_stream_open = true;
    defer {
        if (file_stream_open) _ = fclose(file);
    }
    if (body.len != 0 and fwrite(body.ptr, 1, body.len, file) != body.len)
        return Error.OutputWriteFailed;
    if (fflush(file) != 0) return Error.OutputWriteFailed;
    // fflush flushes the C buffer, NOT the filesystem's dirty pages.
    // An fsync failure must prevent this stage from becoming public.
    if (fsync(fileno(file)) != 0) return Error.OutputSyncFailed;
    const close_result = fclose(file);
    file_stream_open = false;
    if (close_result != 0) return Error.OutputWriteFailed;

    // Exact known size, including large presegmented trit fixtures.
    const reopened = try readFile(allocator, stage, body.len);
    defer allocator.free(reopened);
    if (!std.mem.eql(u8, reopened, expected))
        return Error.CanonicalRoundtripMismatch;
    return stage;
}

/// Publish only by creating a NEW hard link. Existing names are never
/// overwritten, even if another process created them after stage verification.
fn publishVerifiedStage(
    allocator: std.mem.Allocator,
    stage: [:0]const u8,
    dest_path: []const u8,
) !void {
    const dest = try allocator.dupeZ(u8, dest_path);
    defer allocator.free(dest);
    if (link(stage.ptr, dest.ptr) != 0) return Error.OutputExistsOrUnavailable;
}

/// Make the directory-entry change durable, not merely visible.
/// File data is already fsync'd before the hard link is published.
fn syncParentDirectory(allocator: std.mem.Allocator, path: []const u8) !void {
    const parent = std.fs.path.dirname(path) orelse ".";
    const zparent = try allocator.dupeZ(u8, parent);
    defer allocator.free(zparent);
    const dir = opendir(zparent.ptr) orelse return Error.OutputSyncFailed;
    defer _ = closedir(dir);
    const fd = dirfd(dir);
    if (fd < 0 or fsync(fd) != 0) return Error.OutputSyncFailed;
}

/// On Linux, prefer an unnamed inode: a crash before linkat then leaves NO
/// *.tmp.* entry to collect. This backend is an optimization of the existing
/// portable mkstemp + link path, never a second semantic codec.
/// Returns false when the filesystem cannot publish O_TMPFILE; caller then
/// uses the existing exclusive, verified named-stage fallback.
fn tryWriteAnonymous(
    allocator: std.mem.Allocator,
    dest_path: []const u8,
    body: []const u8,
) !bool {
    if (builtin.os.tag != .linux) return false;
    const parent = std.fs.path.dirname(dest_path) orelse ".";
    const parent_z = try allocator.dupeZ(u8, parent);
    defer allocator.free(parent_z);
    // Linux asm-generic: O_TMPFILE = __O_TMPFILE | O_DIRECTORY.
    // Opening an unnamed inode in the destination directory guarantees
    // same-filesystem publication without a crash-leaked temporary name.
    const fd = open(parent_z.ptr, 0o20200002, 0o600);
    if (fd < 0) return false;

    const file = fdopen(fd, "w+b") orelse {
        _ = close(fd);
        return Error.OutputWriteFailed;
    };
    var stream_open = true;
    defer {
        if (stream_open) _ = fclose(file);
    }
    if (body.len != 0 and fwrite(body.ptr, 1, body.len, file) != body.len)
        return Error.OutputWriteFailed;
    if (fflush(file) != 0) return Error.OutputWriteFailed;
    if (fsync(fileno(file)) != 0) return Error.OutputSyncFailed;

    // Validate the actual persisted inode in bounded chunks without a second
    // allocation proportional to user input, preserving large .trits fixtures.
    if (fseek(file, 0, 0) != 0) return Error.OutputWriteFailed;
    var scratch: [4096]u8 = undefined;
    var offset: usize = 0;
    while (offset < body.len) {
        const count = @min(scratch.len, body.len - offset);
        if (fread(scratch[0..].ptr, 1, count, file) != count)
            return Error.CanonicalRoundtripMismatch;
        if (!std.mem.eql(u8, scratch[0..count], body[offset .. offset + count]))
            return Error.CanonicalRoundtripMismatch;
        offset += count;
    }

    const dest_z = try allocator.dupeZ(u8, dest_path);
    defer allocator.free(dest_z);
    // AT_FDCWD = -100, AT_EMPTY_PATH = 0x1000 on Linux. Neither this
    // operation nor the portable fallback overwrites an existing target.
    if (linkat(fileno(file), "", -100, dest_z.ptr, 0x1000) != 0)
        return false;

    const close_result = fclose(file);
    stream_open = false;
    if (close_result != 0) return Error.OutputWriteFailed;
    try syncParentDirectory(allocator, dest_path);
    return true;
}

fn writeVerifiedNew(
    allocator: std.mem.Allocator,
    dest_path: []const u8,
    body: []const u8,
) !void {
    if (try tryWriteAnonymous(allocator, dest_path, body)) return;
    const stage = try createVerifiedStage(allocator, dest_path, body, body);
    defer allocator.free(stage);
    var stage_exists = true;
    defer {
        // The stage is ours, the destination is shared; never unlink dest.
        if (stage_exists) _ = remove(stage.ptr);
    }
    try publishVerifiedStage(allocator, stage, dest_path);
    // On a failed unlink, report failure instead of claiming durability.
    if (remove(stage.ptr) != 0) return Error.OutputWriteFailed;
    stage_exists = false;
    // Persist the published name AND the stage-name removal.
    try syncParentDirectory(allocator, dest_path);
}

/// Physical T5 emission from PRE-SEGMENTED, opaque trits.
/// 0/1 are payload and 2 is solely the physical word boundary.
/// The upstream SENS projection already supplies each exact boundary.
/// This function has NO domain registry, name mapping or semantic dispatch.
fn carryTrits(allocator: std.mem.Allocator, source: []const u8) ![]u8 {
    if (source.len == 0) return Error.InvalidTritBoundary;
    if (source.len > t5.MAX_PHYSICAL_BYTES * 5) return Error.InputTooLarge;
    const out = try allocator.alloc(u8, (source.len + 4) / 5);
    errdefer allocator.free(out);
    var index: usize = 0;
    var value: u8 = 0;
    var used: u8 = 0;
    var after_payload = false;
    for (source) |ch| {
        if (ch != '0' and ch != '1' and ch != '2') return Error.InvalidTrit;
        if (ch == '2') {
            if (!after_payload) return Error.InvalidTritBoundary;
            after_payload = false;
        } else {
            after_payload = true;
        }
        value = value * 3 + (ch - '0');
        used += 1;
        if (used == 5) {
            out[index] = value;
            index += 1;
            value = 0;
            used = 0;
        }
    }
    if (!after_payload) return Error.InvalidTritBoundary;
    while (used != 0) {
        value = value * 3 + 2;
        used += 1;
        if (used == 5) {
            out[index] = value;
            index += 1;
            value = 0;
            used = 0;
        }
    }
    std.debug.assert(index == out.len);
    // Physical D1..D10 carrier profile, not callable SENS admission.
    try t5.validateCoordinatesPhysical(out);
    return out;
}

/// T5M carry consumes exact 0/1 words separated by `2`, then delegates all
/// physical grouping to the T5M transport. It does not inspect domain meaning.
fn carryT5M(allocator: std.mem.Allocator, source: []const u8) ![]u8 {
    if (source.len == 0 or source.len > t5m.MAX_PHYSICAL_BYTES * 5)
        return Error.InvalidTritBoundary;
    // First pass: validate every character and all word boundaries before
    // allocating a word array. A malformed frame must report its grammar
    // error even when the allocator has no free memory.
    // Invalid characters retain precedence over malformed boundaries.
    var count: usize = 1;
    var start_of_word: usize = 0;
    var malformed_boundary = false;
    for (source, 0..) |ch, i| {
        if (ch == '2') {
            if (i == start_of_word) malformed_boundary = true;
            start_of_word = i + 1;
            count += 1;
        } else if (ch != '0' and ch != '1') {
            return Error.InvalidTrit;
        }
    }
    if (malformed_boundary or start_of_word == source.len)
        return Error.InvalidTritBoundary;

    const words = try allocator.alloc(t5m.Word, count);
    defer allocator.free(words);
    var start: usize = 0;
    var word_index: usize = 0;
    for (source, 0..) |ch, i| {
        if (ch == '2') {
            if (i == start) return Error.InvalidTritBoundary;
            words[word_index] = .{ .width = i - start, .bits = source[start..i] };
            word_index += 1;
            start = i + 1;
        }
    }
    if (start == source.len) return Error.InvalidTritBoundary;
    words[word_index] = .{ .width = source.len - start, .bits = source[start..] };
    return t5m.encode(allocator, words);
}

fn produce(allocator: std.mem.Allocator, command: []const u8, source: []const u8) ![]u8 {
    if (std.mem.eql(u8, command, "t5-carry")) {
        return try carryTrits(allocator, source);
    }
    if (std.mem.eql(u8, command, "t5-roundtrip")) {
        const words = try t5.decode(allocator, source);
        defer allocator.free(words);
        return try t5.encode(allocator, words);
    }
    if (std.mem.eql(u8, command, "t5m-carry")) {
        return try carryT5M(allocator, source);
    }
    if (std.mem.eql(u8, command, "t5m-roundtrip")) {
        var decoded = try t5m.decode(allocator, source);
        defer decoded.deinit(allocator);
        const words = try allocator.alloc(t5m.Word, decoded.words.len);
        defer allocator.free(words);
        for (decoded.words, 0..) |word, i|
            words[i] = .{ .width = word.width, .bits = word.bits };
        return t5m.encode(allocator, words);
    }
    // D10 is a coordinate-only carrier. Decoding it never authorizes execute.
    if (std.mem.eql(u8, command, "t5-coordinates-roundtrip")) {
        const words = try t5.decodeCoordinates(allocator, source);
        defer allocator.free(words);
        return try t5.encodeCoordinates(allocator, words);
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
    if (std.mem.eql(u8, command, "t5m-check")) {
        var decoded = try t5m.decode(allocator, source);
        decoded.deinit(allocator);
        return;
    }
    if (std.mem.eql(u8, command, "t5-coordinates-check")) {
        // Explicit D1..D10 physical-only mode, not an SENS execution preflight.
        try t5.validateCoordinatesPhysical(source);
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
        std.mem.eql(u8, command, "t5m-check") or
        std.mem.eql(u8, command, "t5-coordinates-check") or
        std.mem.eql(u8, command, "f3c-check");
    if (check_only and args.len != 3) return Error.Usage;
    if (!check_only and args.len != 4) return Error.Usage;

    const input_is_t5 =
        std.mem.eql(u8, command, "t5-check") or
        std.mem.eql(u8, command, "t5-roundtrip") or
        std.mem.eql(u8, command, "t5-coordinates-check") or
        std.mem.eql(u8, command, "t5-coordinates-roundtrip") or
        std.mem.eql(u8, command, "f3c-pack");
    const input_is_t5m = std.mem.eql(u8, command, "t5m-check") or
        std.mem.eql(u8, command, "t5m-roundtrip");
    const input_is_f3c = std.mem.eql(u8, command, "f3c-check") or
        std.mem.eql(u8, command, "f3c-unpack");
    const input_is_trits = std.mem.eql(u8, command, "t5-carry");
    if (!input_is_t5 and !input_is_t5m and !input_is_f3c and !input_is_trits and
        !std.mem.eql(u8, command, "t5m-carry")) return Error.Usage;
    try requireExtension(source_path, if (input_is_trits or std.mem.eql(u8, command, "t5m-carry"))
        ".trits"
    else if (input_is_t5 or input_is_t5m) ".sens" else ".senc");

    // The trit stream is not yet packed: at most five source trits fit one
    // physical T5 byte. Do not apply the packed-byte limit to this input.
    const input_max_bytes = if (input_is_trits or std.mem.eql(u8, command, "t5m-carry"))
        t5.MAX_PHYSICAL_BYTES * 5
    else
        t5.MAX_PHYSICAL_BYTES + 1;
    const original = try readFile(allocator, source_path, input_max_bytes);
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
    } else if (std.mem.eql(u8, command, "t5-carry")) {
        const words = try t5.decodeCoordinates(allocator, output);
        defer allocator.free(words);
        const replay = try t5.encodeCoordinates(allocator, words);
        defer allocator.free(replay);
        if (!std.mem.eql(u8, output, replay)) return Error.CanonicalRoundtripMismatch;
    } else if (std.mem.eql(u8, command, "t5m-carry")) {
        var words = try t5m.decode(allocator, output);
        defer words.deinit(allocator);
        const replay_words = try allocator.alloc(t5m.Word, words.words.len);
        defer allocator.free(replay_words);
        for (words.words, 0..) |word, i|
            replay_words[i] = .{ .width = word.width, .bits = word.bits };
        const replay = try t5m.encode(allocator, replay_words);
        defer allocator.free(replay);
        if (!std.mem.eql(u8, output, replay)) return Error.CanonicalRoundtripMismatch;
    } else if (!std.mem.eql(u8, original, output)) {
        return Error.CanonicalRoundtripMismatch;
    }

    // No shared output exists until verification has succeeded.
    // Never unlink the destination on any failure, including a writer race.
    try writeVerifiedNew(allocator, dest_path, output);
}

