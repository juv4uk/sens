const assets = [_][]const u8{
    @embedFile("lib/unify.lisp"),
    @embedFile("lib/reason.lisp"),
    @embedFile("lib/forward.lisp"),
    @embedFile("lib/knowledge.lisp"),
    @embedFile("lib/persistent-map.lisp"),
    @embedFile("lib/persistent-vector.lisp"),
    @embedFile("lib/epistemic.lisp"),
    @embedFile("lib/surface/uk.lisp"),
    @embedFile("lib/surface/ukr.lisp"),
    @embedFile("lib/surface/sa.lisp"),
};

export fn sens_wasm_source_asset_len(asset: u32) callconv(.c) usize {
    if (asset >= assets.len) return 0;
    return assets[@intCast(asset)].len;
}

export fn sens_wasm_source_asset_copy(
    asset: u32,
    destination: [*]u8,
    capacity: usize,
) callconv(.c) isize {
    if (asset >= assets.len) return -1;
    const source = assets[@intCast(asset)];
    if (capacity < source.len) return -2;
    @memcpy(destination[0..source.len], source);
    return @intCast(source.len);
}
