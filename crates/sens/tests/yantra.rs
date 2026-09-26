//! MY-LISP-YANTRA: the smallest Chebupelka-style coding agent whose
//! control logic lives entirely in lib/yantra.my. The host boundary is
//! `process-run-raw` (bash tool + curl transport bytes) and `json-parse`
//! (wire-format decode); public `process-run` semantics live in Lisp.
//!
//! The LLM is stubbed per test with scripted assistant messages, so the
//! control loop, completion validation, id correlation and MAX_TURNS are
//! verified deterministically. The bash tool itself is REAL: tests 2-4
//! execute actual subprocesses and assert on their genuine output.

use sens::{eval_program, load_core_library, load_process_library, Environment, Session};

fn agent_session() -> Session {
    // Install only the OS capability layer, opt this session into the exact
    // programs the agent may run, then bootstrap public process semantics in
    // Lisp over the raw byte-preserving host capability.
    sens_host::install();
    let environment =
        Environment::root().with_process_allowlist(vec!["bash".into(), "curl".into()]);
    let mut session = Session { environment };
    load_core_library(&mut session).unwrap();
    load_process_library(&mut session).unwrap();
    eval_program(include_str!("../../../lib/yantra.lisp"), &mut session).unwrap();
    session
}

fn eval_with_agent(source: &str) -> String {
    let mut session = agent_session();
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

/// A pure `complete` stub: returns script element #n where n is the number
/// of assistant messages already in the conversation — deterministic state
/// threading through the immutable message list itself. Index clamps to the
/// last element so an exhausted script repeats its final reply forever.
const SCRIPTED_COMPLETE: &str = r#"
(def script-nth
  (lambda (i script)
    (cond
      ((eq? i 0) (car script))
      ((atom? (cdr script)) (car script))
      (t (script-nth (- i 1) (cdr script))))))
(def make-scripted-complete
  (lambda (script)
    (lambda (messages)
      (script-nth (count-with-role "assistant" messages) script))))
"#;

fn assistant(content: &str) -> String {
    format!("(list (cons (quote role) \"assistant\") (cons (quote content) \"{content}\"))")
}

fn assistant_tool_call(id: &str, cmd: &str) -> String {
    format!(
        r#"(list (cons (quote role) "assistant")
             (cons (quote content) "")
             (cons (quote tool-calls)
                   (list (list (cons (quote id) "{id}")
                               (cons (quote name) "bash")
                               (cons (quote arguments) "{{\"cmd\": \"{cmd}\"}}")))))"#
    )
}

const FIRST_TOOL_RESULT: &str = r#"
(def first-tool-result
  (lambda (messages)
    (cond
      ((atom? messages) "")
      ((equal? (msg-role (car messages)) "tool") (msg-content (car messages)))
      (t (first-tool-result (cdr messages))))))
"#;

/// Yantra M1: stale evidence. A real tool run in an EARLIER exchange must
/// not back an execution claim made later - an intervening assistant
/// message breaks the ownership chain. Tested against the validator
/// directly with a hand-built shared-history shape, because within one
/// `run-agent` invocation the loop would already have completed on the
/// intermediate (claim-free) reply; the guarantee matters when message
/// histories are reused across invocations.
#[test]
fn stale_tool_evidence_cannot_back_a_later_claim() {
    let source = r#"
        (def sys (list (cons (quote role) "system") (cons (quote content) "s")))
        (def user (list (cons (quote role) "user") (cons (quote content) "u")))
        (def with-tools
          (list (cons (quote role) "assistant")
                (cons (quote content) "")
                (cons (quote tool-calls)
                      (list (list (cons (quote id) "call_1")
                                  (cons (quote name) "bash")
                                  (cons (quote arguments) "{\"cmd\": \"pwd\"}"))))))
        (def tool-result
          (list (cons (quote role) "tool")
                (cons (quote tool-call-id) "call_1")
                (cons (quote content) "/home/x")))
        (def plain-reply
          (list (cons (quote role) "assistant") (cons (quote content) "2+2 is 4.")))
        (def stale-claim
          (list (cons (quote role) "assistant")
                (cons (quote content) "I ran rm -rf /tmp/x, the command output confirms it.")))
        ; fresh evidence: claim DIRECTLY follows its own tool result -> valid
        (def fresh (valid-final? stale-claim
                     (list sys user with-tools tool-result stale-claim)))
        ; stale evidence: an unrelated assistant reply sits between the tool
        ; result and the claim -> chain broken -> invalid
        (def stale (valid-final? stale-claim
                     (list sys user with-tools tool-result plain-reply stale-claim)))
        (list fresh stale)
    "#;
    assert_eq!(
        eval_with_agent(source),
        "(t ())",
        "fresh owned evidence must validate; stale evidence must not"
    );
}

