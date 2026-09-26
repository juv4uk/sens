//! lsp_entry.rs - dispatch glue for the `sens lsp` subcommand.
//! Deliberately tiny: all LSP protocol, transport and analysis logic
//! lives in the sens-lsp crate; this module only forwards to its
//! public stdio entrypoint so editors need just one binary.

pub(crate) fn run() {
    sens_lsp::run_stdio()
}
