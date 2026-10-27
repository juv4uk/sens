//! Package-root Zig 0.16.0 tests: physical codecs and freestanding ABI share this module root.
//! Avoid standalone f3c.zig import escaping its module root.
const std = @import("std");
const t5 = @import("t5/t5.zig");
const t5m = @import("t5m.zig");
const d12_dense_experiment = @import("d12_dense_experiment.zig");
const t5m3 = @import("t5m3.zig");
const physical_cycle = @import("physical_cycle.zig");
const ladder = @import("domain_ladder.zig");
const ladder_memory_game = @import("ladder_memory_game.zig");
const ladder_e1 = @import("domain_e1.zig");
const domain_sequence = @import("domain_sequence.zig");
const f3c = @import("f3c/f3c.zig");
const abi = @import("transport_abi.zig");
const freestanding = @import("freestanding.zig");
const envelope_fields = @import("transport/fields.zig");
const e1_physical = @import("transport/e1.zig");
const e1_writer = @import("transport/e1_writer.zig");
const physical_parity_manifest = @import("parity_t5.zig");
const ladder_stdin_tool = @import("tools/ladder_tool.zig");
const transport_cli = @import("transport.zig");

// Current owner-ratified domain ladder only. Exhaust all D8 payloads and
// compare with independent D9 identities carrying the SAME payload bits.
// This is a transport/width law, not a historical mapping or a SENS evaluator.
// Бенчмарк саме Zig ABI, не Lisp-законів. Той самий transport_abi.zig
// виконує encode BE3 -> T5, що й фізичний коридор з Rust. Ні D1-вердиктів,
// ні Python-підміни. Шум shared runner не перетворюємо на швидкісний gate.
// Zig 0.16 вилучив std.time.Timer: для цього Linux CI потрібен CLOCK_MONOTONIC.
const bench_clock = @cImport({
    @cInclude("time.h");
});

fn benchMonotonicNs() !u64 {
    var ts: bench_clock.struct_timespec = undefined;
    if (bench_clock.clock_gettime(bench_clock.CLOCK_MONOTONIC, &ts) != 0)
        return error.ClockUnavailable;
    return @as(u64, @intCast(ts.tv_sec)) * 1_000_000_000 +
        @as(u64, @intCast(ts.tv_nsec));
}

