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
    invalid_suffix: usize = 0,
    non_selector: usize = 0,
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
// Індекс — лише механіка пошуку у вже прочитаних Lisp-таблицях.
// Record зберігає зрізи тих самих джерельних байтів: нової семантики немає.
var coordinate_index_cache = [_]?[]?Record{null} ** 11;
// Підрахунок походить із тих самих незмінних таблиць, один раз за процес.
var question_count_cache = [_]?usize{null} ** 11;

fn bitCoordinate(bits: []const u8) ?usize {
    var coordinate: usize = 0;
    for (bits) |digit| {
        if (digit != '0' and digit != '1') return null;
        coordinate = (coordinate << 1) | @as(usize, digit - '0');
    }
    return coordinate;
}

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

pub const D11Guess = struct {
    parent_bits: []const u8,
    suffix: u8,
    child_lisp: []const u8,
};

fn isD10Selector(name: []const u8) bool {
    if (name.len != 10 or name[0] != 'C' or name[9] != 'R') return false;
    for (name[1..9]) |letter| {
        if (letter != 'A' and letter != 'D') return false;
    }
    return true;
}

/// Раунд D11: учасник пригадує похідний селектор за точним D10-батьком.
/// Це перевірка таблиці та композиційної координати, не допуск до SENS.
pub fn gradeD11(guesses: []const D11Guess) Score {
    var result: Score = .{};
    for (guesses, 0..) |guess, index| {
        var repeated = false;
        for (guesses[0..index]) |previous| {
            if (previous.suffix == guess.suffix and
                std.mem.eql(u8, previous.parent_bits, guess.parent_bits))
            {
                repeated = true;
                break;
            }
        }
        if (repeated) {
            result.duplicate += 1;
            continue;
        }
        if (guess.parent_bits.len != 10) {
            result.unknown += 1;
            continue;
        }
        if (guess.suffix != '0' and guess.suffix != '1') {
            result.invalid_suffix += 1;
            continue;
        }
        const parent = lookup(10, guess.parent_bits) orelse {
            result.unknown += 1;
            continue;
        };
        if (!isD10Selector(parent.lisp)) {
            result.non_selector += 1;
            continue;
        }
        var bits: [11]u8 = undefined;
        @memcpy(bits[0..10], guess.parent_bits);
        bits[10] = guess.suffix;
        const child = lookup(11, &bits) orelse {
            result.unknown += 1;
            continue;
        };
        if (std.ascii.eqlIgnoreCase(child.lisp, guess.child_lisp)) {
            result.correct += 1;
        } else {
            result.wrong += 1;
        }
    }
    result.answered = result.correct;
    const total = questionCount(11);
    result.missing = if (total > result.correct) total - result.correct else 0;
    return result;
}

fn coordinateIndex(width: u8) ?[]?Record {
    if (width == 0 or width > 11) return null;
    const domain_index = @as(usize, width) - 1;
    if (coordinate_index_cache[domain_index]) |records| return records;

    const table = source(width) orelse return null;
    const shift: u6 = @intCast(width);
    const capacity = @as(usize, 1) << shift;
    const records = std.heap.page_allocator.alloc(?Record, capacity) catch return null;
    @memset(records, null);
    var lines = std.mem.splitScalar(u8, table, '\n');
    while (lines.next()) |line| {
        const row = parseRow(width, line) orelse continue;
        const coordinate = bitCoordinate(row.bits) orelse continue;
        // Як і послідовний пошук, повертаємо перший запис координати.
        if (records[coordinate] == null) records[coordinate] = row;
    }
    coordinate_index_cache[domain_index] = records;
    return records;
}

