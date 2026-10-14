//! Package-root Zig 0.16.0 tests: both codec modules share this import root.
//! Avoid standalone f3c.zig import escaping its module root.
const std = @import("std");
const t5 = @import("t5/t5.zig");
const f3c = @import("f3c/f3c.zig");
const abi = @import("transport_abi.zig");
const envelope_fields = @import("transport/fields.zig");
const sterile_ladder = @import("sterile/domain_word.zig");

test "import exact-width transport suites" {
    std.debug.assert(@sizeOf(t5.Word) > 0);
    std.debug.assert(f3c.FRAME_LABEL == 0xf3);
    _ = t5;
    _ = f3c;
    _ = abi;
    _ = envelope_fields;
    _ = sterile_ladder;
}
