# SENS LSP — Language Server Protocol adapter (M0–M3)

> A thin LSP adapter over the canonical SENS core.
> The LSP never re-parses `.lisp`, never greps for definitions, never
> invents semantics.

## Boundary rules (enforced by module layout)

| Concern | Owner |
|---|---|
| Parsing, spans, errors | `crates/sens` — canonical `parse()`, `Expr{kind,span}`, `LanguageError` reused unchanged |
| Position mapping (byte ↔ line/UTF-16) | LSP adapter (`analysis.rs`) — pure arithmetic |
| JSON-RPC framing (stdio Content-Length) | LSP transport (`transport.rs`) |
| JSON-RPC **decode** | canonical `sens::parse_json` (extracted from the `json-parse` special form; the special form delegates to it) |
| JSON-RPC **encode** | LSP transport-local (`jsonout.rs`) — deliberately NOT in the language core: no SENS feature independently needs a canonical serializer |

There is exactly one parser and one JSON decoder. Nothing is duplicated.

## M0 scope

Implemented: `initialize` (capabilities list exactly what exists),
`textDocument/didOpen`, `textDocument/didChange` (full sync),
`publishDiagnostics` (pushed on sync), `textDocument/documentSymbol`,
`textDocument/hover`, `textDocument/definition`, shutdown/exit lifecycle.

Out of scope: completion, rename, formatting, references, semantic
tokens, workspace indexing, AI/LLM and Yantra integration.

## Behavior notes

- **Diagnostics** come from the canonical parser (`LanguageError` with its
  proven span) plus canonical arity metadata for known direct calls. Unknown
  or dynamic heads are not guessed; locally shadowed builtins and quoted data
  are excluded.
- **documentSymbol** returns only structurally provable definitions:
  top-level `(def name ...)` / `(defmacro name ...)` whose second element
  is a symbol. Symbol text inside strings or comments can never qualify —
  it does not exist as a def-form in the AST. `SymbolKind` is Function
  (12) because LSP has no Macro kind; the exact keyword travels in
  `detail`. `selectionRange` covers just the defined name.
- **hover / definition** resolve through the same parse-tree def table,
  same document only (M0). Hovering unknown names returns `null` —
  unknown stays unknown.

## Running

Two equivalent entrypoints share one implementation:

```bash
cargo build --workspace

# subcommand of the main CLI binary (preferred):
target/debug/sens lsp

# standalone binary (kept for now):
target/debug/sens-lsp
```

Both speak LSP over stdio (`Content-Length` framing). stdout carries only
framed protocol traffic; use stderr for any debug logging. Point your
editor's LSP config at `sens lsp`.

## Release integration

`scripts/release.lisp` bumps all five canonical crates together
(`sens`, `sens-cli`, `sens-literate`, `sens-wasm`, `sens-lsp`). The test
`crates/sens-lsp/tests/release_parity.rs` fails on version drift,
so a crate added to one list but not the other cannot slip through.

## Tests

- `crates/sens-lsp/tests/e2e.rs` — end-to-end tests driving the
  real server with real JSON-RPC messages: capabilities, false-positive
  diagnostics, real parser-backed diagnostic ranges, def/defmacro symbols
  with exact selection ranges, hover payload with canonical source,
  go-to-definition range, string/comment non-detection, malformed-input
  robustness (server keeps serving afterwards).
- `crates/sens-lsp/tests/stdio.rs` — spawns the actual binary and
  performs a framed initialize → initialized → shutdown → exit handshake
  over pipes, like an editor would.

## M1 scope (2026-08-22)

Added on the same principles (canonical parser only, nothing invented):

- **Workspace index** (`workspace.rs`): `initialize` with `rootUri` scans
  all `.lisp` files under the root (4 MB per-file cap, hidden dirs skipped)
  and remembers every structurally proven definition with its file URI.
  Open/change events refresh one document's contributions incrementally.
- **Cross-file go-to-definition**: same-document resolution first (M0 path),
  then the workspace index. Ranges come from the defining file's own text.
- **Completion** (`textDocument/completion`, kind Function): local defs,
  runtime-discovered builtins, syntax-dispatched forms, workspace defs;
  filtered by the symbol prefix at the cursor. Core items include signatures.

## Known limitations

- Diagnostics deliberately cover parse errors and statically provable arity
  errors only; types and dynamic calls remain runtime concerns.
- Full-document sync (simple and correct, not incremental).
- Completion inherits parse-only honesty: a document that fails to parse
  contributes no definitions (visible while typing unbalanced forms).

## M2 scope (2026-08-22)

- **References** (`textDocument/references`): every code occurrence of
  the cursor symbol across open + indexed documents.
  `includeDeclaration` (context) is honored per-document — declarations
  live wherever their def-form is, not only in the cursor's file.
- **Rename** (`textDocument/rename`): WorkspaceEdit across all affected
  files. newName validated against the SENS symbol charset (error
  -32602 otherwise). Quoted data (`(quote x)` subtrees) is never touched:
  data symbols are not code references, per analysis::symbol_occurrences.

## M3 scope (2026-08-26)

- `sens::language_items()` is the tooling boundary for runtime-discovered
  builtin names plus explicit syntax-dispatched forms. Each item carries a
  signature, documentation, kind, and arity.
- Hover and completion consume the same metadata. Local definitions shadow
  first-class builtins exactly as they do in evaluation.
- Arity diagnostics inspect only canonical known heads. They do not infer
  user-function signatures, execute code, inspect quoted data, or classify
  unknown calls.
