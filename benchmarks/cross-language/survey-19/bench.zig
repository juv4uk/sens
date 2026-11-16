const std = @import("std");
const Io = std.Io;

fn fib(n: u64) u64 {
    if (n < 2) return n;
    return fib(n - 1) + fib(n - 2);
}

fn sieve(alloc: std.mem.Allocator, n: usize) !usize {
    const comp = try alloc.alloc(u8, n + 1);
    defer alloc.free(comp);
    @memset(comp, 0);

    var i: usize = 2;
    while (i * i <= n) : (i += 1) {
        if (comp[i] == 0) {
            var j: usize = i * i;
            while (j <= n) : (j += i) comp[j] = 1;
        }
    }

    var count: usize = 0;
    var k: usize = 2;
    while (k <= n) : (k += 1) {
        if (comp[k] == 0) count += 1;
    }
    return count;
}

fn collatz(n: u64) u64 {
    var total: u64 = 0;
    var i: u64 = 1;
    while (i <= n) : (i += 1) {
        var x = i;
        while (x != 1) {
            x = if (x % 2 == 0) x / 2 else 3 * x + 1;
            total += 1;
        }
    }
    return total;
}

pub fn main(init: std.process.Init) !void {
    const io = init.io;
    const arena = init.arena.allocator();
    const args = try init.minimal.args.toSlice(arena);

    var stdout_buffer: [256]u8 = undefined;
    var stdout_writer = Io.File.stdout().writer(io, &stdout_buffer);
    const out = &stdout_writer.interface;

    const fib_n: u64 = if (args.len > 1) try std.fmt.parseInt(u64, args[1], 10) else 35;
    const sieve_n: usize = if (args.len > 2) try std.fmt.parseInt(usize, args[2], 10) else 10_000_000;
    const col_n: u64 = if (args.len > 3) try std.fmt.parseInt(u64, args[3], 10) else 1_000_000;

    try out.print("fib({d}) = {d}\n", .{ fib_n, fib(fib_n) });
    try out.print("sieve({d}) = {d}\n", .{ sieve_n, try sieve(init.gpa, sieve_n) });
    try out.print("collatz({d}) = {d}\n", .{ col_n, collatz(col_n) });
    try out.flush();
}
