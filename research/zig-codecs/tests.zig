//! Package-root Zig 0.16.0 tests: physical codecs and freestanding ABI share this module root.
//! Avoid standalone f3c.zig import escaping its module root.
const std = @import("std");
const t5 = @import("t5/t5.zig");
const f3c = @import("f3c/f3c.zig");
const abi = @import("transport_abi.zig");
const freestanding = @import("freestanding.zig");
const envelope_fields = @import("transport/fields.zig");
const e1_physical = @import("transport/e1.zig");
const e1_writer = @import("transport/e1_writer.zig");

test "import exact-width transport suites" {
    std.debug.assert(@sizeOf(t5.Word) > 0);
    std.debug.assert(f3c.FRAME_LABEL == 0xf3);
    std.debug.assert(freestanding.F3C_SCRATCH_BYTES == 8192);
    std.debug.assert(freestanding.F3C_SUFFIX_ROM_BYTES == 4000);
    _ = t5;
    _ = f3c;
    _ = abi;
    _ = freestanding;
    _ = envelope_fields;
    _ = e1_physical;
    _ = e1_writer;
}
