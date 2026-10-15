# Rust-isolation patch #1: carry `language-contract.lisp` through the Zig ABI

Template: how `lib/linter.lisp` was retired (commit `526befd6c8`). Apply **all three
parts atomically** -- a partial apply breaks the build (the Rust part references a Zig
export that must exist). Prepared here because the agent sandbox has no Zig 0.16.0; the
swarm applies and proves it. Target: the first entry of
`research/rust-project-deps-plan.json` (`../../../language-contract.lisp`).

---

## Part 1 -- `zig_transport_root.zig` (embed + export, mirror the linter)

Add after the `linter_asset` block (≈ line 29):

```zig
// A second opaque asset: the language contract. Same fail-closed contract --
// caller owns memory; capacity=0 queries exact byte length; -2 = no partial write.
const contract_asset = @embedFile("language-contract.lisp");
pub export fn sens_zig_language_contract_bytes_copy(dst: [*]u8, capacity: usize) isize {
    if (contract_asset.len == 0) return -1;
    if (capacity == 0) return @intCast(contract_asset.len);
    if (capacity < contract_asset.len) return -2;
    @memcpy(dst[0..contract_asset.len], contract_asset[0..contract_asset.len]);
    return @intCast(contract_asset.len);
}

test "opaque language-contract bytes cross Zig without partial writes or semantic registry" {
    const required = sens_zig_language_contract_bytes_copy(undefined, 0);
    try std.testing.expectEqual(@as(isize, @intCast(contract_asset.len)), required);
    var short: [1]u8 = .{0xA5};
    try std.testing.expectEqual(@as(isize, -2),
        sens_zig_language_contract_bytes_copy(&short, short.len));
    try std.testing.expectEqual(@as(u8, 0xA5), short[0]);
    var output: [contract_asset.len]u8 = undefined;
    try std.testing.expectEqual(required,
        sens_zig_language_contract_bytes_copy(&output, output.len));
    try std.testing.expectEqualSlices(u8, contract_asset[0..contract_asset.len], &output);
}
```

## Part 2 -- `crates/sens-cli/src/zig_transport.rs` (extern + carrier)

In the `unsafe extern "C" { ... }` block, next to the linter export:

```rust
    fn sens_zig_language_contract_bytes_copy(output: *mut u8, capacity: usize) -> isize;
```

After `linter_source_bytes`, mirror it exactly:

```rust
/// Retrieves opaque language-contract bytes through the sterile Zig C ABI.
/// No direct Rust include/open of language-contract.lisp and no semantic work in Zig.
pub fn language_contract_source_bytes() -> Result<Vec<u8>, String> {
    version()?;
    let required = unsafe {
        sens_zig_language_contract_bytes_copy(std::ptr::NonNull::<u8>::dangling().as_ptr(), 0)
    };
    if required <= 0 {
        return Err("ZIG_CONTRACT_CARRIER invalid source length".into());
    }
    let len = usize::try_from(required).map_err(|_| "ZIG_CONTRACT_CARRIER length overflow")?;
    // Host memory bound. This is not a SENS domain/semantic admission threshold.
    if len > 8 * 1024 * 1024 {
        return Err("ZIG_CONTRACT_CARRIER source exceeds host byte limit".into());
    }
    let mut bytes = vec![0u8; len];
    let copied = unsafe { sens_zig_language_contract_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };
    if copied != required {
        return Err(format!("ZIG_CONTRACT_CARRIER byte copy rejected: code={copied}"));
    }
    Ok(bytes)
}
```

## Part 3 -- `crates/sens-cli/src/main.rs` (carrier fn + replace the include)

Add after `linter_source_zig_only`:

```rust
/// Isolated byte carrier for the language contract. SENS decides its meaning.
fn language_contract_zig_only() -> Result<String, String> {
    #[cfg(feature = "zig-transport")]
    {
        let bytes = zig_transport::language_contract_source_bytes()?;
        String::from_utf8(bytes)
            .map_err(|e| format!("ZIG_CONTRACT_CARRIER invalid UTF-8 surface: {e}"))
    }
    #[cfg(not(feature = "zig-transport"))]
    {
        Err("RUST_ZIG_ONLY: language contract requires Zig; no Rust project-source fallback".into())
    }
}
```

Replace the direct include (≈ line 247):

```rust
        let contract_source = include_str!("../../../language-contract.lisp");
```

with:

```rust
        let contract_source = match language_contract_zig_only() {
            Ok(source) => source,
            Err(error) => {
                eprintln!("Error loading language contract through Zig: {error}");
                process::exit(2);
            }
        };
```

---

## Acceptance

1. `cargo build --features zig-transport` + `zig build-exe zig_transport_root.zig` both build.
2. `python3 scripts/report_rust_project_deps.py --check` -- the contract dep shows as
   **burndown** (12 -> 11); no new dependency.
3. The physical `.sens` route and `--lint` still pass (linter and contract both cross Zig).
4. `scripts/check_rust_isolated_only_zig.py` -- one fewer violation.

**Order:** repeat this exact shape for the remaining 11 in `crates/sens/src/lib.rs`
(`macro`, `core2`, `core3`, `core4`, `generated/meta-semantic-registry`, `meta-eval`,
`time`, `utf8`, `process`, `tcp`, `fs`) -- one atomic commit each, ledger records each.
