//! Deliberately DOES NOT compile: two exact domains cannot be equated.
//! Invoked only by the existing CI's compile-rejection witness.
const words = @import("domain_word.zig");

test "cross-width equality must not typecheck" {
    const one = words.DomainWord(1).init(0b1);
    const eight = words.DomainWord(8).init(0b0000_0001);
    _ = words.sameWord(1, one, eight);
}
