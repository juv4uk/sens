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

fn hexInto(out: []u8, bytes: []const u8) []u8 {
    const digits = "0123456789abcdef";
    for (bytes, 0..) |b, i| {
        out[i * 2] = digits[b >> 4];
        out[i * 2 + 1] = digits[b & 0xf];
    }
    return out[0 .. bytes.len * 2];
}

fn firstDiff(a: []const u8, b: []const u8) usize {
    const n = @min(a.len, b.len);
    var i: usize = 0;
    while (i < n) : (i += 1) if (a[i] != b[i]) return i;
    return n;
}

/// Повертає true, якщо файл канонічний (decode->encode == байти).
fn accepts(allocator: std.mem.Allocator, path: []const u8, detail: *bool) !bool {
    const original = readFile(allocator, path) catch { detail.* = false; return false; };
    defer allocator.free(original);
    const words = t5.decode(allocator, original) catch { detail.* = false; return false; };
    defer allocator.free(words);
    const re = t5.encode(allocator, words) catch { detail.* = false; return false; };
    defer allocator.free(re);
    if (!std.mem.eql(u8, original, re)) {
        detail.* = false;
        return false;
    }
    detail.* = true;
    return true;
}

fn processList(allocator: std.mem.Allocator, list_path: []const u8, expect_accept: bool) !usize {
    const data = try readFile(allocator, list_path);
    defer allocator.free(data);
    var failures: usize = 0;
    var checked: usize = 0;
    var it = std.mem.splitScalar(u8, data, '\n');
    while (it.next()) |raw| {
        const line = std.mem.trim(u8, raw, " \t\r");
        if (line.len == 0 or line[0] == '#') continue;
        checked += 1;
        var ok = false;
        const got = accepts(allocator, line, &ok) catch false;
        if (got != expect_accept) {
            failures += 1;
            std.debug.print("FAIL test_id=t5-parity layer=transport file={s} expected={s} actual={s} reproduce='zig run parity_t5.zig'\n", .{
                line,
                if (expect_accept) "ACCEPT" else "REJECT",
                if (got) "ACCEPT" else "REJECT",
            });
        } else if (expect_accept) {
            const original = try readFile(allocator, line);
            defer allocator.free(original);
            var hbuf: [8192]u8 = undefined;
            std.debug.print("OK file={s} bytes={d} sha_hex={s}\n", .{ line, original.len, hexInto(&hbuf, original) });
        }
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
