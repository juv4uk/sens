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

// Не дублюємо реєстр у Zig: читаємо чинні Lisp-файли з кореня checkout.
// Zig 0.16 не дозволяє вбудовувати файл поза коренем пакета.
// Таблиці тримаємо в пам'яті до завершення процесу: Record повертає їхні зрізи.
const CFile = opaque {};
extern "c" fn fopen([*:0]const u8, [*:0]const u8) ?*CFile;
extern "c" fn fclose(*CFile) c_int;
extern "c" fn fseek(*CFile, c_long, c_int) c_int;
extern "c" fn ftell(*CFile) c_long;
extern "c" fn fread([*]u8, usize, usize, *CFile) usize;

var table_cache = [_]?[]u8{null} ** 11;

fn source(width: u8) ?[]const u8 {
    const path: [*:0]const u8 = switch (width) {
        1 => "lib/domains/d1.lisp",
        2 => "lib/domains/d2.lisp",
        3 => "lib/domains/d3.lisp",
        4 => "lib/domains/d4.lisp",
        5 => "lib/domains/d5.lisp",
        6 => "lib/domains/d6.lisp",
        7 => "lib/domains/d7.lisp",
        8 => "lib/domains/d8.lisp",
        9 => "lib/domains/d9.lisp",
        10 => "lib/domains/d10.lisp",
        11 => "lib/domains/d11.lisp",
        else => return null,
    };
    const index = @as(usize, width) - 1;
    if (table_cache[index]) |bytes| return bytes;

    const file = fopen(path, "rb") orelse return null;
    defer _ = fclose(file);
    if (fseek(file, 0, 2) != 0) return null;
    const raw_len = ftell(file);
    if (raw_len <= 0 or fseek(file, 0, 0) != 0) return null;
    const len: usize = @intCast(raw_len);
    const bytes = std.heap.page_allocator.alloc(u8, len) catch return null;
    if (fread(bytes.ptr, 1, len, file) != len) {
        std.heap.page_allocator.free(bytes);
        return null;
    }
    table_cache[index] = bytes;
    return bytes;
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

fn gradeFiltered(guesses: []const Guess, domain: ?u8) Score {
    var result: Score = .{};
    for (guesses, 0..) |guess, index| {
        if (domain) |width| {
            if (guess.width != width) continue;
        }
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

pub fn grade(guesses: []const Guess) Score {
    return gradeFiltered(guesses, null);
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
    var result = gradeFiltered(guesses, width);
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
        if (!std.mem.eql(u8, actual.lisp, "()") and std.ascii.eqlIgnoreCase(actual.lisp, guess.lisp)) answered += 1;
    }
    result.answered = answered;
    const total = questionCount(width);
    result.missing = if (total > answered) total - answered else 0;
    return result;
}

