//! Драбина D13 · дослід 13-бітних селекторних кандидатів.
//! НЕ ратифікований домен, НЕ опкоди, НЕ доказ семантики SENS.
//! Джерело батьків — чинна Lisp-таблиця D11 через ladder_memory_game.zig.
//! Закон-кандидат: p_ab(x) = p(s_a(s_b(x))), s_0=CAR, s_1=CDR.
//! Два біти дописуються до 11-бітного коду батька в порядку a,b.
//! D12 є математичним доменом, ESC13 — окремим фізичним дослідом.

const std = @import("std");
const ladder = @import("ladder_memory_game.zig");

pub const Candidate = struct {
    bits: [13]u8,
    lisp: [13]u8,
};

pub fn candidateCount() usize {
    return ladder.questionCount(11) * 4;
}

/// Механічна пропозиція координати, без реєстрації в lib/domains/d13.lisp.
pub fn candidateAt(index: usize) ?Candidate {
    if (index >= candidateCount()) return null;
    const parent = ladder.questionAt(11, index / 4) orelse return null;
    if (parent.bits.len != 11 or parent.lisp.len != 11) return null;
    if (parent.lisp[0] != 'C' or parent.lisp[10] != 'R') return null;
    for (parent.lisp[1..10]) |letter| {
        if (letter != 'A' and letter != 'D') return null;
    }

    const suffix = index % 4;
    const a: u8 = if (suffix < 2) '0' else '1';
    const b: u8 = if (suffix % 2 == 0) '0' else '1';

    var bits: [13]u8 = undefined;
    for (0..11) |i| bits[i] = parent.bits[i];
    bits[11] = a;
    bits[12] = b;

    var lisp: [13]u8 = undefined;
    for (0..10) |i| lisp[i] = parent.lisp[i];
    lisp[10] = if (a == '0') 'A' else 'D';
    lisp[11] = if (b == '0') 'A' else 'D';
    lisp[12] = 'R';
    return .{ .bits = bits, .lisp = lisp };
}

test "D13 research: four exact suffix vectors from first D11 selector" {
    const expected_bits = [_][]const u8{
        "0110000000000",
        "0110000000001",
        "0110000000010",
        "0110000000011",
    };
    const expected_lisp = [_][]const u8{
        "CDAAAAAAAAAAR",
        "CDAAAAAAAAADR",
        "CDAAAAAAAADAR",
        "CDAAAAAAAADDR",
    };
    for (0..4) |i| {
        const candidate = candidateAt(i) orelse return error.MissingCandidate;
        try std.testing.expectEqualSlices(u8, expected_bits[i], &candidate.bits);
        try std.testing.expectEqualSlices(u8, expected_lisp[i], &candidate.lisp);
    }
}

test "D13 research: exactly 2048 unique 13-bit proposals, not opcodes" {
    try std.testing.expectEqual(@as(usize, 512), ladder.questionCount(11));
    try std.testing.expectEqual(@as(usize, 2048), candidateCount());
    var seen = [_]bool{false} ** (1 << 13);
    for (0..candidateCount()) |i| {
        const candidate = candidateAt(i) orelse return error.MissingCandidate;
        var coordinate: usize = 0;
        for (candidate.bits) |digit| {
            try std.testing.expect(digit == '0' or digit == '1');
            coordinate = (coordinate << 1) | @as(usize, if (digit == '1') 1 else 0);
        }
        try std.testing.expect(!seen[coordinate]);
        seen[coordinate] = true;
    }
    try std.testing.expect(candidateAt(candidateCount()) == null);
}

test "D13 research: suffix 01 is not suffix 10" {
    const ab = candidateAt(1) orelse return error.MissingCandidate;
    const ba = candidateAt(2) orelse return error.MissingCandidate;
    try std.testing.expect(!std.mem.eql(u8, &ab.bits, &ba.bits));
    try std.testing.expect(!std.mem.eql(u8, &ab.lisp, &ba.lisp));
}
