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
    answered: usize = 0,
    missing: usize = 0,
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

/// Відтворювана перестановка запитань для чесного раунду.
/// Один seed дає той самий порядок; усі індекси з'являються рівно один раз.
/// Це механіка гри: назви й координати як і раніше читаються з Lisp-таблиць.
pub fn questionOrder(allocator: std.mem.Allocator, width: u8, seed: u64) ![]usize {
    const count = questionCount(width);
    const order = try allocator.alloc(usize, count);
    for (order, 0..) |*index, i| index.* = i;

    var state = if (seed == 0) @as(u64, 0x9e3779b97f4a7c15) else seed;
    var i = count;
    while (i > 1) {
        i -= 1;
        state ^= state << 13;
        state ^= state >> 7;
        state ^= state << 17;
        const j: usize = @intCast(state % @as(u64, @intCast(i + 1)));
        std.mem.swap(usize, &order[i], &order[j]);
    }
    return order;
}

/// Оцінює повноту одного доменного раунду, окрім точності кожної відповіді.
/// Невідомі координати й структурні записи не зараховуються як пригадані функції.
pub fn gradeDomain(width: u8, guesses: []const Guess) Score {
    var result = grade(guesses);
    var answered: usize = 0;
    for (guesses, 0..) |guess, index| {
        if (guess.width != width) continue;
        var repeated = false;
        for (guesses[0..index]) |previous| {
            if (previous.width == guess.width and std.mem.eql(u8, previous.bits, guess.bits)) {
                repeated = true;
                break;
            }
        }
        if (repeated) continue;
        const actual = lookup(guess.width, guess.bits) orelse continue;
        if (!std.mem.eql(u8, actual.lisp, "()")) answered += 1;
    }
    result.answered = answered;
    const total = questionCount(width);
    result.missing = if (total > answered) total - answered else 0;
    return result;
}

test "Драбина D11: раунд має 512 унікальних відтворюваних запитань і повний підрахунок" {
    const allocator = std.testing.allocator;
    try std.testing.expectEqual(@as(usize, 512), questionCount(11));
    try std.testing.expectEqual(@as(usize, 512), coordinateCount(11));

    const order = try questionOrder(allocator, 11, 0x53454e534c414444);
    defer allocator.free(order);
    const replay = try questionOrder(allocator, 11, 0x53454e534c414444);
    defer allocator.free(replay);
    try std.testing.expectEqualSlices(usize, order, replay);
    try std.testing.expectEqual(@as(usize, 512), order.len);

    var seen = [_]bool{false} ** 512;
    var guesses = try allocator.alloc(Guess, order.len);
    defer allocator.free(guesses);
    for (order, 0..) |question_index, i| {
        try std.testing.expect(question_index < seen.len);
        try std.testing.expect(!seen[question_index]);
        seen[question_index] = true;
        const record = questionAt(11, question_index) orelse return error.MissingQuestion;
        guesses[i] = .{ .width = record.width, .bits = record.bits, .lisp = record.lisp };
    }
    for (seen) |found| try std.testing.expect(found);

    const result = gradeDomain(11, guesses);
    try std.testing.expectEqual(@as(usize, 512), result.correct);
    try std.testing.expectEqual(@as(usize, 512), result.answered);
    try std.testing.expectEqual(@as(usize, 0), result.missing);
    try std.testing.expectEqual(@as(usize, 0), result.wrong);
    try std.testing.expectEqual(@as(usize, 0), result.duplicate);
    try std.testing.expectEqual(@as(usize, 0), result.unknown);
}

test "Драбина D11: прогалина, хибна відповідь і повтор не зараховуються як нові функції" {
    const first = questionAt(11, 0) orelse return error.MissingQuestion;
    const guesses = [_]Guess{
        .{ .width = 11, .bits = first.bits, .lisp = first.lisp },
        .{ .width = 11, .bits = first.bits, .lisp = "НЕПРАВИЛЬНА-НАЗВА" },
        .{ .width = 11, .bits = "00000000000", .lisp = "UNKNOWN" },
    };
    const result = gradeDomain(11, &guesses);
    try std.testing.expectEqual(@as(usize, 1), result.correct);
    try std.testing.expectEqual(@as(usize, 1), result.duplicate);
    try std.testing.expectEqual(@as(usize, 1), result.unknown);
    try std.testing.expectEqual(@as(usize, 1), result.answered);
    try std.testing.expectEqual(@as(usize, 511), result.missing);
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
