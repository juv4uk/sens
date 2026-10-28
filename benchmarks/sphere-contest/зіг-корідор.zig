//! Сфера Zig: корідор.
//! ЦІЛЬ: D6 додати-1 (001110), lib/domains/d6.lisp:23.
//! Міряє лише перенесення T5M: запис числа в десятковий вигляд і читання назад.
//! Власного годинника немає: у Zig 0.16 std.time має лише константи,
//! а std.Io вимагає екземпляра. Час міряє оболонка навколо процесу.
const std = @import("std");

const rounds: usize = 1_000_000;

pub fn main() !void {
    var buf: [64]u8 = undefined;
    var checksum: u64 = 0;

    var round: usize = 0;
    while (round < rounds) : (round += 1) {
        const value: u64 = @intCast(round);
        const written = try std.fmt.bufPrint(&buf, "{d}", .{value});
        const read_back = try std.fmt.parseInt(u64, written, 10);
        if (read_back != value) return error.TransportLoss;
        checksum +%= read_back;
    }
    std.debug.print("зіг-корідор: {d} обертів, контрольна сума {d}\n", .{ rounds, checksum });
}