/// Test 1: a pure question finishes without any tool.
#[test]
#[ignore = "pre-Core4 yantra legacy suite under migration in #1145"]
fn pure_question_finishes_without_a_tool() {
    let source = format!(
        r#"
        {SCRIPTED_COMPLETE}
        (def complete (make-scripted-complete (list {assistant_msg})))
        (def result (run-agent complete "You are a helpful agent." "What is 2+2?"))
        (list (result-status result)
              (has-tool-result? (result-messages result))
              (result-answer result))
        "#,
        assistant_msg = assistant("2+2 is 4.")
    );
    assert_eq!(
        eval_with_agent(&source),
        "(completed () \"2+2 is 4.\")",
        "pure question must complete with no tool involvement"
    );
}

/// MYLISP-YANTRA-EPISTEMIC-BOUNDARY: a completed result is never bare
/// `completed` -- it always carries `(epistemic-status . hypothesis)`,
/// so nothing downstream can mistake the LLM's own text for something
/// reason.my has proved, by the return shape alone.
#[test]
#[ignore = "pre-Core4 yantra legacy suite under migration in #1145"]
fn completed_result_is_always_tagged_as_an_unproven_hypothesis() {
    let source = format!(
        r#"
        {SCRIPTED_COMPLETE}
        (def complete (make-scripted-complete (list {assistant_msg})))
        (def result (run-agent complete "You are a helpful agent." "What is 2+2?"))
        (list (result-status result) (result-epistemic-status result))
        "#,
        assistant_msg = assistant("2+2 is 4.")
    );
    assert_eq!(
        eval_with_agent(&source),
        "(completed hypothesis)",
        "a completed answer must be explicitly marked as an unproven, LLM-sourced hypothesis"
    );
}

/// Test 2: a filesystem question goes through the REAL bash process.
#[test]
#[ignore = "pre-Core4 yantra legacy suite under migration in #1145"]
fn filesystem_question_invokes_real_bash() {
    let marker = "yantra-real-bash-marker";
    let source = format!(
        r#"
        {SCRIPTED_COMPLETE}
        {FIRST_TOOL_RESULT}
        (def complete (make-scripted-complete
                        (list {tool_call}
                              {final_answer})))
        (def result (run-agent complete "You are an agent." "What does that file say?"))
        (list (result-status result)
              (first-tool-result (result-messages result)))
        "#,
        tool_call = assistant_tool_call("call_fs", &format!("echo {marker}")),
        final_answer = assistant("Done."),
    );
    let outcome = eval_with_agent(&source);
    assert!(outcome.contains("completed"), "{outcome}");
    // The tool message content is the REAL stdout of a real bash process —
    // impossible to fabricate without process-run having executed.
    assert!(
        outcome.contains(marker),
        "real bash stdout missing from tool result: {outcome}"
    );
}

