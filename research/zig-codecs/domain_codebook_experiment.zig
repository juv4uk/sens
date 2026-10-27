//! DWC1: дослідний словниковий фізичний носій точних (width,bits).
//! Це НЕ production-кодек і НЕ SENS evaluator. Словник містить тільки біти.
//! Формат: F3 01 | ULEB(word_count) | prefix-bitstream | zero tail.
//! Кодова книга зафіксована на core.sens; інші корпуси — незалежна перевірка.
const std = @import("std");
const t5m = @import("t5m.zig");

pub const Word = t5m.Word;
pub const Decoded = t5m.Decoded;
pub const Error = error{
    EmptyProgram,
    WrongMagic,
    UnsupportedVersion,
    InvalidBinaryDigit,
    InvalidWidth,
    InvalidCount,
    NonCanonical,
    Truncated,
    InvalidTail,
    TransportTooLarge,
    OutOfMemory,
};

const MAX_BYTES: usize = t5m.MAX_PHYSICAL_BYTES;
const MAX_WORD_BITS: usize = MAX_BYTES * 5;
const MAGIC = [_]u8{ 0xf3, 0x01 };

// 16 механічних семибітових координат з тренувального core.sens.
// Порядок — частота в frozen training corpus; жодного імені чи семантики.
const DICTIONARY = [_][]const u8{
    "1111001", "1110100", "1100110", "1101110",
    "1101000", "1100101", "1111010", "1100010",
    "1110000", "0101101", "1101010", "1110011",
    "1110101", "1110010", "1110110", "1111000",
};

fn exact(word: Word, bits: []const u8) bool {
    return word.width == bits.len and std.mem.eql(u8, word.bits, bits);
}

fn dictionaryIndex(word: Word) ?u8 {
    if (word.width != 7) return null;
    for (DICTIONARY, 0..) |bits, i| {
        if (std.mem.eql(u8, word.bits, bits)) return @intCast(i);
    }
    return null;
}

fn gammaBitCount(value: usize) usize {
    var n = value;
    var zeroes: usize = 0;
    while (n > 1) : (n >>= 1) zeroes += 1;
    return 2 * zeroes + 1;
}

fn countByteLen(value: usize) usize {
    var n = value;
    var bytes: usize = 1;
    while (n >= 128) : (n >>= 7) bytes += 1;
    return bytes;
}

fn wordBitCount(word: Word) usize {
    if (exact(word, "00")) return 1;
    if (exact(word, "10") or exact(word, "01")) return 3;
    if (dictionaryIndex(word) != null) return 7;
    return 3 + gammaBitCount(word.width) + word.width;
}

const Writer = struct {
    bytes: []u8,
    bit_pos: usize = 0,

    fn bit(self: *Writer, value: u8) void {
        std.debug.assert(value <= 1 and self.bit_pos < self.bytes.len * 8);
        const index = self.bit_pos / 8;
        const shift: u3 = @intCast(7 - self.bit_pos % 8);
        self.bytes[index] |= value << shift;
        self.bit_pos += 1;
    }

    fn bits(self: *Writer, value: usize, count: usize) void {
        var remaining = count;
        while (remaining > 0) {
            remaining -= 1;
            const shift: u6 = @intCast(remaining);
            self.bit(@intCast((value >> shift) & 1));
        }
    }

    fn gamma(self: *Writer, value: usize) void {
        const half = gammaBitCount(value) / 2;
        for (0..half) |_| self.bit(0);
        self.bits(value, half + 1);
    }
};

fn writeCount(out: []u8, count: usize) usize {
    var n = count;
    var pos: usize = 0;
    while (n >= 128) {
        out[pos] = @intCast((n & 0x7f) | 0x80);
        n >>= 7;
        pos += 1;
    }
    out[pos] = @intCast(n);
    return pos + 1;
}

pub fn encode(allocator: std.mem.Allocator, words: []const Word) Error![]u8 {
    if (words.len == 0) return Error.EmptyProgram;
    var payload_bits: usize = 0;
    for (words) |word| {
        if (word.width == 0 or word.width > MAX_WORD_BITS or word.bits.len != word.width)
            return Error.InvalidWidth;
        for (word.bits) |bit| {
            if (bit != '0' and bit != '1') return Error.InvalidBinaryDigit;
        }
        payload_bits = std.math.add(usize, payload_bits, wordBitCount(word)) catch
            return Error.TransportTooLarge;
    }
    const payload_bytes = std.math.add(usize, payload_bits, 7) catch
        return Error.TransportTooLarge;
    const total = std.math.add(usize, 2 + countByteLen(words.len), payload_bytes / 8) catch
        return Error.TransportTooLarge;
    if (total > MAX_BYTES) return Error.TransportTooLarge;

    const output = allocator.alloc(u8, total) catch return Error.OutOfMemory;
    @memset(output, 0);
    output[0] = MAGIC[0];
    output[1] = MAGIC[1];
    const header_len = 2 + writeCount(output[2..], words.len);
    var writer = Writer{ .bytes = output[header_len..] };
    for (words) |word| {
        if (exact(word, "00")) {
            writer.bit(0);
        } else if (exact(word, "10")) {
            writer.bits(0b100, 3);
        } else if (exact(word, "01")) {
            writer.bits(0b101, 3);
        } else if (dictionaryIndex(word)) |index| {
            writer.bits(0b110, 3);
            writer.bits(@as(usize, index), 4);
        } else {
            writer.bits(0b111, 3);
            writer.gamma(word.width);
            for (word.bits) |digit| writer.bit(digit - '0');
        }
    }
    std.debug.assert(writer.bit_pos == payload_bits);
    return output;
}

