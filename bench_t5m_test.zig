//! Zig 0.16: фізична перевірка T5M, без мовного оракула SENS.
//! Виконувати zig test окремо від zig run бенчмарка.
const std = @import("std");
const codec = @import("research/zig-codecs/t5m.zig");
const benchmark = @import("bench_t5m.zig");
const physical: []const u8 = @embedFile("benchmarks/lists.sens");

