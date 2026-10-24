//! Непрозорі байти таблиць людських проєкцій. Zig не визначає їхню семантику.
const std = @import("std");

pub const tables = [_][]const u8{
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

pub fn copy(domain: u8, dst: [*]u8, capacity: usize) isize {
    if (domain == 0 or domain > tables.len) return -1;
    const asset = tables[@as(usize, domain) - 1];
    if (asset.len == 0) return -1;
    if (capacity == 0) return @intCast(asset.len);
    if (capacity < asset.len) return -2;
    @memcpy(dst[0..asset.len], asset);
    return @intCast(asset.len);
}

/// Build-каталог досі споживає десять повних таблиць D1–D10.
/// Це область каталогу проєкцій, а не верхня межа доменів SENS чи T5M.
/// Кожен запис: номер таблиці u8, довжина u32 big-endian, незмінені байти.
pub fn writeBuildTables(output: *std.Io.Writer) !void {
    for (tables[0..10], 1..) |asset, domain| {
        try output.writeByte(@intCast(domain));
        var size: [4]u8 = undefined;
        std.mem.writeInt(u32, &size, @intCast(asset.len), .big);
        try output.writeAll(&size);
        try output.writeAll(asset);
    }
}
