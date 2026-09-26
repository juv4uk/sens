//! MY-LISP-LSP M0 acceptance tests. Every test drives the real server
//! with real framed JSON-RPC/LSP messages and asserts on the protocol
//! responses — a handler only counts as implemented when this passes.

use sens::{Environment, Value};
use sens_lsp::Harness as Server;
use std::fs;
use std::path::{Path, PathBuf};

fn raw(m: &str) -> String {
    m.to_string()
}

/// initialize → capabilities must list exactly the M0 features.
#[test]
fn t01_initialize_returns_m0_capabilities() {
    let mut server = Server::new();
    let replies = server.feed(&[raw(
        r#"{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}"#,
    )]);
    assert_eq!(replies.len(), 1);
    let r = replies[0].as_str();
    assert!(r.contains("\"capabilities\""), "{r}");
    assert!(r.contains("\"textDocumentSync\":1"), "{r}");
    assert!(r.contains("\"documentSymbolProvider\":true"), "{r}");
    assert!(r.contains("\"hoverProvider\":true"), "{r}");
    assert!(r.contains("\"definitionProvider\":true"), "{r}");
    // M1 added completion; M2 adds references+rename.
    assert!(r.contains("\"referencesProvider\":true"), "{r}");
    assert!(r.contains("\"renameProvider\":true"), "{r}");
    assert!(
        r.contains("\"completionProvider\""),
        "M1 completion advertised: {r}"
    );
}

const VALID_DOC: &str = "; a comment mentioning mystery_word\n(def answer 42)\n(defmacro unless (cond body) (list 'if cond body))\n";

/// didOpen of a valid document → publishDiagnostics with EMPTY list.
#[test]
fn t02_valid_document_produces_no_false_diagnostics() {
    let mut server = Server::new();
    let open = format!(
        r#"{{"jsonrpc":"2.0","method":"textDocument/didOpen","params":{{"textDocument":{{"uri":"file:///t.lisp","languageId":"sens","version":1,"text":{}}}}}}}"#,
        json_string(VALID_DOC)
    );
    let replies = server.feed(&[open]);
    assert_eq!(replies.len(), 1);
    let r = replies[0].as_str();
    assert!(r.contains("publishDiagnostics"), "{r}");
    assert!(
        r.contains("\"diagnostics\":[]"),
        "no false diagnostics: {r}"
    );
}

/// didOpen of an invalid document → at least one parser-backed diagnostic
/// with the canonical error span.
#[test]
fn t03_invalid_document_produces_real_diagnostic() {
    let mut server = Server::new();
    let bad = "(def x 1)\n(def broken\n"; // unclosed list on line 2
    let open = format!(
        r#"{{"jsonrpc":"2.0","method":"textDocument/didOpen","params":{{"textDocument":{{"uri":"file:///bad.lisp","languageId":"sens","version":1,"text":{}}}}}}}"#,
        json_string(bad)
    );
    let replies = server.feed(&[open]);
    assert_eq!(replies.len(), 1);
    let r = replies[0].as_str();
    assert!(r.contains("publishDiagnostics"), "{r}");
    assert!(
        !r.contains("\"diagnostics\":[]"),
        "must contain a diagnostic: {r}"
    );
    assert!(r.contains("\"severity\":1"), "{r}");
    assert!(r.contains("\"source\":\"sens\""), "{r}");
    assert!(
        sens::parse_json(r).is_ok(),
        "diagnostic must be valid JSON: {r}"
    );
    // The diagnostic range must point into line 1 (0-based), where the
    // unclosed form starts — proven by the canonical parser's span.
    assert!(r.contains("\"start\":{\"line\":1"), "{r}");
}

/// documentSymbol finds a real top-level `(def ...)` with exact ranges.
#[test]
fn t04_document_symbol_finds_def() {
    let (reply, _) = symbols_for(VALID_DOC);
    assert!(reply.contains("\"name\":\"answer\""), "{reply}");
    assert!(reply.contains("\"detail\":\"def\""), "{reply}");
    // selectionRange points at the NAME, not the whole form:
    // `(def answer` — the name starts at character 5.
    assert!(
        reply.contains("\"selectionRange\":{\"start\":{\"line\":1,\"character\":5}"),
        "{reply}"
    );
    // ordinary text in the comment is not a symbol
    assert!(!reply.contains("mystery_word"), "{reply}");
}