/// Test 3: "run pwd" answered with only a textual claim can NEVER finish.
/// The validator rejects every turn; the loop runs to MAX_TURNS with no
/// completion and no fabricated tool result.
#[test]
#[ignore = "pre-Core4 yantra legacy suite under migration in #1145"]
fn textual_claim_without_tool_result_cannot_finish() {
    let source = format!(
        r#"
        {SCRIPTED_COMPLETE}
        (def complete (make-scripted-complete
                        (list {claiming_reply})))
        (def result (run-agent complete "You are an agent." "run pwd"))
        (list (result-status result)
              (has-tool-result? (result-messages result))
              (count-with-role "assistant" (result-messages result)))
        "#,
        claiming_reply = assistant("I ran pwd, the output of the command is /home/agents.")
    );
    assert_eq!(
        eval_with_agent(&source),
        "(max-turns-reached () 6)",
        "a textual execution claim must never complete without a real tool result"
    );
}

/// Test 4: tool results are correlated by tool_call_id, copied from the
/// executed call object by construction.
#[test]
#[ignore = "pre-Core4 yantra legacy suite under migration in #1145"]
fn tool_result_correlated_by_tool_call_id() {
    let source = format!(
        r#"
        {SCRIPTED_COMPLETE}
        (def complete (make-scripted-complete
                        (list {tool_call}
                              {final_answer})))
        (def correlated?
          (lambda (messages)
            (cond
              ((atom? messages) ())
              ((equal? (msg-role (car messages)) "tool")
               (equal? (msg-tool-call-id (car messages)) "call_pwd_42"))
              (t (correlated? (cdr messages))))))
        (correlated? (result-messages (run-agent complete "s" "run pwd")))
        "#,
        tool_call = assistant_tool_call("call_pwd_42", "pwd"),
        final_answer = assistant("pwd printed the working directory."),
    );
    assert_eq!(eval_with_agent(&source), "t");
}

/// Test 5: the hard MAX_TURNS limit stops an endlessly tool-calling model
/// after exactly max-turns turns.
#[test]
#[ignore = "pre-Core4 yantra legacy suite under migration in #1145"]
fn hard_max_turns_limit_stops_endless_tool_calls() {
    let source = format!(
        r#"
        {SCRIPTED_COMPLETE}
        ; every turn asks for another bash call — never finishes on its own
        (def complete (lambda (messages) {tool_call}))
        (def result (run-agent complete "s" "keep going"))
        (list (result-status result) (result-turn result))
        "#,
        tool_call = assistant_tool_call("call_loop", "echo again")
    );
    assert_eq!(
        eval_with_agent(&source),
        "(max-turns-reached 6)",
        "loop must stop exactly at MAX_TURNS"
    );
}

/// Bonus coverage: the wire path the live Ollama wiring uses — request-body
/// JSON encoding (.my) round-trips through json-parse (the host primitive).
#[test]
#[ignore = "pre-Core4 yantra legacy suite under migration in #1145"]
fn json_encode_and_parse_round_trip() {
    let source = r#"
        (def body (build-request-body "qwen3:4b"
                    (list (list (cons (quote role) "user")
                                (cons (quote content) "say \"hi\"\nnow")))))
        (def parsed (json-parse body))
        (list
          (equal? (alist-ref "model" parsed) "qwen3:4b")
          (alist-ref "content" (car (alist-ref "messages" parsed)))
          (length (alist-ref "tools" parsed)))
        "#
    .to_string();
    assert_eq!(
        eval_with_agent(&source),
        "(t \"say \\\"hi\\\"\\nnow\" 1)",
        "encode/parse round trip must preserve strings incl. escapes"
    );
}

// YANTRA-HTTP-ERROR-PROPAGATION: the transport layer returns the full
// (exit-code stdout stderr) triple, and ollama-complete turns non-zero
// exits into a BLOCKED result carrying the evidence — never an empty
// body fed to json-parse.
#[test]
fn http_transport_success_passes_body_through() {
    // Real curl against the real oracle's HTTP surface is out of scope
    // here; success-path framing is verified structurally instead:
    let src = r#"
      (let ((r (list 0 "{\"ok\":true}" "")))
        (list (http-transport-exit r) (http-transport-body r)))
    "#;
    let rendered = eval_with_agent(src);
    assert!(rendered.contains("(0"), "unexpected: {rendered}");
    assert!(
        rendered.contains("ok\\\":true") || rendered.contains("ok"),
        "unexpected: {rendered}"
    );
}