const Reader = struct {
    bytes: []const u8,
    bit_pos: usize = 0,

    fn remaining(self: *const Reader) usize {
        return self.bytes.len * 8 - self.bit_pos;
    }

    fn bit(self: *Reader) Error!u8 {
        if (self.remaining() == 0) return Error.Truncated;
        const index = self.bit_pos / 8;
        const shift: u3 = @intCast(7 - self.bit_pos % 8);
        const value = (self.bytes[index] >> shift) & 1;
        self.bit_pos += 1;
        return value;
    }

    fn bits(self: *Reader, count: usize) Error!usize {
        if (count > @bitSizeOf(usize) or count > self.remaining()) return Error.Truncated;
        var value: usize = 0;
        for (0..count) |_| value = (value << 1) | @as(usize, try self.bit());
        return value;
    }

    fn gamma(self: *Reader) Error!usize {
        var zeroes: usize = 0;
        while ((try self.bit()) == 0) {
            zeroes += 1;
            if (zeroes >= @bitSizeOf(usize)) return Error.InvalidWidth;
        }
        var value: usize = 1;
        for (0..zeroes) |_| value = (value << 1) | @as(usize, try self.bit());
        if (value == 0) return Error.InvalidWidth;
        return value;
    }
};

fn readCount(data: []const u8) Error!struct { count: usize, body: usize } {
    if (data.len == 0) return Error.EmptyProgram;
    if (data.len < 3) return Error.Truncated;
    if (data[0] != MAGIC[0]) return Error.WrongMagic;
    if (data[1] != MAGIC[1]) return Error.UnsupportedVersion;
    var count: usize = 0;
    var factor: usize = 1;
    var pos: usize = 2;
    while (true) {
        if (pos >= data.len) return Error.Truncated;
        const byte = data[pos];
        pos += 1;
        const term = std.math.mul(usize, @as(usize, byte & 0x7f), factor) catch
            return Error.InvalidCount;
        count = std.math.add(usize, count, term) catch return Error.InvalidCount;
        if ((byte & 0x80) == 0) {
            if (pos > 3 and (byte & 0x7f) == 0) return Error.NonCanonical;
            break;
        }
        factor = std.math.mul(usize, factor, 128) catch return Error.InvalidCount;
    }
    if (count == 0) return Error.InvalidCount;
    return .{ .count = count, .body = pos };
}

fn literal(out: ?[]u8, source: []const u8) Error!usize {
    if (out) |target| {
        if (target.len != source.len) return Error.InvalidWidth;
        for (source, 0..) |digit, i| target[i] = digit;
    }
    return source.len;
}

fn readWord(reader: *Reader, out: ?[]u8) Error!usize {
    if (try reader.bit() == 0) return literal(out, "00");
    if (try reader.bit() == 0) {
        return literal(out, if (try reader.bit() == 0) "10" else "01");
    }
    if (try reader.bit() == 0) {
        const index = try reader.bits(4);
        return literal(out, DICTIONARY[index]);
    }
    const width = try reader.gamma();
    if (width == 0 or width > MAX_WORD_BITS) return Error.InvalidWidth;
    if (width > reader.remaining()) return Error.Truncated;
    if (out) |target| {
        if (target.len != width) return Error.InvalidWidth;
    }

    // Літеральний escape не може дублювати короткий канонічний код.
    // Перша проходка з out=null теж має відхилити неканонічний кадр.
    if (width == 2 or width == 7) {
        var small_value: u8 = 0;
        for (0..width) |i| {
            const bit = try reader.bit();
            small_value = (small_value << 1) | bit;
            if (out) |target| target[i] = bit + '0';
        }
        if (width == 2 and small_value != 0b11) return Error.NonCanonical;
        if (width == 7) {
            for (DICTIONARY) |bits| {
                var dictionary_value: u8 = 0;
                for (bits) |digit| {
                    dictionary_value = (dictionary_value << 1) | (digit - '0');
                }
                if (small_value == dictionary_value) return Error.NonCanonical;
            }
        }
    } else if (out) |target| {
        for (target) |*digit| digit.* = (try reader.bit()) + '0';
    } else {
        for (0..width) |_| _ = try reader.bit();
    }
    return width;
}

fn checkTail(reader: *Reader) Error!void {
    if ((reader.bit_pos + 7) / 8 != reader.bytes.len) return Error.InvalidTail;
    while (reader.remaining() != 0) {
        if (try reader.bit() != 0) return Error.InvalidTail;
    }
}

pub fn decode(allocator: std.mem.Allocator, data: []const u8) Error!Decoded {
    if (data.len > MAX_BYTES) return Error.TransportTooLarge;
    const header = try readCount(data);
    const body = data[header.body..];
    if (header.count > body.len * 8) return Error.InvalidCount;

    const words = allocator.alloc(t5m.DecodedWord, header.count) catch
        return Error.OutOfMemory;
    errdefer allocator.free(words);
    var first = Reader{ .bytes = body };
    var total_bits: usize = 0;
    for (words) |*word| {
        const width = try readWord(&first, null);
        total_bits = std.math.add(usize, total_bits, width) catch
            return Error.TransportTooLarge;
        if (total_bits > MAX_WORD_BITS) return Error.TransportTooLarge;
        word.* = .{ .width = width, .bits = &.{} };
    }
    try checkTail(&first);
    const storage = allocator.alloc(u8, total_bits) catch return Error.OutOfMemory;
    errdefer allocator.free(storage);
    var second = Reader{ .bytes = body };
    var offset: usize = 0;
    for (words) |*word| {
        const dest = storage[offset .. offset + word.width];
        const actual_width = try readWord(&second, dest);
        if (actual_width != word.width) return Error.InvalidWidth;
        word.bits = dest;
        offset += word.width;
    }
    try checkTail(&second);
    return .{ .words = words, .bit_storage = storage };
}