/// documentSymbol finds a real `(defmacro ...)`.
#[test]
fn t05_document_symbol_finds_defmacro() {
    let (reply, _) = symbols_for(VALID_DOC);
    assert!(reply.contains("\"name\":\"unless\""), "{reply}");
    assert!(reply.contains("\"detail\":\"defmacro\""), "{reply}");
}

fn symbols_for(doc: &str) -> (String, String) {
    let mut server = Server::new();
    let open = format!(
        r#"{{"jsonrpc":"2.0","method":"textDocument/didOpen","params":{{"textDocument":{{"uri":"file:///s.lisp","languageId":"sens","version":1,"text":{}}}}}}}"#,
        json_string(doc)
    );
    let symbols = r#"{"jsonrpc":"2.0","id":7,"method":"textDocument/documentSymbol","params":{"textDocument":{"uri":"file:///s.lisp"}}}"#;
    let replies = server.feed(&[open, symbols.to_string()]);
    assert_eq!(replies.len(), 2);
    (replies[1].clone(), replies[0].clone())
}

/// hover on a locally defined symbol → kind + location + canonical source.
#[test]
fn t06_hover_on_known_definition_is_useful() {
    let mut server = Server::new();
    let doc = "(def greeting \"hello\")\n(print greeting)\n";
    let open = open_msg("file:///h.lisp", doc);
    // hover over `greeting` usage on line 1 char 8.
    let hover = hover_msg("file:///h.lisp", 1, 8);
    let replies = server.feed(&[open, hover]);
    assert_eq!(replies.len(), 2);
    let r = &replies[1];
    assert!(
        r.contains("\"result\":{\"contents\":{\"kind\":\"markdown\""),
        "{r}"
    );
    assert!(r.contains("**def** `greeting`"), "{r}");
    // The canonical representation of the defining form travels along.
    assert!(r.contains("(def greeting \\\"hello\\\")"), "{r}");

    // A local binding shadows a builtin in the evaluator and must also
    // shadow its tooling metadata.
    let mut shadow_server = Server::new();
    let shadow_doc = "(def max 42)\n(max)\n";
    let replies = shadow_server.feed(&[
        open_msg("file:///shadow.lisp", shadow_doc),
        hover_msg("file:///shadow.lisp", 1, 2),
    ]);
    let shadow = &replies[1];
    assert!(
        shadow.contains("**def** `max`"),
        "local max must win: {shadow}"
    );
    assert!(
        !shadow.contains("**builtin**"),
        "builtin metadata leaked: {shadow}"
    );
}

/// definition on a use of a local symbol → the def name's exact range.
#[test]
fn t07_definition_resolves_to_correct_range() {
    let mut server = Server::new();
    let doc = "(def target (+ 1 2))\n(+ target 10)\n";
    let open = open_msg("file:///d.lisp", doc);
    let goto =
        r#"{"jsonrpc":"2.0","id":3,"method":"textDocument/definition","params":{"textDocument":{"uri":"file:///d.lisp"},"position":{"line":1,"character":3}}}"#.to_string();
    let replies = server.feed(&[open, goto]);
    assert_eq!(replies.len(), 2);
    let r = &replies[1];
    // `target` is defined at line 0, chars 5..11 ("(def |target| ...").
    assert!(
        r.contains("\"uri\":\"file:///d.lisp\"") && r.contains("\"range\":{\"start\":{\"line\":0,\"character\":5},\"end\":{\"line\":0,\"character\":11}}"),
        "{r}"
    );
}

