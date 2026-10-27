//! Приймання #5767: Zig T5 byte-exact на РЕАЛЬНОМУ корпусі + негативні фікстури.
//! Два списки шляхів (libc, без std.fs/std.io — немає в Zig 0.16):
//!   parity_accept.txt — кожен мусить: decode -> encode == вихідні байти (канонічність);
//!   parity_reject.txt — кожен мусить бути ВІДХИЛЕНИЙ (fail-closed).
//! Не виконує програму і не судить семантику: лише фізичний транспорт.
const std = @import("std");
const t5 = @import("t5/t5.zig");

const CFile = opaque {};
extern "c" fn fopen([*:0]const u8, [*:0]const u8) ?*CFile;
extern "c" fn fclose(*CFile) c_int;
extern "c" fn fseek(*CFile, c_long, c_int) c_int;
extern "c" fn ftell(*CFile) c_long;
extern "c" fn fread([*]u8, usize, usize, *CFile) usize;

fn readFile(allocator: std.mem.Allocator, path: []const u8) ![]u8 {
    const zpath = try allocator.dupeZ(u8, path);
    defer allocator.free(zpath);
    const file = fopen(zpath.ptr, "rb") orelse return error.OpenFailed;
    defer _ = fclose(file);
    if (fseek(file, 0, 2) != 0) return error.SeekFailed;
    const end = ftell(file);
    if (end < 0) return error.SeekFailed;
    if (fseek(file, 0, 0) != 0) return error.SeekFailed;
    const bytes = try allocator.alloc(u8, @intCast(end));
    errdefer allocator.free(bytes);
    if (bytes.len != 0 and fread(bytes.ptr, 1, bytes.len, file) != bytes.len)
        return error.ReadFailed;
    return bytes;
}

/// Дайджести зберігаються як 32 байти, без створення великих hex-буферів.
const Check = struct {
    accepted: bool,
    byte_count: usize,
    fixture_sha256: [32]u8,
    replay_sha256: ?[32]u8 = null,
    first_diff: ?usize = null,
};

fn firstDiff(a: []const u8, b: []const u8) usize {
    const n = @min(a.len, b.len);
    var i: usize = 0;
    while (i < n) : (i += 1) if (a[i] != b[i]) return i;
    return n;
}

/// Неканонічний носій => REJECT; неможливість прочитати fixture => ПОМИЛКА harness.
/// Жодна фізична відмова не перетворюється на семантичний вердикт SENS.
fn accepts(allocator: std.mem.Allocator, path: []const u8) !Check {
    const original = try readFile(allocator, path);
    defer allocator.free(original);
    var fixture_sha: [32]u8 = undefined;
    std.crypto.hash.sha2.Sha256.hash(original, &fixture_sha, .{});
    const rejected = Check{
        .accepted = false,
        .byte_count = original.len,
        .fixture_sha256 = fixture_sha,
    };
    const words = t5.decodeCoordinates(allocator, original) catch |err| switch (err) {
        error.OutOfMemory => return err,
        else => return rejected,
    };
    defer allocator.free(words);
    const re = try t5.encodeCoordinates(allocator, words);
    defer allocator.free(re);
    var replay_sha: [32]u8 = undefined;
    std.crypto.hash.sha2.Sha256.hash(re, &replay_sha, .{});
    const same = std.mem.eql(u8, original, re);
    return .{
        .accepted = same,
        .byte_count = original.len,
        .fixture_sha256 = fixture_sha,
        .replay_sha256 = replay_sha,
        .first_diff = if (same) null else firstDiff(original, re),
    };
}

fn manifestPath(raw: []const u8) []const u8 {
    return if (raw.len != 0 and raw[raw.len - 1] == '\r')
        raw[0 .. raw.len - 1]
    else
        raw;
}

// Explicit comment grammar: "#" or "# " starts a human comment.
// A Git path such as "#law.sens" is a real file, not an implicit comment;
// skipping it would give a false positive for the parity corpus.
fn skipManifestRow(line: []const u8) bool {
    return line.len == 0 or std.mem.eql(u8, line, "#") or
        std.mem.startsWith(u8, line, "# ");
}


