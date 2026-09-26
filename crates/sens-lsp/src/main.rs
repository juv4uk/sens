//! Standalone `sens-lsp` binary — a thin wrapper around the library
//! entrypoint. Kept alongside `sens lsp` so both entrypoints share one
//! implementation.

fn main() {
    sens_lsp::run_stdio()
}