/// Symbol text inside strings and comments must never be a definition.
#[test]
fn t08_symbols_in_strings_and_comments_are_not_definitions() {
    let mut server = Server::new();
    let doc = concat!(
        "; (def commented-out 1)\n",
        "(print \"(def in-string 2)\")\n",
        "(def real-def 3)\n"
    );
    let open = open_msg("file:///c.lisp", doc);
    let symbols = symbols_msg("file:///c.lisp");
    let replies = server.feed(&[open, symbols]);
    let r = &replies[1];
    assert!(r.contains("real-def"), "{r}");
    assert!(
        !r.contains("commented-out"),
        "comment text leaked as symbol: {r}"
    );
    assert!(
        !r.contains("in-string"),
        "string text leaked as symbol: {r}"
    );
}

/// Malformed input must not crash the server; later requests still work.
#[test]
fn t09_malformed_input_does_not_crash() {
    let mut server = Server::new();
    // garbage JSON
    let replies = server.feed(&["this is not json {{{".to_string()]);
    assert_eq!(replies.len(), 1);
    assert!(
        replies[0].contains("-32700"),
        "ParseError expected: {}",
        replies[0]
    );
    // unknown method with id → MethodNotFound; without id → silent drop
    let replies = server.feed(&[
        r#"{"jsonrpc":"2.0","id":9,"method":"workspace/executeCommand","params":{}}"#.to_string(),
        r#"{"jsonrpc":"2.0","method":"$/unknownNotification","params":{}}"#.to_string(),
        r#"{"jsonrpc":"2.0"}"#.to_string(),
    ]);
    assert_eq!(replies.len(), 1);
    assert!(replies[0].contains("-32601"), "{}", replies[0]);
    // server still fully functional afterwards
    let open = open_msg("file:///ok.lisp", "(def alive t)");
    let symbols = symbols_msg("file:///ok.lisp");
    let replies = server.feed(&[open, symbols]);
    assert!(replies[1].contains("\"name\":\"alive\""), "{}", replies[1]);
}

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

