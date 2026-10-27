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
    // Доведена селекторна чверть: лише корені D3 CDR=011 та CAR=100.
    // Біти суфікса не просто синтаксис: 0=A/CAR, 1=D/CDR.
    const root_letter: u8 = if (std.mem.eql(u8, parent.bits[0..3], "011"))
        'D'
    else if (std.mem.eql(u8, parent.bits[0..3], "100"))
        'A'
    else
        return null;
    if (parent.lisp[0] != 'C' or parent.lisp[1] != root_letter or parent.lisp[10] != 'R') return null;
    for (parent.bits[3..], 0..) |bit, index| {
        const expected_letter: u8 = switch (bit) {
            '0' => 'A',
            '1' => 'D',
            else => return null,
        };
        if (parent.lisp[index + 2] != expected_letter) return null;
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

/// Точна координата D11-батька визначається старшими 11 бітами D13.
/// Порядок рядків таблиці не є частиною тотожності функції.
fn parentBitsFromWord(word: u16) ?[11]u8 {
    if (word < first_word or word > last_word) return null;
    const parent_word = word >> 2;
    var bits: [11]u8 = undefined;
    for (0..bits.len) |i| {
        const shift: u4 = @intCast(10 - i);
        bits[i] = if (((parent_word >> shift) & 1) == 0) '0' else '1';
    }
    return bits;
}

/// Індекс 0..2047 відображається на безперервну ділянку D13.
/// Це НЕ дозвіл на використання слова як виконуваного коду SENS.
pub fn candidateAt(index: usize) ?Candidate {
    if (index >= candidate_count) return null;
    return candidateFromWord(first_word + @as(u16, @intCast(index)));
}

pub fn candidateFromWord(word: u16) ?Candidate {
    const parent_bits = parentBitsFromWord(word) orelse return null;
    const parent = ladder.lookup(11, &parent_bits) orelse return null;
    return derive(parent, @intCast(word & 0b11));
}


pub fn main() !void {
    const first = candidateAt(0) orelse return error.MissingCandidate;
    const last = candidateAt(candidate_count - 1) orelse return error.MissingCandidate;
    std.debug.print(
        "D13_LADDER candidates={d} parents=512 first_bits={s} first_name={s} last_bits={s} last_name={s} semantic_status=UNRATIFIED transport=NONE\n",
        .{ candidate_count, first.bits[0..], first.lisp[0..], last.bits[0..], last.lisp[0..] },
    );
}
