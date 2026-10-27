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


