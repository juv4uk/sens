//! Гра «Драбина D13»: виведення, а не ратифікація 2048 селекторів.
//! Джерело істини: чинні 512 рядків lib/domains/d11.lisp, які читає
//! ladder_memory_game.zig. D13 тут є лише дослідним простором кандидатів.
//! Закон: p||ab означає p(s_a(s_b(x))), s_0=CAR, s_1=CDR.
//! Відсутні нові прямі opcode, D13-доменна таблиця і доказ виконання SENS.
//! Не плутати з математичними D12,D24,D48… або транспортним ESC13.

const std = @import("std");
const ladder = @import("ladder_memory_game.zig");

pub const first_word: u16 = 0b0110000000000;
pub const last_word: u16 = 0b1001111111111;
pub const candidate_count: usize = 2048;

pub const Candidate = struct {
    bits: [13]u8,
    lisp: [13]u8,
};

/// Одна точна композиція вже відомого селектора D11 та двох CAR/CDR.
/// Ім'я має 11 літер A/D між C і R; код складається з 11+2 бітів.
pub fn derive(parent: ladder.Record, suffix: u2) ?Candidate {
    if (parent.width != 11 or parent.bits.len != 11 or parent.lisp.len != 11) return null;
    if (parent.lisp[0] != 'C' or parent.lisp[10] != 'R') return null;
    for (parent.bits) |bit| {
        if (bit != '0' and bit != '1') return null;
    }
    for (parent.lisp[1..10]) |letter| {
        if (letter != 'A' and letter != 'D') return null;
    }

    var result: Candidate = undefined;
    std.mem.copyForwards(u8, result.bits[0..11], parent.bits);
    result.bits[11] = if ((suffix & 0b10) == 0) '0' else '1';
    result.bits[12] = if ((suffix & 0b01) == 0) '0' else '1';

    std.mem.copyForwards(u8, result.lisp[0..10], parent.lisp[0..10]);
    result.lisp[10] = if ((suffix & 0b10) == 0) 'A' else 'D';
    result.lisp[11] = if ((suffix & 0b01) == 0) 'A' else 'D';
    result.lisp[12] = 'R';
    return result;
}

/// Індекс 0..2047 відображається на безперервну ділянку D13.
/// Це НЕ дозвіл на використання слова як виконуваного коду SENS.
pub fn candidateAt(index: usize) ?Candidate {
    if (index >= candidate_count) return null;
    const parent = ladder.questionAt(11, index / 4) orelse return null;
    return derive(parent, @intCast(index % 4));
}

pub fn candidateFromWord(word: u16) ?Candidate {
    if (word < first_word or word > last_word) return null;
    return candidateAt(@as(usize, word - first_word));
}

test "Драбина D13: 512 батьків породжують рівно 2048 точних різних координат" {
    try std.testing.expectEqual(@as(usize, 512), ladder.questionCount(11));
    try std.testing.expectEqual(@as(usize, 512), ladder.coordinateCount(11));
    var seen = [_]bool{false} ** 8192;
    for (0..candidate_count) |i| {
        const child = candidateAt(i) orelse return error.MissingCandidate;
        const word = try std.fmt.parseInt(u16, &child.bits, 2);
        try std.testing.expectEqual(first_word + @as(u16, @intCast(i)), word);
        try std.testing.expect(!seen[word]);
        seen[word] = true;
        try std.testing.expectEqual(@as(usize, 13), child.bits.len);
        try std.testing.expectEqual(@as(usize, 13), child.lisp.len);
        const reverse = candidateFromWord(word) orelse return error.MissingReverse;
        try std.testing.expectEqualSlices(u8, &child.bits, &reverse.bits);
        try std.testing.expectEqualSlices(u8, &child.lisp, &reverse.lisp);
    }
    for (first_word..last_word + 1) |word| {
        try std.testing.expect(seen[word]);
    }
}

test "Драбина D13: чотири різні суфікси зберігають порядок CAR/CDR" {
    const parent = ladder.questionAt(11, 0) orelse return error.MissingParent;
    const names = [_][]const u8{ "AA", "AD", "DA", "DD" };
    const tails = [_][]const u8{ "00", "01", "10", "11" };
    for (0..4) |i| {
        const child = derive(parent, @intCast(i)) orelse return error.MissingCandidate;
        try std.testing.expectEqualSlices(u8, parent.bits, child.bits[0..11]);
        try std.testing.expectEqualSlices(u8, tails[i], child.bits[11..13]);
        try std.testing.expectEqualSlices(u8, parent.lisp[0..10], child.lisp[0..10]);
        try std.testing.expectEqualSlices(u8, names[i], child.lisp[10..12]);
        try std.testing.expectEqual(@as(u8, 'R'), child.lisp[12]);
    }
}

test "Драбина D13: чужі та некоректні координати відхиляються" {
    try std.testing.expect(candidateAt(candidate_count) == null);
    try std.testing.expect(candidateFromWord(first_word - 1) == null);
    try std.testing.expect(candidateFromWord(last_word + 1) == null);
    try std.testing.expect(candidateFromWord(0x1fff) == null);
    const invalid_parent = ladder.Record{ .width = 11, .bits = "01100000000", .lisp = "NOTSELECTOR" };
    try std.testing.expect(derive(invalid_parent, 0) == null);
}

pub fn main() !void {
    const first = candidateAt(0) orelse return error.MissingCandidate;
    const last = candidateAt(candidate_count - 1) orelse return error.MissingCandidate;
    std.debug.print(
        "D13_LADDER candidates={d} parents=512 first_bits={s} first_name={s} last_bits={s} last_name={s} semantic_status=UNRATIFIED transport=NONE\n",
        .{ candidate_count, first.bits[0..], first.lisp[0..], last.bits[0..], last.lisp[0..] },
    );
}
