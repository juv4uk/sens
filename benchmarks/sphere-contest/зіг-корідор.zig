//! Сфера Zig: корідор.
//! ЦІЛЬ: D6 додати-1 (001110), lib/domains/d6.lisp:23.
//! Міряє лише перенесення T5M: кодування й декодування числа без втрат.
const std = @import("std");

pub fn main() !void {
    var буфер: [64]u8 = undefined;
    const значення: u64 = 1;
    var найкраще: u64 = std.math.maxInt(u64);

    var оберт: usize = 0;
    while (оберт < 100_000) : (оберт += 1) {
        const початок = std.time.nanoTimestamp();
        const записано = try std.fmt.bufPrint(&буфер, "{d}", .{значення});
        const прочитано = try std.fmt.parseInt(u64, записано, 10);
        const кінець = std.time.nanoTimestamp();
        if (прочитано != значення) return error.ВтратаПриПеренесенні;
        const тривало = @as(u64, @intCast(кінець - початок));
        if (тривало < найкраще) найкраще = тривало;
    }
    std.debug.print("зіг-корідор: найкращий оберт {d} нс\n", .{найкраще});
}
