//! Драбина кодеків · рівень 1: щільний фізичний D12-run (дослідний).
//! Рівно 12 сирих бітів на слово, MSB-first; два слова займають три байти.
//! Raw payload лишається некадрованим; frameLen/encodeFrame/decodeFrame — окремий явний дослідний маршрут.
//! Код не вгадує домен, знак, дріб, float або виконуваність SENS.
//! Немає auto-detect/fallback до T5M, T5M3, F3C чи інших форматів. Кадр не є production .sens.

const std = @import("std");

pub const WIDTH: usize = 12;
pub const Error = error{
    EmptyRun,
    InvalidWord,
    OutputTooSmall,
    InvalidLength,
    NonCanonicalTail,
    TooLarge,
    InvalidMagic,
    UnsupportedVersion,
    WrongDomain,
    InvalidFrameLength,
    ChecksumMismatch,
};

/// Кількість байтів payload; у непарного останнє півбайта — нульове.
pub fn packedLen(word_count: usize) Error!usize {
    if (word_count == 0) return Error.EmptyRun;
    const pairs = std.math.mul(usize, word_count / 2, 3) catch return Error.TooLarge;
    return std.math.add(usize, pairs, if (word_count % 2 == 0) @as(usize, 0) else 2) catch
        return Error.TooLarge;
}

/// Транспортує непрозорі 12-бітні слова без втрати старших нулів.
/// За помилки жоден байт output не змінюється.
pub fn encode(words: []const u16, output: []u8) Error!usize {
    const n = try packedLen(words.len);
    for (words) |word| {
        if (word > 0x0fff) return Error.InvalidWord;
    }
    if (output.len < n) return Error.OutputTooSmall;
    // Кожний байт записується рівно один раз: додаткове занулення зайве.
    var i: usize = 0;
    var offset: usize = 0;
    while (i + 1 < words.len) {
        const first = words[i];
        const second = words[i + 1];
        output[offset] = @intCast(first >> 4);
        output[offset + 1] = @intCast(((first & 0x000f) << 4) | (second >> 8));
        output[offset + 2] = @intCast(second & 0x00ff);
        i += 2;
        offset += 3;
    }
    if (i < words.len) {
        const last = words[i];
        output[offset] = @intCast(last >> 4);
        output[offset + 1] = @intCast((last & 0x000f) << 4);
    }
    return n;
}

/// Відновлює рівно word_count слів. Невірна довжина чи padding — відмова.
/// За помилки жодне слово output не змінюється.
pub fn decode(data: []const u8, word_count: usize, output: []u16) Error!void {
    const n = try packedLen(word_count);
    if (data.len != n) return Error.InvalidLength;
    if (output.len < word_count) return Error.OutputTooSmall;
    if (word_count % 2 != 0 and (data[n - 1] & 0x0f) != 0)
        return Error.NonCanonicalTail;

    for (0..word_count) |i| {
        const base = (i / 2) * 3;
        output[i] = if (i % 2 == 0)
            (@as(u16, data[base]) << 4) | (@as(u16, data[base + 1]) >> 4)
        else
            ((@as(u16, data[base + 1]) & 0x0f) << 8) | @as(u16, data[base + 2]);
    }
}


/// Explicit opt-in research frame. This is not .sens/T5M and is never auto-detected.
/// Layout: "D12C" | version:u8 | domain-width:u8 | word-count:u32be
///         | payload-byte-count:u32be | packed payload | CRC-32/IEEE:u32be.
/// The frame identifies this raw transport only; it does not admit D12 evaluation.
pub const FRAME_MAGIC = "D12C";
pub const FRAME_VERSION: u8 = 1;
pub const FRAME_HEADER_LEN: usize = 14;
pub const FRAME_CHECKSUM_LEN: usize = 4;
pub const FRAME_OVERHEAD: usize = FRAME_HEADER_LEN + FRAME_CHECKSUM_LEN;

/// Exact framed size. The count and payload size are explicit 32-bit fields.
pub fn frameLen(word_count: usize) Error!usize {
    if (word_count > @as(usize, std.math.maxInt(u32))) return Error.TooLarge;
    const payload_len = try packedLen(word_count);
    if (payload_len > @as(usize, std.math.maxInt(u32))) return Error.TooLarge;
    return std.math.add(usize, FRAME_OVERHEAD, payload_len) catch return Error.TooLarge;
}

