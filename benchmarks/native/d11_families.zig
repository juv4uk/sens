// d11-families: ті самі три операції, що в SENS-бенчмарку, але нативно Zig-ом.
// Zig тут — коридор і швидкий хост; порівняння з Rust і SENS чесне за однаковими операціями.
const std = @import("std");

fn filtr(xs: []const i64, p: i64, out: []i64) usize {
    var n: usize = 0;
    for (xs) |x| if (x == p) { out[n] = x; n += 1; };
    return n;
}
fn alistLookup(k: i64, keys: []const i64, vals: []const i64) ?i64 {
    for (keys, 0..) |key, i| if (key == k) return vals[i];
    return null;
}
fn freq(xs: []const i64, keys: []i64, counts: []usize) usize {
    var n: usize = 0;
    for (xs) |x| {
        var found = false;
        var i: usize = 0;
        while (i < n) : (i += 1) if (keys[i] == x) { counts[i] += 1; found = true; break; };
        if (!found) { keys[n] = x; counts[n] = 1; n += 1; }
    }
    return n;
}
fn once() usize {
    const xs = [_]i64{ 1, 2, 1, 3, 1, 4, 1 };
    const keys = [_]i64{ 1, 2, 3 };
    const vals = [_]i64{ 10, 20, 30 };
    var fbuf: [8]i64 = undefined;
    var kbuf: [8]i64 = undefined;
    var cbuf: [8]usize = undefined;
    const a = filtr(&xs, 1, &fbuf);
    const b: usize = if (alistLookup(2, &keys, &vals) != null) 1 else 0;
    const c = freq(&xs, &kbuf, &cbuf);
    return a + b + c;
}
pub fn main() !void {
    const reps: usize = 200000;
    var sink: usize = 0;
    var i: usize = 0;
    while (i < reps) : (i += 1) {
        sink += once();
    }
    std.debug.print("D11-FAMILIES-ZIG reps={d} sink={d} (час — зовнішній, через `time`)\n", .{ reps, sink });
}