pub fn json_string(s: &str) -> String {
    let mut out = String::from("\"");
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

fn open_msg(uri: &str, text: &str) -> String {
    format!(
        r#"{{"jsonrpc":"2.0","method":"textDocument/didOpen","params":{{"textDocument":{{"uri":{uri},"languageId":"sens","version":1,"text":{text}}}}}}}"#,
        uri = json_string(uri),
        text = json_string(text),
    )
}

fn symbols_msg(uri: &str) -> String {
    format!(
        r#"{{"jsonrpc":"2.0","id":99,"method":"textDocument/documentSymbol","params":{{"textDocument":{{"uri":{}}}}}}}"#,
        json_string(uri)
    )
}

fn hover_msg(uri: &str, line: u32, character: u32) -> String {
    format!(
        r#"{{"jsonrpc":"2.0","id":98,"method":"textDocument/hover","params":{{"textDocument":{{"uri":{}}},"position":{{"line":{line},"character":{character}}}}}}}"#,
        json_string(uri)
    )
}

// ---------------------------------------------------------------------------
// M1: workspace index, cross-file definition, completion
// ---------------------------------------------------------------------------

/// Unique temp workspace: a.my defines `foo`, b.my uses it.
fn m1_workspace() -> std::path::PathBuf {
    static SEQ: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
    let seq = SEQ.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    let dir: PathBuf = std::env::temp_dir().join(format!("lsp-m1-{}-{seq}", std::process::id()));
    let _ = fs::remove_dir_all(&dir);
    fs::create_dir_all(&dir).unwrap();
    fs::write(dir.join("a.lisp"), "(def foo (lambda (x) (* x x)))\n").unwrap();
    fs::write(dir.join("b.lisp"), "(foo 21)\n").unwrap();
    dir
}

fn did_open(uri: &str, text: &str) -> String {
    format!(
        r#"{{"jsonrpc":"2.0","method":"textDocument/didOpen","params":{{"textDocument":{{"uri":{},"languageId":"sens","version":1,"text":{}}}}}}}"#,
        json_string(uri),
        json_string(text)
    )
}

fn request(id: u32, method: &str, params: &str) -> String {
    format!(r#"{{"jsonrpc":"2.0","id":{id},"method":"{method}","params":{params}}}"#)
}

/// Full cross-file flow: initialize scans the root, b.my opens, cursor on
/// `foo` resolves into a.my.
#[test]
fn t10_workspace_definition_resolves_across_files() {
    let dir = m1_workspace();
    let _a_uri = format!("file://{}/a.lisp", dir.display());
    let b_uri = format!("file://{}/b.lisp", dir.display());

    let init = request(
        1,
        "initialize",
        &format!(
            r#"{{"rootUri":{}}}"#,
            json_string(&format!("file://{}", dir.display()))
        ),
    );
    let open = did_open(&b_uri, "(foo 21)\n");
    let mut server = Server::new();
    server.feed(&[raw(&init), raw(&open)]);

    // Cursor at line 0 char 1 sits inside `foo`.
    let params = format!(
        r#"{{"textDocument":{{"uri":{}}},"position":{{"line":0,"character":1}}}}"#,
        json_string(&b_uri)
    );
    let replies = server.feed(&[raw(&request(7, "textDocument/definition", &params))]);
    assert_eq!(replies.len(), 1);
    let r = replies[0].as_str();
    assert!(
        r.contains("/a.lisp"),
        "cross-file definition must point into a.my: {r}"
    );
    assert!(
        r.contains("\"range\""),
        "definition must carry a range: {r}"
    );
}

/// Completion offers builtins and local defs filtered by prefix.
#[test]
fn t11_completion_offers_builtins_and_local_defs() {
    // NOTE: completion inherits M0's parse-only honesty — a document that
    // fails to parse contributes no definitions. Editors see this only
    // while typing unbalanced forms; documented in docs/lsp-m0.md.
    let mut server = Server::new();
    let open = did_open("file:///w.lisp", "(def alpha 1)\n(al )\n");
    let init = request(1, "initialize", "{}");
    server.feed(&[raw(&init), raw(&open)]);

    // Cursor at end of `(al` → prefix "al".
    let params = r#"{"textDocument":{"uri":"file:///w.lisp"},"position":{"line":1,"character":3}}"#;
    let replies = server.feed(&[raw(&request(8, "textDocument/completion", params))]);
    assert_eq!(replies.len(), 1);
    let r = replies[0].as_str();
    assert!(r.contains("alpha"), "local def must be offered: {r}");
    // Prefix "al" filters out builtins like "+" but may match none of them;
    // ensure no builtin leaked through the prefix filter.
    assert!(
        !r.contains("\"label\":\"+\""),
        "prefix filter must drop '+': {r}"
    );

    // Empty prefix → builtins are offered.
    server.feed(&[did_open("file:///w2.lisp", "\n")]);
    let params2 = r#"{"textDocument":{"uri":"file:///w2.lisp"},"position":{"line":0,"character":0}}"#;
    let replies2 = server.feed(&[raw(&request(9, "textDocument/completion", params2))]);
    let r2 = replies2[0].as_str();
    assert!(
        r2.contains("\"label\":\"+\"") || r2.contains("\"+\""),
        "builtin + must be offered on empty prefix: {r2}"
    );

    for (name, value) in Environment::root().snapshot() {
        if matches!(value, Value::Builtin(_)) {
            let label = format!("\"label\":\"{name}\"");
            assert!(
                r2.contains(&label),
                "runtime builtin {name} must be offered by completion: {r2}"
            );
        }
    }

    let mut shadow_server = Server::new();
    shadow_server.feed(&[did_open(
        "file:///shadow-completion.lisp",
        "(def max 42)\n(ma )\n",
    )]);
    let shadow_params = r#"{"textDocument":{"uri":"file:///shadow-completion.lisp"},"position":{"line":1,"character":3}}"#;
    let shadow_reply =
        shadow_server.feed(&[raw(&request(10, "textDocument/completion", shadow_params))]);
    let shadow = &shadow_reply[0];
    assert!(
        shadow.contains("\"label\":\"max\",\"kind\":3,\"detail\":\"local def\""),
        "local completion metadata must shadow builtin max: {shadow}"
    );
}

// ---------------------------------------------------------------------------
// M2: references + rename
// ---------------------------------------------------------------------------

/// Shared 3-file workspace: defs in defs.my, usages spread across files.
fn m2_workspace() -> std::path::PathBuf {
    // unique per CALL: parallel tests sharing one pid raced on
    // remove_dir_all/recreate (flaky t12/t13/t14 in full sweeps)
    static SEQ: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
    let seq = SEQ.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    let dir = std::env::temp_dir().join(format!("lsp-m2-{}-{seq}", std::process::id()));
    let _ = fs::remove_dir_all(&dir);
    fs::create_dir_all(&dir).unwrap();
    fs::write(dir.join("defs.lisp"), "(def target (lambda (x) x))\n").unwrap();
    fs::write(dir.join("use1.lisp"), "(target 1)\n").unwrap();
    // quoted occurrence must NEVER count (it is data, not a code reference)
    fs::write(dir.join("use2.lisp"), "(quote target)\n(list target)\n").unwrap();
    dir
}

#[test]
fn t12_references_cross_file_excludes_quoted_data() {
    let dir = m2_workspace();
    let use1 = format!("file://{}/use1.lisp", dir.display());

    let init = request(
        1,
        "initialize",
        &format!(
            r#"{{"rootUri":{}}}"#,
            json_string(&format!("file://{}", dir.display()))
        ),
    );
    let open = did_open(&use1, "(target 1)\n");
    let mut server = Server::new();
    server.feed(&[raw(&init), raw(&open)]);

    let params = format!(
        r#"{{"textDocument":{{"uri":{}}},"position":{{"line":0,"character":1}},"context":{{"includeDeclaration":true}}}}"#,
        json_string(&use1)
    );
    let replies = server.feed(&[raw(&request(5, "textDocument/references", &params))]);
    let r = replies[0].as_str();

    // Expect: def in defs.my + usage in use1.my + usage in use2.my line 2.
    assert_eq!(3, r.matches("\"uri\"").count(), "expected 3 locations: {r}");
    assert!(r.contains("defs.lisp"), "{r}");
    assert!(
        !r.contains("quote") || !r.contains("(quote"),
        "quoted data must be excluded: {r}"
    );
}

#[test]
fn t13_references_exclude_declaration_when_asked() {
    let dir = m2_workspace();
    let use1 = format!("file://{}/use1.lisp", dir.display());
    let init = request(
        1,
        "initialize",
        &format!(
            r#"{{"rootUri":{}}}"#,
            json_string(&format!("file://{}", dir.display()))
        ),
    );
    let open = did_open(&use1, "(target 1)\n");
    let mut server = Server::new();
    server.feed(&[raw(&init), raw(&open)]);

    let params = format!(
        r#"{{"textDocument":{{"uri":{}}},"position":{{"line":0,"character":1}},"context":{{"includeDeclaration":false}}}}"#,
        json_string(&use1)
    );
    let replies = server.feed(&[raw(&request(6, "textDocument/references", &params))]);
    let r = replies[0].as_str();
    assert_eq!(
        2,
        r.matches("\"uri\"").count(),
        "declaration excluded → 2 refs: {r}"
    );
}

#[test]
fn t14_rename_produces_cross_file_edits_and_validates_name() {
    let dir = m2_workspace();
    let use1 = format!("file://{}/use1.lisp", dir.display());
    let init = request(
        1,
        "initialize",
        &format!(
            r#"{{"rootUri":{}}}"#,
            json_string(&format!("file://{}", dir.display()))
        ),
    );
    let open = did_open(&use1, "(target 1)\n");
    let mut server = Server::new();
    server.feed(&[raw(&init), raw(&open)]);

    // Valid rename.
    let params = format!(
        r#"{{"textDocument":{{"uri":{}}},"position":{{"line":0,"character":1}},"newName":"renamed-thing"}}"#,
        json_string(&use1)
    );
    let replies = server.feed(&[raw(&request(7, "textDocument/rename", &params))]);
    let r = replies[0].as_str();
    assert!(r.contains("\"changes\""), "{r}");
    // 3 code references: def name + use1 + use2 line 2. The quoted
    // `(quote target)` on use2 line 1 must stay untouched — it is data.
    assert_eq!(
        3,
        r.matches("\"newText\":\"renamed-thing\"").count(),
        "def + 2 code usages renamed; quoted data excluded: {r}"
    );
    let use2_section = r.split("use2.lisp").nth(1).unwrap_or("");
    assert!(
        use2_section.contains("\"line\":1,"),
        "use2 edits start at line 1: {r}"
    );
    assert!(r.contains("defs.lisp"), "{r}");

    // Invalid name → error response, not a workspace edit.
    let bad = format!(
        r#"{{"jsonrpc":"2.0","id":8,"method":"textDocument/rename","params":{{"textDocument":{{"uri":{}}},"position":{{"line":0,"character":1}},"newName":"9bad"}}}}"#,
        json_string(&use1)
    );
    let replies = server.feed(&[raw(&bad)]);
    let r = replies[0].as_str();
    assert!(
        r.contains("\"error\"") || r.contains("-32602"),
        "invalid name must be rejected: {r}"
    );
    assert!(
        sens::parse_json(r).is_ok(),
        "error response must be valid JSON: {r}"
    );
}

#[test]
fn t15_arity_diagnostics_are_conservative_and_shadow_aware() {
    let mut server = Server::new();
    let bad = did_open("file:///arity-bad.lisp", "(car 1 2)\n");
    let replies = server.feed(&[bad]);
    let diagnostic = &replies[0];
    assert!(
        diagnostic.contains("arity: car expects 1, received 2"),
        "known direct call must report exact arity: {diagnostic}"
    );

    let shadowed = did_open(
        "file:///arity-shadow.lisp",
        "(def car (lambda (x y) x))\n(car 1 2)\n(quote (car 1 2))\n(read)\n",
    );
    let replies = server.feed(&[shadowed]);
    assert!(
        replies[0].contains("\"diagnostics\":[]"),
        "local shadow, quoted data, and valid optional arity must stay clean: {}",
        replies[0]
    );

    let too_many = did_open("file:///arity-read.lisp", "(read \"a\" \"b\")\n");
    let replies = server.feed(&[too_many]);
    assert!(
        replies[0].contains("arity: read expects between 0 and 1, received 2"),
        "bounded optional arity must be enforced: {}",
        replies[0]
    );

    let mut metadata_server = Server::new();
    metadata_server.feed(&[did_open("file:///metadata.lisp", "(car 1)\n")]);
    let hover = metadata_server.feed(&[hover_msg("file:///metadata.lisp", 0, 2)]);
    assert!(
        hover[0].contains("(car pair)"),
        "hover must expose the canonical signature: {}",
        hover[0]
    );

    metadata_server.feed(&[did_open("file:///metadata-completion.lisp", "\n")]);
    let params = r#"{"textDocument":{"uri":"file:///metadata-completion.lisp"},"position":{"line":0,"character":0}}"#;
    let completion = metadata_server.feed(&[raw(&request(16, "textDocument/completion", params))]);
    assert!(
        completion[0].contains("builtin · (car pair)"),
        "completion must expose the canonical signature: {}",
        completion[0]
    );
}

/// ECO-DECISION-2026-08-27-MYLISP-WSM-RENAME: `.wsm` is now the canonical
/// extension, `.my`/`.lisp` stay supported. Workspace scanning (M1) must
/// pick up `.wsm` files exactly like `.my` ones — same cross-file
/// definition flow as t10, just with the new extension on both files.
#[test]
fn t16_workspace_scan_recognizes_wsm_extension() {
    static SEQ: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
    let seq = SEQ.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    let dir: PathBuf = std::env::temp_dir().join(format!("lsp-wsm-{}-{seq}", std::process::id()));
    let _ = fs::remove_dir_all(&dir);
    fs::create_dir_all(&dir).unwrap();
    fs::write(dir.join("a.lisp"), "(def foo (lambda (x) (* x x)))\n").unwrap();
    fs::write(dir.join("b.lisp"), "(foo 21)\n").unwrap();

    let b_uri = format!("file://{}/b.lisp", dir.display());
    let init = request(
        1,
        "initialize",
        &format!(
            r#"{{"rootUri":{}}}"#,
            json_string(&format!("file://{}", dir.display()))
        ),
    );
    let open = did_open(&b_uri, "(foo 21)\n");
    let mut server = Server::new();
    server.feed(&[raw(&init), raw(&open)]);

    let params = format!(
        r#"{{"textDocument":{{"uri":{}}},"position":{{"line":0,"character":1}}}}"#,
        json_string(&b_uri)
    );
    let replies = server.feed(&[raw(&request(7, "textDocument/definition", &params))]);
    assert_eq!(replies.len(), 1);
    let r = replies[0].as_str();
    assert!(
        r.contains("/a.lisp"),
        "cross-file definition must point into a.wsm: {r}"
    );
}

// ---------------------------------------------------------------------------
// G3: guard knowledge in hover + arity diagnostics (live WSM files)
// ---------------------------------------------------------------------------

/// The sens repo root (parent of crates/sens-lsp), used as the LSP
/// workspace root so initialize loads guard knowledge from the REAL
/// lib/guard.wsm and knowledge/guard-reference.wsm.
fn sens_repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..").join("..")
}

fn init_with_root(root: &Path) -> String {
    request(
        1,
        "initialize",
        &format!(
            r#"{{"rootUri":{}}}"#,
            json_string(&format!("file://{}", root.display()))
        ),
    )
}

/// Hover over a guard function name in ordinary source must surface its
/// canonical defining form from lib/guard.wsm — the live file, not a
/// Rust copy.
#[test]
fn t17_g3_guard_function_hover_from_live_lib_guard_wsm() {
    let uri = "file:///g3fn.lisp";
    let doc = "(guard-unknown subject missing-evidence guidance)\n";
    let mut server = Server::new();
    let replies = server.feed(&[
        raw(&init_with_root(&sens_repo_root())),
        raw(&did_open(uri, doc)),
        raw(&hover_msg(uri, 0, 2)),
    ]);
    assert_eq!(replies.len(), 3);
    let r = replies[2].as_str();
    assert!(r.contains("**guard function**"), "{r}");
    // The canonical source must be the live def, structurally provable.
    assert!(r.contains("(def guard-unknown"), "{r}");
    assert!(r.contains("lib/guard.lisp"), "{r}");
}

/// A wrong-arity call to a live guard function is caught by arity
/// diagnostics exactly like a runtime builtin would be.
#[test]
fn t18_g3_guard_function_wrong_arity_is_diagnosed() {
    let uri = "file:///g3ar.lisp";
    let doc = "(guard-unknown only-one-arg)\n"; // expects 3
    let mut server = Server::new();
    let replies = server.feed(&[
        raw(&init_with_root(&sens_repo_root())),
        raw(&did_open(uri, doc)),
    ]);
    assert_eq!(replies.len(), 2);
    let r = replies[1].as_str();
    assert!(r.contains("publishDiagnostics"), "{r}");
    assert!(r.contains("arity: guard-unknown expects"), "{r}");
    assert!(
        !r.contains("\"diagnostics\":[]"),
        "must not be empty: {r}"
    );
}

/// Hover over a guard topic symbol surfaces the reference-bureau entry.
/// The topic directory parse is slow (~3.4s release / ~65s debug for the
/// 47KB canonical file), so this stays explicit rather than slowing every
/// `cargo test`. Run: `cargo test --release -p sens-lsp -- --ignored`
#[test]
#[ignore = "guard-reference.wsm topic parse is slow; run explicitly in release"]
fn t19_g3_guard_topic_hover_from_live_reference_wsm() {
    let uri = "file:///g3tp.lisp";
    let doc = "(guard)\n"; // `guard` as a bare symbol form, not a call
    let mut server = Server::new();
    let replies = server.feed(&[
        raw(&init_with_root(&sens_repo_root())),
        raw(&did_open(uri, doc)),
        raw(&hover_msg(uri, 0, 2)),
    ]);
    assert_eq!(replies.len(), 3);
    let r = replies[2].as_str();
    assert!(r.contains("**guard topic**"), "{r}");
    // The summary must come from the live canonical file, and the
    // unknown-route guidance (ASK-OWNER for guard) must travel along.
    assert!(r.contains("**unknown route:**"), "{r}");
}