fn writeU32BE(output: []u8, offset: usize, value: u32) void {
    output[offset] = @truncate(value >> 24);
    output[offset + 1] = @truncate(value >> 16);
    output[offset + 2] = @truncate(value >> 8);
    output[offset + 3] = @truncate(value);
}

fn readU32BE(input: []const u8, offset: usize) u32 {
    return (@as(u32, input[offset]) << 24) |
        (@as(u32, input[offset + 1]) << 16) |
        (@as(u32, input[offset + 2]) << 8) |
        @as(u32, input[offset + 3]);
}

/// CRC-32/IEEE, reflected polynomial 0xEDB88320, init/xorout 0xFFFFFFFF.
fn checksum32(bytes: []const u8) u32 {
    var crc: u32 = 0xffff_ffff;
    for (bytes) |byte| {
        crc ^= @as(u32, byte);
        for (0..8) |_| {
            if ((crc & 1) != 0) {
                crc = (crc >> 1) ^ 0xedb8_8320;
            } else {
                crc >>= 1;
            }
        }
    }
    return ~crc;
}

/// Encodes a bounded explicit frame. All input/size checks precede any write.
pub fn encodeFrame(words: []const u16, output: []u8) Error!usize {
    const total_len = try frameLen(words.len);
    const payload_len = try packedLen(words.len);
    for (words) |word| {
        if (word > 0x0fff) return Error.InvalidWord;
    }
    if (output.len < total_len) return Error.OutputTooSmall;

    @memcpy(output[0..4], FRAME_MAGIC);
    output[4] = FRAME_VERSION;
    output[5] = @intCast(WIDTH);
    writeU32BE(output, 6, @intCast(words.len));
    writeU32BE(output, 10, @intCast(payload_len));
    _ = try encode(words, output[FRAME_HEADER_LEN .. FRAME_HEADER_LEN + payload_len]);
    writeU32BE(
        output,
        total_len - FRAME_CHECKSUM_LEN,
        checksum32(output[0 .. total_len - FRAME_CHECKSUM_LEN]),
    );
    return total_len;
}

/// Validates the complete frame before decoding to caller memory.
/// Wrong headers, inconsistent lengths and bad checksums fail closed.
pub fn decodeFrame(frame: []const u8, output: []u16) Error!usize {
    if (frame.len < FRAME_OVERHEAD) return Error.InvalidFrameLength;
    if (!std.mem.eql(u8, frame[0..4], FRAME_MAGIC)) return Error.InvalidMagic;
    if (frame[4] != FRAME_VERSION) return Error.UnsupportedVersion;
    if (frame[5] != @as(u8, @intCast(WIDTH))) return Error.WrongDomain;

    const word_count: usize = @intCast(readU32BE(frame, 6));
    const declared_payload_len: usize = @intCast(readU32BE(frame, 10));
    const payload_len = try packedLen(word_count);
    if (declared_payload_len != payload_len) return Error.InvalidFrameLength;
    const total_len = try frameLen(word_count);
    if (frame.len != total_len) return Error.InvalidFrameLength;

    const checksum_offset = frame.len - FRAME_CHECKSUM_LEN;
    if (readU32BE(frame, checksum_offset) != checksum32(frame[0..checksum_offset]))
        return Error.ChecksumMismatch;

    try decode(frame[FRAME_HEADER_LEN .. FRAME_HEADER_LEN + payload_len], word_count, output);
    return word_count;
}


test "D12 dense fixed vector preserves boundaries and leading zeros" {
    const source = [_]u16{ 0x800, 0xfff, 0x000, 0x001, 0x7ff };
    var bytes: [8]u8 = undefined;
    try std.testing.expectEqual(@as(usize, 8), try encode(&source, &bytes));
    try std.testing.expectEqualSlices(u8, &.{ 0x80, 0x0f, 0xff, 0x00, 0x00, 0x01, 0x7f, 0xf0 }, &bytes);

    var decoded: [source.len]u16 = undefined;
    try decode(&bytes, source.len, &decoded);
    try std.testing.expectEqualSlices(u16, &source, &decoded);
}

test "D12 dense exhaustive 4096 raw words with complementary partner" {
    for (0..4096) |i| {
        const a: u16 = @intCast(i);
        const source = [_]u16{ a, a ^ 0x0fff };
        var bytes: [3]u8 = undefined;
        try std.testing.expectEqual(@as(usize, 3), try encode(&source, &bytes));
        var decoded: [2]u16 = undefined;
        try decode(&bytes, source.len, &decoded);
        try std.testing.expectEqualSlices(u16, &source, &decoded);
    }
}

