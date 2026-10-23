//! Гра «Драбина»: перевірка пам'яті машинних координат за чинними таблицями.
//! Це гра знання інвентарю, НЕ оракул виконуваності функцій SENS.
//! Джерело істини одне: lib/domains/d1.lisp … d11.lisp.
//! D7 — клавіатурні дані; D11 — робоче похідне розширення.
const std = @import("std");

pub const Record = struct {
    width: u8,
    bits: []const u8,
    lisp: []const u8,
};

pub const Guess = struct {
    width: u8,
    bits: []const u8,
    lisp: []const u8,
};

pub const Score = struct {
    correct: usize = 0,
    wrong: usize = 0,
    duplicate: usize = 0,
    unknown: usize = 0,
    structural: usize = 0,
};

// Не дублюємо реєстр у Zig: кожна відповідь читається з канонічного Lisp.
fn source(width: u8) ?[]const u8 {
    return switch (width) {
        1 => @embedFile("../../lib/domains/d1.lisp"),
        2 => @embedFile("../../lib/domains/d2.lisp"),
        3 => @embedFile("../../lib/domains/d3.lisp"),
        4 => @embedFile("../../lib/domains/d4.lisp"),
        5 => @embedFile("../../lib/domains/d5.lisp"),
        6 => @embedFile("../../lib/domains/d6.lisp"),
        7 => @embedFile("../../lib/domains/d7.lisp"),
        8 => @embedFile("../../lib/domains/d8.lisp"),
        9 => @embedFile("../../lib/domains/d9.lisp"),
        10 => @embedFile("../../lib/domains/d10.lisp"),
        11 => @embedFile("../../lib/domains/d11.lisp"),
        else => null,
    };
}

// Читаємо лише точну координату та колонку LISP, без інтерпретації семантики.
fn parseRow(width: u8, line: []const u8) ?Record {
    const n: usize = @intCast(width);
    const row = std.mem.trimStart(u8, line, " \t");
    if (row.len < n + 3 or row[0] != '(' or row[n + 1] != ' ') return null;
    const bits = row[1 .. n + 1];
    for (bits) |digit| {
        if (digit != '0' and digit != '1') return null;
    }
    const marker = "(LISP ";
    const marker_at = std.mem.indexOf(u8, row, marker) orelse return null;
    const value = row[marker_at + marker.len ..];
    if (std.mem.startsWith(u8, value, "()")) {
        return .{ .width = width, .bits = bits, .lisp = "()" };
    }
    const end = std.mem.indexOfScalar(u8, value, ')') orelse return null;
    if (end == 0) return null;
    return .{ .width = width, .bits = bits, .lisp = value[0..end] };
}

pub fn lookup(width: u8, bits: []const u8) ?Record {
    if (bits.len != @as(usize, width)) return null;
    const table = source(width) orelse return null;
    var lines = std.mem.splitScalar(u8, table, '\n');
    while (lines.next()) |line| {
        const row = parseRow(width, line) orelse continue;
        if (std.mem.eql(u8, row.bits, bits)) return row;
    }
    return null;
}

// Завданням конкурсу є пригадати назву та код. Порожня LISP-поверхня
// є структурою/даними, а не «забутою функцією».
pub fn questionAt(width: u8, index: usize) ?Record {
    const table = source(width) orelse return null;
    var lines = std.mem.splitScalar(u8, table, '\n');
    var seen: usize = 0;
    while (lines.next()) |line| {
        const row = parseRow(width, line) orelse continue;
        if (std.mem.eql(u8, row.lisp, "()")) continue;
        if (seen == index) return row;
        seen += 1;
    }
    return null;
}

pub fn questionCount(width: u8) usize {
    const table = source(width) orelse return 0;
    var lines = std.mem.splitScalar(u8, table, '\n');
    var count: usize = 0;
    while (lines.next()) |line| {
        const row = parseRow(width, line) orelse continue;
        if (!std.mem.eql(u8, row.lisp, "()")) count += 1;
    }
    return count;
}

pub fn coordinateCount(width: u8) usize {
    const table = source(width) orelse return 0;
    var lines = std.mem.splitScalar(u8, table, '\n');
    var count: usize = 0;
    while (lines.next()) |line| {
        if (parseRow(width, line) != null) count += 1;
    }
    return count;
}

pub fn grade(guesses: []const Guess) Score {
    var result: Score = .{};
    for (guesses, 0..) |guess, index| {
        var repeated = false;
        for (guesses[0..index]) |previous| {
            if (previous.width == guess.width and std.mem.eql(u8, previous.bits, guess.bits)) {
                repeated = true;
                break;
            }
        }
        if (repeated) {
            result.duplicate += 1;
            continue;
        }
        const actual = lookup(guess.width, guess.bits) orelse {
            result.unknown += 1;
            continue;
        };
        if (std.mem.eql(u8, actual.lisp, "()")) {
            result.structural += 1;
        } else if (std.ascii.eqlIgnoreCase(actual.lisp, guess.lisp)) {
            result.correct += 1;
        } else {
            result.wrong += 1;
        }
    }
    return result;
}

test "Драбина: усі D1–D10 мають точні двійкові координати" {
    var width: u8 = 1;
    while (width <= 10) : (width += 1) {
        const shift: u6 = @intCast(width);
        const expected = @as(usize, 1) << shift;
        try std.testing.expectEqual(expected, coordinateCount(width));
    }
}

test "Драбина: D7 не є функціями, D11 позначений як робоче розширення" {
    try std.testing.expectEqual(@as(usize, 0), questionCount(7));
    try std.testing.expect(questionCount(11) > 0);
    try std.testing.expectEqualStrings("CDAAAAAAAAR", lookup(11, "01100000000").?.lisp);
}

test "Драбина: іменні раунди D3–D5 мають 7, 16 і 32 запитання" {
    try std.testing.expectEqual(@as(usize, 7), questionCount(3));
    try std.testing.expectEqual(@as(usize, 16), questionCount(4));
    try std.testing.expectEqual(@as(usize, 32), questionCount(5));
    try std.testing.expectEqualStrings("QUOTE", questionAt(3, 0).?.lisp);
    try std.testing.expectEqualStrings("APPLY", questionAt(4, 0).?.lisp);
    try std.testing.expectEqualStrings("EVALQUOTE", questionAt(5, 0).?.lisp);
    try std.testing.expect(std.mem.indexOf(u8, source(2).?, "(11 (ук крапка)") != null);
    try std.testing.expectEqualStrings("()", lookup(2, "11").?.lisp);
}

test "Драбина: точні коди, хибні назви, повтори і незайняті координати" {
    const answers = [_]Guess{
        .{ .width = 3, .bits = "001", .lisp = "quote" },
        .{ .width = 3, .bits = "001", .lisp = "CAR" },
        .{ .width = 3, .bits = "100", .lisp = "CDR" },
        .{ .width = 4, .bits = "0000", .lisp = "APPLY" },
        .{ .width = 2, .bits = "11", .lisp = "()" },
        .{ .width = 3, .bits = "1110", .lisp = "CONS" },
    };
    const result = grade(&answers);
    try std.testing.expectEqual(@as(usize, 2), result.correct);
    try std.testing.expectEqual(@as(usize, 1), result.wrong);
    try std.testing.expectEqual(@as(usize, 1), result.duplicate);
    try std.testing.expectEqual(@as(usize, 1), result.unknown);
    try std.testing.expectEqual(@as(usize, 1), result.structural);
}