/// Duplicate paths are not independent T5 physical witnesses. Preserve
/// literal path bytes, with only the manifest's terminal CR normalized.
fn seenEarlierPath(data: []const u8, before: usize, candidate: []const u8) bool {
    var previous = std.mem.splitScalar(u8, data[0..before], '\n');
    while (previous.next()) |raw| {
        const path = manifestPath(raw);
        if (!skipManifestRow(path) and std.mem.eql(u8, path, candidate))
            return true;
    }
    return false;
}

fn processList(allocator: std.mem.Allocator, list_path: []const u8, expect_accept: bool) !usize {
    const data = try readFile(allocator, list_path);
    defer allocator.free(data);
    var failures: usize = 0;
    var checked: usize = 0;
    var offset: usize = 0;
    var it = std.mem.splitScalar(u8, data, '\n');
    while (it.next()) |raw| {
        const previous_end = offset;
        offset += raw.len;
        if (offset < data.len) offset += 1;
        // Only CRLF's terminal CR is normalized. Never trim legal path bytes.
        const line = manifestPath(raw);
        if (skipManifestRow(line)) continue;
        if (seenEarlierPath(data, previous_end, line)) {
            failures += 1;
            std.debug.print("можливість-розв'язати-цікаву-задачу (fail) test_id=t5-parity-manifest-duplicate layer=transport manifest={s} path={s} byte_offset={d} fixture_sha256=UNAVAILABLE expected=UNIQUE actual=DUPLICATE reproduce='zig build-exe -O ReleaseFast -lc research/zig-codecs/parity_t5.zig && ./parity_t5'\n", .{ list_path, line, previous_end });
            continue;
        }
        checked += 1;
        const check = accepts(allocator, line) catch |err| {
            failures += 1;
            std.debug.print("можливість-розв'язати-цікаву-задачу (fail) test_id=t5-parity-fixture-io layer=transport file={s} fixture_sha256=UNAVAILABLE replay_sha256=UNAVAILABLE first_diff=NA expected={s} actual=HARNESS_ERROR error={s} reproduce='zig build-exe -O ReleaseFast -lc research/zig-codecs/parity_t5.zig && ./parity_t5'\n", .{
                line,
                if (expect_accept) "ACCEPT" else "REJECT",
                @errorName(err),
            });
            continue;
        };
        const fixture_hex = std.fmt.bytesToHex(check.fixture_sha256, .lower);
        if (check.accepted != expect_accept) {
            failures += 1;
            const replay_hex = if (check.replay_sha256) |sha|
                std.fmt.bytesToHex(sha, .lower)
            else
                [_]u8{'-'} ** 64;
            std.debug.print("можливість-розв'язати-цікаву-задачу (fail) test_id=t5-parity layer=transport file={s} bytes={d} fixture_sha256={s} replay_sha256={s} first_diff={any} expected={s} actual={s} reproduce='zig build-exe -O ReleaseFast -lc research/zig-codecs/parity_t5.zig && ./parity_t5'\n", .{
                line,
                check.byte_count,
                &fixture_hex,
                &replay_hex,
                check.first_diff,
                if (expect_accept) "ACCEPT" else "REJECT",
                if (check.accepted) "ACCEPT" else "REJECT",
            });
        } else if (expect_accept) {
            std.debug.print("OK file={s} bytes={d} sha256={s}\n", .{ line, check.byte_count, &fixture_hex });
        }
    }
    if (checked == 0) {
        failures += 1;
        std.debug.print("можливість-розв'язати-цікаву-задачу (fail) test_id=t5-parity-empty-list layer=transport file={s} expected=NONEMPTY actual=EMPTY reproduce='zig run -lc research/zig-codecs/parity_t5.zig'\n", .{list_path});
    }
    std.debug.print("list={s} expect={s} checked={d} failures={d}\n", .{
        list_path, if (expect_accept) "ACCEPT" else "REJECT", checked, failures,
    });
    return failures;
}

pub fn main() !void {
    const allocator = std.heap.page_allocator;
    var total: usize = 0;
    total += try processList(allocator, "parity_accept.txt", true);
    total += try processList(allocator, "parity_reject.txt", false);
    std.debug.print("PARITY_SUMMARY failures={d}\n", .{total});
    if (total != 0) return error.ParityFailed;
}