pub fn lookup(width: u8, bits: []const u8) ?Record {
    if (bits.len != @as(usize, width)) return null;
    const coordinate = bitCoordinate(bits) orelse return null;
    const records = coordinateIndex(width) orelse return null;
    return records[coordinate];
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
    if (width == 0 or width > 11) return 0;
    const index = @as(usize, width) - 1;
    if (question_count_cache[index]) |cached| return cached;
    const table = source(width) orelse return 0;
    var lines = std.mem.splitScalar(u8, table, '\n');
    var count: usize = 0;
    while (lines.next()) |line| {
        const row = parseRow(width, line) orelse continue;
        if (!std.mem.eql(u8, row.lisp, "()")) count += 1;
    }
    question_count_cache[index] = count;
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

test "Драбина: кеш кількості питань зберігає відповідність Lisp-таблицям" {
    var width: u8 = 1;
    while (width <= 11) : (width += 1) {
        const table = source(width) orelse return error.MissingDomainTable;
        var lines = std.mem.splitScalar(u8, table, '\n');
        var expected: usize = 0;
        while (lines.next()) |line| {
            const row = parseRow(width, line) orelse continue;
            if (!std.mem.eql(u8, row.lisp, "()")) expected += 1;
        }
        try std.testing.expectEqual(expected, questionCount(width));
        try std.testing.expectEqual(expected, questionCount(width));
    }
    try std.testing.expectEqual(@as(usize, 0), questionCount(0));
    try std.testing.expectEqual(@as(usize, 0), questionCount(12));
}

test "Драбина: індекс зберігає кожен запис і відкидає не-двійковий код" {
    var width: u8 = 1;
    while (width <= 11) : (width += 1) {
        const table = source(width) orelse return error.MissingDomainTable;
        var lines = std.mem.splitScalar(u8, table, '\n');
        while (lines.next()) |line| {
            const row = parseRow(width, line) orelse continue;
            const indexed = lookup(width, row.bits) orelse return error.MissingIndexedRecord;
            try std.testing.expectEqualStrings(row.lisp, indexed.lisp);
            try std.testing.expectEqualStrings(row.bits, indexed.bits);
        }
    }
    try std.testing.expect(lookup(11, "0110000000x") == null);
    try std.testing.expect(lookup(11, "0110000000") == null);
    try std.testing.expect(lookup(12, "011000000000") == null);
}

test "Драбина D11: правильний код з хибною назвою не означає пригадану функцію" {
    const first = questionAt(11, 0) orelse return error.MissingQuestion;
    const guesses = [_]Guess{
        .{ .width = 11, .bits = first.bits, .lisp = "WRONGSELECTOR" },
    };
    const result = gradeDomain(11, &guesses);
    try std.testing.expectEqual(@as(usize, 0), result.correct);
    try std.testing.expectEqual(@as(usize, 1), result.wrong);
    try std.testing.expectEqual(@as(usize, 0), result.answered);
    try std.testing.expectEqual(@as(usize, 512), result.missing);
}

test "Драбина D11: чужі домени не впливають на оцінку раунду" {
    const first = questionAt(11, 0) orelse return error.MissingQuestion;
    const guesses = [_]Guess{
        .{ .width = 11, .bits = first.bits, .lisp = first.lisp },
        .{ .width = 3, .bits = "100", .lisp = "CDR" },
        .{ .width = 3, .bits = "100", .lisp = "CDR" },
        .{ .width = 3, .bits = "1110", .lisp = "CONS" },
        .{ .width = 2, .bits = "11", .lisp = "()" },
    };
    const result = gradeDomain(11, &guesses);
    try std.testing.expectEqual(@as(usize, 1), result.correct);
    try std.testing.expectEqual(@as(usize, 0), result.wrong);
    try std.testing.expectEqual(@as(usize, 0), result.duplicate);
    try std.testing.expectEqual(@as(usize, 0), result.unknown);
    try std.testing.expectEqual(@as(usize, 0), result.structural);
    try std.testing.expectEqual(@as(usize, 1), result.answered);
    try std.testing.expectEqual(@as(usize, 511), result.missing);
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

test "Драбина: точний породжувальний закон центральної чверті селекторів" {
    // D7 є текстом; D12 є математикою. Не виводимо з геометрії допуск D13.
    const widths = [_]u8{ 3, 4, 5, 6, 8, 9, 10, 11 };
    for (widths) |width| {
        const shift: u6 = @intCast(width - 3);
        const quarter: usize = @as(usize, 1) << shift;
        const expected: usize = 2 * quarter;
        const first: usize = 3 * quarter;
        const last_exclusive: usize = first + expected;
        var seen = [_]bool{false} ** 512;
        var selector_count: usize = 0;

        const table = source(width) orelse return error.MissingDomainTable;
        var lines = std.mem.splitScalar(u8, table, '\n');
        while (lines.next()) |line| {
            const row = parseRow(width, line) orelse continue;
            const word = try std.fmt.parseInt(usize, row.bits, 2);
            const in_quarter = word >= first and word < last_exclusive;

            var is_selector = row.lisp.len == @as(usize, width);
            if (is_selector) {
                is_selector = row.lisp[0] == 'C' and row.lisp[row.lisp.len - 1] == 'R';
                if (is_selector) {
                    for (row.lisp[1 .. row.lisp.len - 1]) |letter| {
                        if (letter != 'A' and letter != 'D') {
                            is_selector = false;
                            break;
                        }
                    }
                }
            }
            // Жоден не-селектор не може займати середню чверть.
            // Жоден селектор не може жити поза нею.
            try std.testing.expectEqual(in_quarter, is_selector);
            if (!is_selector) continue;

            const index = word - first;
            try std.testing.expect(!seen[index]);
            seen[index] = true;
            selector_count += 1;

            // D3-корені: 011=CDR, 100=CAR.
            const root: u8 = if (std.mem.eql(u8, row.bits[0..3], "011"))
                'D'
            else if (std.mem.eql(u8, row.bits[0..3], "100"))
                'A'
            else
                return error.ForeignSelectorRoot;
            try std.testing.expectEqual(root, row.lisp[1]);

            // Кожен наступний 0 означає A/CAR, 1 означає D/CDR.
            for (row.bits[3..], 0..) |bit, index_in_tail| {
                const expected_letter: u8 = if (bit == '0') 'A' else if (bit == '1') 'D' else return error.InvalidSelectorBit;
                try std.testing.expectEqual(expected_letter, row.lisp[index_in_tail + 2]);
            }
        }

        try std.testing.expectEqual(expected, selector_count);
        for (seen[0..expected]) |present| try std.testing.expect(present);
    }
}

test "Драбина D11: 512 унікальних похідних точно виконують закон суфікса" {
    try std.testing.expectEqual(@as(usize, 512), questionCount(11));
    var seen = [_]bool{false} ** 2048;
    for (0..questionCount(11)) |i| {
        const child = questionAt(11, i).?;
        const parent = lookup(10, child.bits[0..10]).?;
        try std.testing.expect(isD10Selector(parent.lisp));
        try std.testing.expect(child.bits[10] == '0' or child.bits[10] == '1');
        var coordinate: usize = 0;
        for (child.bits) |digit| coordinate = (coordinate << 1) | @as(usize, digit - '0');
        try std.testing.expect(!seen[coordinate]);
        seen[coordinate] = true;
        var expected: [11]u8 = undefined;
        @memcpy(expected[0..9], parent.lisp[0..9]);
        expected[9] = if (child.bits[10] == '0') 'A' else 'D';
        expected[10] = 'R';
        try std.testing.expectEqualStrings(&expected, child.lisp);
        var sibling_bits: [11]u8 = undefined;
        @memcpy(sibling_bits[0..], child.bits);
        sibling_bits[10] = if (child.bits[10] == '0') '1' else '0';
        try std.testing.expect(lookup(11, &sibling_bits) != null);
    }
}

test "Конкурс D11: вірна назва, хибна, повтор, не-селектор і зіпсований суфікс" {
    const guesses = [_]D11Guess{
        .{ .parent_bits = "0110000000", .suffix = '0', .child_lisp = "cdaaaaaaaar" },
        .{ .parent_bits = "0110000000", .suffix = '0', .child_lisp = "WRONG" },
        .{ .parent_bits = "0110000000", .suffix = '1', .child_lisp = "WRONG" },
        .{ .parent_bits = "0110000000", .suffix = '2', .child_lisp = "CDAAAAAAAAR" },
        .{ .parent_bits = "0000000000", .suffix = '0', .child_lisp = "CDAAAAAAAAR" },
    };
    const score = gradeD11(&guesses);
    try std.testing.expectEqual(@as(usize, 1), score.correct);
    try std.testing.expectEqual(@as(usize, 1), score.wrong);
    try std.testing.expectEqual(@as(usize, 1), score.duplicate);
    try std.testing.expectEqual(@as(usize, 0), score.unknown);
    try std.testing.expectEqual(@as(usize, 1), score.invalid_suffix);
    try std.testing.expectEqual(@as(usize, 1), score.non_selector);
    try std.testing.expectEqual(@as(usize, 1), score.answered);
    try std.testing.expectEqual(@as(usize, 511), score.missing);
}

test "Конкурс D11: обидва суфікси та повтор зіпсованої відповіді" {
    const guesses = [_]D11Guess{
        .{ .parent_bits = "0110000000", .suffix = '0', .child_lisp = "CDAAAAAAAAR" },
        .{ .parent_bits = "0110000000", .suffix = '1', .child_lisp = "CDAAAAAAADR" },
        .{ .parent_bits = "0110000000", .suffix = '2', .child_lisp = "WRONG" },
        .{ .parent_bits = "0110000000", .suffix = '2', .child_lisp = "WRONG" },
    };
    const score = gradeD11(&guesses);
    try std.testing.expectEqual(@as(usize, 2), score.correct);
    try std.testing.expectEqual(@as(usize, 1), score.duplicate);
    try std.testing.expectEqual(@as(usize, 1), score.invalid_suffix);
    try std.testing.expectEqual(@as(usize, 2), score.answered);
    try std.testing.expectEqual(@as(usize, 510), score.missing);
}