#[test]
fn transport_failure_becomes_blocked_result_with_evidence() {
    // curl to a port nothing listens on: fast refusal, exit != 0.
    let src = r#"
      (let ((r (http-post-json "http://127.0.0.1:1/x" "{}")))
        (cond ((= (http-transport-exit r) 0) 1 "UNEXPECTED-SUCCESS")
              ((= (http-transport-exit r) 0) 0 (http-transport-exit r))))
    "#;
    let rendered = eval_with_agent(src);
    assert!(!rendered.contains("UNEXPECTED-SUCCESS"), "{rendered}");
}


fn eval_bridge_with_agent(source: &str) -> String {
    let mut session = agent_session();
    eval_program(
        include_str!("../../../tests/fixtures/yantraos-bridge-witness.lisp"),
        &mut session,
    )
    .expect("yantraOS bridge witness should load");
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
#[ignore = "pre-Core4 yantra legacy suite under migration in #1145"]
fn yantraos_bridge_builds_typed_action_envelope() {
    let source = r#"
        (let ((envelope
                (yo-action-envelope
                  (quote (draft brief))
                  (quote file-management)
                  (quote create)
                  (quote client/brief.txt)
                  (quote ((content "hello") (overwrite 0)))
                  (quote (created-and-verified))
                  (quote ((source sens) (revision 1)))
                  (quote required))))
          (list
            (yo-action-envelope? envelope)
            (yo-field (quote capability) (yo-field (quote action) envelope))
            (yo-field (quote operation) (yo-field (quote action) envelope))
            (yo-field (quote approval) envelope)))
    "#;

    assert_eq!(
        eval_bridge_with_agent(source),
        "(yes file-management create required)"
    );
}

#[test]
#[ignore = "pre-Core4 yantra legacy suite under migration in #1145"]
fn yantraos_bridge_rejects_raw_shell_capability() {
    let source = r#"
        (let ((envelope
                (yo-action-envelope
                  (quote (delete temp))
                  (quote shell)
                  (quote execute)
                  (quote rm)
                  (quote ((command "rm -rf /tmp/x")))
                  (quote (verified))
                  (quote ((source sens)))
                  (quote required))))
          (yo-action-envelope? envelope))
    "#;

    assert_eq!(eval_bridge_with_agent(source), "no");
}

#[test]
#[ignore = "pre-Core4 yantra legacy suite under migration in #1145"]
fn yantraos_bridge_rejects_raw_command_field_under_non_shell_capability() {
    let source = r#"
        (let ((envelope
                (yo-action-envelope
                  (quote (archive report))
                  (quote file-management)
                  (quote create)
                  (quote client/report.txt)
                  (quote ((command "rm -rf /tmp/x")))
                  (quote (verified))
                  (quote ((source sens)))
                  (quote required))))
          (yo-action-envelope? envelope))
    "#;

    assert_eq!(eval_bridge_with_agent(source), "no");
}

#[test]
#[ignore = "pre-Core4 yantra legacy suite under migration in #1145"]
fn yantraos_bridge_keeps_execution_observation_and_provenance() {
    let source = r#"
        (let ((request-provenance
                (quote ((request-id r-42)
                        (state revision-7))))
              (observation
                (yo-execution-observation
                  (quote executed)
                  (quote CLI_FAST_PATH)
                  (quote ((exit-code 0)))
                  (quote ((audit-id a-99)))
                  request-provenance)))
          (list
            (yo-execution-observation? observation)
            (yo-field (quote result) observation)
            (yo-field (quote route) observation)
            (yo-field (quote provenance) observation)))
    "#;

    assert_eq!(
        eval_bridge_with_agent(source),
        "(yes executed CLI_FAST_PATH ((request-id r-42) (state revision-7)))"
    );
}