test "D12 dense overwrites reused nonzero buffers canonically" {
    var output = [_]u8{0xa5} ** 8;

    const first_len = try encode(&.{0xabc}, &output);
    try std.testing.expectEqual(@as(usize, 2), first_len);
    try std.testing.expectEqualSlices(u8, &.{ 0xab, 0xc0 }, output[0..first_len]);

    const second_len = try encode(&.{ 0x123, 0x456, 0x789 }, &output);
    try std.testing.expectEqual(@as(usize, 5), second_len);
    try std.testing.expectEqualSlices(u8, &.{ 0x12, 0x34, 0x56, 0x78, 0x90 }, output[0..second_len]);

    const third_len = try encode(&.{ 0xfff, 0x000 }, &output);
    try std.testing.expectEqual(@as(usize, 3), third_len);
    try std.testing.expectEqualSlices(u8, &.{ 0xff, 0xf0, 0x00 }, output[0..third_len]);
}

test "D12 dense exact byte ordering and run lengths" {
    const pairs = [_]struct { words: [2]u16, bytes: [3]u8 }{
        .{ .words = .{ 0x000, 0xfff }, .bytes = .{ 0x00, 0x0f, 0xff } },
        .{ .words = .{ 0xfff, 0x000 }, .bytes = .{ 0xff, 0xf0, 0x00 } },
        .{ .words = .{ 0xabc, 0x123 }, .bytes = .{ 0xab, 0xc1, 0x23 } },
        .{ .words = .{ 0x7ff, 0x800 }, .bytes = .{ 0x7f, 0xf8, 0x00 } },
    };
    for (pairs) |sample| {
        var bytes: [3]u8 = undefined;
        _ = try encode(&sample.words, &bytes);
        try std.testing.expectEqualSlices(u8, &sample.bytes, &bytes);
        var decoded: [2]u16 = undefined;
        try decode(&bytes, 2, &decoded);
        try std.testing.expectEqualSlices(u16, &sample.words, &decoded);
    }

    const counts = [_]usize{ 1, 2, 3, 4, 5, 16, 127, 128, 129 };
    const lengths = [_]usize{ 2, 3, 5, 6, 8, 24, 191, 192, 194 };
    for (counts, lengths) |count, expected| {
        try std.testing.expectEqual(expected, try packedLen(count));
    }
}

test "D12 dense long and odd runs preserve bytes on reencode" {
    const counts = [_]usize{ 1, 2, 3, 5, 16, 127, 128, 129, 4095, 4096 };
    var words: [4096]u16 = undefined;
    var decoded: [4096]u16 = undefined;
    var bytes: [6144]u8 = undefined;
    var replay: [6144]u8 = undefined;

    for (counts) |count| {
        for (0..count) |i| {
            words[i] = @intCast((i * 73 + (i >> 1) * 137) & 0x0fff);
        }
        const n = try encode(words[0..count], &bytes);
        try decode(bytes[0..n], count, decoded[0..count]);
        try std.testing.expectEqualSlices(u16, words[0..count], decoded[0..count]);

        const replay_n = try encode(decoded[0..count], &replay);
        try std.testing.expectEqual(n, replay_n);
        try std.testing.expectEqualSlices(u8, bytes[0..n], replay[0..replay_n]);
    }
}

test "D12 dense rejects invalid payload without modifying output" {
    var bytes = [_]u8{0xa5} ** 3;
    try std.testing.expectError(Error.InvalidWord, encode(&.{ 0x1000, 0x000 }, &bytes));
    try std.testing.expectEqualSlices(u8, &.{ 0xa5, 0xa5, 0xa5 }, &bytes);

    var short = [_]u8{0xa5} ** 2;
    try std.testing.expectError(Error.OutputTooSmall, encode(&.{ 0xabc, 0x123 }, &short));
    try std.testing.expectEqualSlices(u8, &.{ 0xa5, 0xa5 }, &short);

    var decoded = [_]u16{0xaaaa};
    try std.testing.expectError(Error.NonCanonicalTail, decode(&.{ 0xab, 0xc1 }, 1, &decoded));
    try std.testing.expectError(Error.InvalidLength, decode(&.{0xab}, 1, &decoded));
    try std.testing.expectError(Error.InvalidLength, decode(&.{ 0xab, 0xc0, 0x00 }, 1, &decoded));
    try std.testing.expectEqualSlices(u16, &.{0xaaaa}, &decoded);

    var short_decoded = [_]u16{0xbeef};
    try std.testing.expectError(Error.OutputTooSmall, decode(&.{ 0xab, 0xc1, 0x23 }, 2, &short_decoded));
    try std.testing.expectEqualSlices(u16, &.{0xbeef}, &short_decoded);

    var untouched = [_]u8{0xa5} ** 5;
    try std.testing.expectError(Error.InvalidWord, encode(&.{ 0xabc, 0x123, 0x1000 }, &untouched));
    try std.testing.expectEqualSlices(u8, &.{ 0xa5, 0xa5, 0xa5, 0xa5, 0xa5 }, &untouched);

    try std.testing.expectError(Error.EmptyRun, packedLen(0));
    try std.testing.expectError(Error.TooLarge, packedLen(std.math.maxInt(usize)));
}

test "D12 dense explicit frame validates version domain length and integrity" {
    const words = [_]u16{ 0x000, 0x001 };
    const golden = [_]u8{
        0x44, 0x31, 0x32, 0x43, 0x01, 0x0c, 0x00, 0x00, 0x00, 0x02, 0x00,
        0x00, 0x00, 0x03, 0x00, 0x00, 0x01, 0x1e, 0x23, 0xa9, 0x9f,
    };
    var frame: [golden.len]u8 = undefined;
    const encoded_len = try encodeFrame(&words, &frame);
    try std.testing.expectEqual(golden.len, encoded_len);
    try std.testing.expectEqualSlices(u8, &golden, &frame);

    var decoded: [2]u16 = undefined;
    try std.testing.expectEqual(@as(usize, 2), try decodeFrame(&frame, &decoded));
    try std.testing.expectEqualSlices(u16, &words, &decoded);

    const sentinel = [_]u16{ 0xaaaa, 0xbbbb };
    var untouched = sentinel;

    var bad_magic = golden;
    bad_magic[0] ^= 1;
    try std.testing.expectError(Error.InvalidMagic, decodeFrame(&bad_magic, &untouched));
    try std.testing.expectEqualSlices(u16, &sentinel, &untouched);

    var bad_version = golden;
    bad_version[4] = 2;
    try std.testing.expectError(Error.UnsupportedVersion, decodeFrame(&bad_version, &untouched));
    try std.testing.expectEqualSlices(u16, &sentinel, &untouched);

    var bad_domain = golden;
    bad_domain[5] = 11;
    try std.testing.expectError(Error.WrongDomain, decodeFrame(&bad_domain, &untouched));
    try std.testing.expectEqualSlices(u16, &sentinel, &untouched);

    var bad_length = golden;
    bad_length[13] = 4;
    try std.testing.expectError(Error.InvalidFrameLength, decodeFrame(&bad_length, &untouched));
    try std.testing.expectEqualSlices(u16, &sentinel, &untouched);
    try std.testing.expectError(Error.InvalidFrameLength, decodeFrame(golden[0 .. golden.len - 1], &untouched));

    var bad_payload = golden;
    bad_payload[14] ^= 1;
    try std.testing.expectError(Error.ChecksumMismatch, decodeFrame(&bad_payload, &untouched));
    try std.testing.expectEqualSlices(u16, &sentinel, &untouched);

    var bad_checksum = golden;
    bad_checksum[20] ^= 1;
    try std.testing.expectError(Error.ChecksumMismatch, decodeFrame(&bad_checksum, &untouched));
    try std.testing.expectEqualSlices(u16, &sentinel, &untouched);

    var short_output = [_]u16{0xbeef};
    try std.testing.expectError(Error.OutputTooSmall, decodeFrame(&golden, &short_output));
    try std.testing.expectEqualSlices(u16, &.{0xbeef}, &short_output);

    var invalid_output = [_]u8{0xa5} ** golden.len;
    const untouched_bytes = [_]u8{0xa5} ** golden.len;
    try std.testing.expectError(Error.InvalidWord, encodeFrame(&.{ 0x1000 }, &invalid_output));
    try std.testing.expectEqualSlices(u8, &untouched_bytes, &invalid_output);

    var short_frame = [_]u8{0xa5} ** (golden.len - 1);
    const untouched_short_frame = short_frame;
    try std.testing.expectError(Error.OutputTooSmall, encodeFrame(&words, &short_frame));
    try std.testing.expectEqualSlices(u8, &untouched_short_frame, &short_frame);
    try std.testing.expectError(Error.EmptyRun, frameLen(0));
    try std.testing.expectError(Error.TooLarge, frameLen(std.math.maxInt(usize)));
}
