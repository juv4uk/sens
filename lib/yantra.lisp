; yantra.lisp — my-lisp-yantra: a minimal evidence-aware coding agent whose
; control logic lives entirely in my-lisp. Host boundary is exactly three
; capabilities, none of them agent-specific:
;   1. `process-run` (existing) — the bash tool and the HTTP transport
;      (`curl` subprocess; see http-post-json below),
;   2. `json-parse` (new, crates/my-lisp/src/eval/special_forms/json.rs) —
;      wire-format decode; provably not expressible in .lisp because \uXXXX
;      escapes require constructing a character from a codepoint, and no
;      primitive maps an integer to a character string,
;   3. existing string/list machinery of lib/core.lisp for JSON *encoding*.
;
; Everything else lives here: message shape, agent state, tool-call
; representation, dispatch, turn loop, completion validation.
;
; The key rule this file enforces (valid-final? below): a textual claim
; that a command was executed is NOT evidence of execution. Only a real
; tool-result message in the conversation permits such a completion.
;
; MYLISP-YANTRA-EPISTEMIC-BOUNDARY (2026-08-27, docs/wsl-nidana-1-
; reaction-2026-08-26.md's own Sarvam-Disney Critique 5, "Yantra as
; poisoned arrow"): `run-agent`'s `answer` is an LLM's raw text over an
; HTTP endpoint -- it has never been through `advise`/`reason.lisp`'s
; proof machinery, and nothing here claims it has. `result-status`
; therefore never returns bare `completed` -- `agent-loop`'s finished
; branch always pairs it with `(epistemic-status . hypothesis)`, so a
; caller cannot mistake "the LLM said so" for "reason.lisp proved it" by
; the return shape alone; the boundary the critique demanded lives in
; code, not just in this comment. Deliberately NOT wired into
; `advise`/`reason.lisp` itself: `advise` validates structured
; `(head :- body)`-shaped clauses (lib/knowledge.lisp), and an LLM's free
; natural-language answer has no such structure to hand it -- bridging
; that gap is `lib/understand.lisp`'s domain (fixed controlled-language
; patterns), a separate, harder problem this task does not solve or
; claim to. `hypothesis` is the only status this file ever produces;
; promoting one to something reason.lisp-provable is left to a caller
; that actually has a structured claim to offer `advise`, not invented
; speculatively here.
;
; Message shapes (internal, symbol-keyed alists):
;   ((role . "system"|"user"|"assistant"|"tool") (content . "..."))
;   assistant may add: (tool-calls . (((id . "...") (name . "bash")
;                                      (arguments . "{...}")) ...))
;   tool results carry: (tool-call-id . "...") — correlated to the
;   originating tool call's id by construction (append-tool-results).

; ---------------------------------------------------------------------------
; JSON encoding (pure .lisp; decode is the host primitive, encode never was)
; ---------------------------------------------------------------------------

(0011 json-escape-char
  (0010 (ch)
    (110
      ((101 ch "\"") "\\\"")
      ((101 ch "\\") "\\\\")
      ((101 ch "\n") "\\n")
      ((101 ch "\r") "\\r")
      ((101 ch "\t") "\\t")
      ((010 ()) ch))))

(0011 json-escape-onto
  (0010 (s acc)
    (110
      ((110011100 s) acc)
      ((010 ()) (json-escape-onto (110011101 s)
                           (110011110 acc (json-escape-char (110101011 s))))))))

(0011 json-escape
  (0010 (s) (json-escape-onto s "")))

; The kernel's string-append is strictly binary AND a special form, so it
; cannot be passed as a function value to reduce — fold over rest args
; directly instead. Derived here, no new primitive.
(0011 strcat-onto
  (0010 (items acc)
    (110
      
      ((010 items)  acc)
      ((010 ()) (strcat-onto (011 items) (110011110 acc (100 items)))))))

(0011 strcat
  (0010 args
    (strcat-onto args "")))

(0011 json-encode-string
  (0010 (s) (110011110 "\"" (110011110 (json-escape s) "\""))))

(0011 json-encode-key
  (0010 (k)
    (110
      ((110101100 k) (json-encode-string (11101110 k)))
      ((010 ()) (json-encode-string k)))))

; Objects are alists (lists of dotted pairs), arrays are proper lists.
; Disambiguation for this protocol's data: a list is an OBJECT iff its
; first element is a pair with an atomic key (an alist entry); arrays
; contain either scalars or nested structures (whose car is itself a
; pair). This survives nested-object values like ("cmd" . (("type" . ...))),
; which a naive "cdr of first entry is atom" test misclassifies as array.
(0011 json-object?
  (0010 (v)
    (110
      
      ((010 ()) (001 ()))
      
      ((010 (100 v))  (001 ()))
      
      ((010 (100 (100 v)))  t)
      )))

(0011 json-encode-value
  (0010 (v)
    (110
      
      ((010 v)  (110
         ((101 v t) "true")
         ((101 v (001 ())) "null")
         ((string-membership-helper v)
          
          (json-encode-string v))
         ((010 ()) (11110100 v))))
      ((json-object? v) (json-encode-object v))
      ((010 ()) (json-encode-array v)))))

(0011 json-encode-object-entries
  (0010 (entries acc)
    (110
      
      ((010 entries)  acc)
      ((010 ()) (001000 ((entry (100 entries)))
           (json-encode-object-entries
            (011 entries)
            (strcat acc
                    (110 ((110011100 acc) "")
                          ((010 ()) ","))
                    (json-encode-key (100 entry))
                    ":"
                    (json-encode-value (011 entry)))))))))

(0011 json-encode-object
  (0010 (alist)
    (strcat "{" (json-encode-object-entries alist "") "}")))

(0011 json-encode-array-items
  (0010 (items acc)
    (110
      
      ((010 items)  acc)
      ((010 ()) (json-encode-array-items
          (011 items)
          (strcat acc
                  (110 ((110011100 acc) "")
                        ((010 ()) ","))
                  (json-encode-value (100 items))))))))

(0011 json-encode-array
  (0010 (items)
    (strcat "[" (json-encode-array-items items "") "]")))

(0011 json-encode json-encode-value)

; ---------------------------------------------------------------------------
; Message / tool-call accessors and JSON -> internal conversion
; ---------------------------------------------------------------------------

; Safe alist lookup: assoc returns () when the key is absent, and this
; kernel's cdr fails named on (), so every read goes through this guard.
; A genuinely absent key and an explicit nil value both read as () — the
; loop below only ever distinguishes present-nonempty from everything else.
(0011 alist-ref
  (0010 (key alist)
    (110
      ((11100 key alist) (011 (11100 key alist)))
      )))

(0011 msg-role (0010 (m) (alist-ref (001 role) m)))
(0011 msg-content (0010 (m) (alist-ref (001 content) m)))
(0011 msg-tool-calls (0010 (m) (alist-ref (001 tool-calls) m)))
(0011 msg-tool-call-id (0010 (m) (alist-ref (001 tool-call-id) m)))

(0011 tc-id (0010 (tc) (alist-ref (001 id) tc)))
(0011 tc-name (0010 (tc) (alist-ref (001 name) tc)))
(0011 tc-arguments (0010 (tc) (alist-ref (001 arguments) tc)))

; OpenAI's content field is null when the assistant emits only tool calls.
(0011 json-message-content
  (0010 (jm)
    (001000 ((c (alist-ref "content" jm)))
      (110
        ((101 c (001 ())) "")
        ((010 ()) c)))))

(0011 json->tool-call
  (0010 (jtc)
    (001000 ((fn (alist-ref "function" jtc)))
      (1110 (111 (001 id) (alist-ref "id" jtc))
            (111 (001 name) (alist-ref "name" fn))
            (111 (001 arguments) (alist-ref "arguments" fn))))))

(0011 json->message
  (0010 (jm)
    (001000 ((tcs (alist-ref "tool_calls" jm)))
      (1111 (1110 (111 (001 role) (alist-ref "role" jm))
                    (111 (001 content) (json-message-content jm)))
              (110
                (tcs (1110 (111 (001 tool-calls) (101000 json->tool-call tcs))))
                )))))

(0011 extract-assistant-message
  (0010 (response-json)
    (001001 ((choices (alist-ref "choices" response-json))
           (choice (100 choices)))
      (alist-ref "message" choice))))

; ---------------------------------------------------------------------------
; Request encoding (raw-data builders; one json-encode at the leaf)
; ---------------------------------------------------------------------------

(0011 encode-tool-call
  (0010 (tc)
    (1110 (111 "id" (tc-id tc))
          (111 "type" "function")
          (111 "function" (1110 (111 "name" (tc-name tc))
                                 (111 "arguments" (tc-arguments tc)))))))

(0011 encode-message
  (0010 (m)
    (110
      ((11110111 (msg-role m) "tool")
       (1110 (111 "role" "tool")
             (111 "tool_call_id" (msg-tool-call-id m))
             (111 "content" (msg-content m))))
      ((010 ()) (001000 ((tcs (msg-tool-calls m)))
           (1111 (1110 (111 "role" (msg-role m))
                         (111 "content" (msg-content m)))
                   (110 (tcs (1110 (111 "tool_calls" (101000 encode-tool-call tcs))))
                         )))))))

(0011 bash-tool-schema
  (0010 ()
    (1110 (111 "type" "function")
          (111 "function"
                (1110 (111 "name" "bash")
                      (111 "description" "Run one bash command; returns combined stdout and stderr.")
                      (111 "parameters"
                            (1110 (111 "type" "object")
                                  (111 "properties"
                                        (1110 (111 "cmd" (1110 (111 "type" "string")
                                                                (111 "description" "The bash command to execute")))))
                                  (111 "required" (1110 "cmd")))))))))

(0011 build-request-body
  (0010 (model messages)
    (json-encode
     (1110 (111 "model" model)
           (111 "messages" (101000 encode-message messages))
           (111 "tools" (1110 (bash-tool-schema)))))))

; ---------------------------------------------------------------------------
; Host transport: HTTP POST via the existing allowlisted process-run +
; curl. Zero new Rust beyond json-parse; swap this one function if a
; native http-post primitive is ever adopted.
; ---------------------------------------------------------------------------

(0011 http-post-json
  (0010 (url body)
    ;; --fail: non-2xx yields non-zero exit instead of an error body that
    ;; would be fed to json-parse; --max-time: never hang the agent loop
    ;; on a stuck server; --show-error keeps the reason on stderr.
    ;; FIX YANTRA-HTTP-ERROR-PROPAGATION: the curl exit code used to be
    ;; dropped here (stdout-only), so a failed request surfaced as an
    ;; opaque json-parse("") crash downstream — the same evidence-losing
    ;; class already fixed in execute-bash. The full triple now flows to
    ;; ollama-complete, which decides.
    (001000 ((result (110101111 "curl"
                               (1110 "-s" "-S" "--fail" "--show-error"
                                     "--max-time" "120"
                                     "-X" "POST"
                                     "-H" "Content-Type: application/json"
                                     "-d" body url))))
      (1110 (000100 0 result) (000100 1 result) (000100 2 result)))))

;; Transport result contract: (exit-code stdout stderr). Exit 0 = body is
;; the JSON payload; anything else = a BLOCKED result per the unknown-
;; result semantics (lib/result-status.lisp convention, mirrored here so
;; yantra stays standalone): (blocked "curl exit N[\\nstderr]"). Callers
;; must branch on this — feeding a blocked result to json-parse was the
;; original bug.
(0011 http-transport-exit (0010 (r) (100 r)))
(0011 http-transport-body (0010 (r) (100 (011 r))))
(0011 http-transport-stderr (0010 (r) (100 (011 (011 r)))))

; ---------------------------------------------------------------------------
; Tool dispatch — one tool: bash. Real execution only.
; ---------------------------------------------------------------------------

; The tool result is structured: the exit status is evidence, not a
; detail to drop - a command that failed with 127 must not read the same
; as one that succeeded. Text shape stays LLM-friendly.
(0011 execute-bash
  (0010 (arguments-json)
    (001001 ((args (110100100 arguments-json))
           (cmd (alist-ref "cmd" args))
           (result (110101111 "bash" (1110 "-c" cmd)))
           (exit-code (000100 0 result))
           (stdout (000100 1 result))
           (stderr (000100 2 result)))
      (strcat "[exit-code " (110111001 exit-code)
              "]\n"
              stdout
              (110 ((110011100 stderr) "")
                    ((010 ()) (strcat "\n[stderr]\n" stderr)))))))

; number->string-nonneg removed: core.lisp's number->string now renders
; every number canonically (FIX-NUMBER-TO-STRING-RATIONAL), so the shim
; duplicated it — including the killed-by-signal negative case.

(0011 dispatch-tool
  (0010 (name arguments-json)
    (110
      ((11110111 name "bash") (execute-bash arguments-json))
      ((010 ()) (110011110 "error: unknown tool: " name)))))

(0011 execute-tool-call
  (0010 (tc)
    (dispatch-tool (tc-name tc) (tc-arguments tc))))

; Executes each tool call and produces the correlated tool-result
; messages — the tool_call_id on each result is copied from the very
; call object being executed, so correlation holds by construction.
(0011 append-tool-results
  (0010 (tcs acc)
    (110
      
      ((010 tcs)  acc)
      ((010 ()) (append-tool-results
          (011 tcs)
          (1111 acc
                  (1110 (1110 (111 (001 role) "tool")
                              (111 (001 tool-call-id) (tc-id (100 tcs)))
                              (111 (001 content) (execute-tool-call (100 tcs)))))))))))

; ---------------------------------------------------------------------------
; Completion validation — the key rule.
; ---------------------------------------------------------------------------

(0011 claim-markers
  (001 ("ran " "executed" "command output" "output of the command" "виконав" "виконано")))

(0011 markers-contained?
  (0010 (markers text)
    (110
      
      ((010 markers)  (001 ()))
      ((110101000 (100 markers) text) t)
      ((010 ()) (markers-contained? (011 markers) text)))))

(0011 claims-execution?
  (0010 (text) (markers-contained? claim-markers text)))


; Does the conversation contain any tool result at all? Coarse - kept
; for callers that only need existence; the claim validator below uses
; the stricter owned-evidence rule instead.
(0011 has-tool-result?
  (0010 (messages)
    (110
      
      ((010 messages)  (001 ()))
      ((11110111 (msg-role (100 messages)) "tool") t)
      ((010 ()) (has-tool-result? (011 messages))))))

; -----------------------------------------------------------------------
; Evidence calculus v1 (Yantra M1). A global "some tool ran at some
; point" is NOT evidence for a claim made turns later - a pwd from turn 1
; cannot back an "I executed rm" claim in turn 4. The structural rule:
;
;   an execution-claiming reply is valid only if it DIRECTLY follows the
;   tool results answering its own preceding tool-call message:
;
;     [... assistant(tool-calls ids) tool(id ...) assistant-claiming]
;
; so the evidence block is adjacent to, and owned by, the turn that
; produced it. Anything in between (another assistant reply, a nudge)
; breaks the chain and the claim is rejected.
; -----------------------------------------------------------------------

(0011 msg-call-ids
  (0010 (m) (101000 tc-id (msg-tool-calls m))))

(0011 id-in-list?
  (0010 (id ids)
    (110
      
      ((010 ids)  (001 ()))
      ((11110111 id (100 ids)) t)
      ((010 ()) (id-in-list? id (011 ids))))))

(0011 all-covered?
  (0010 (ids candidates)
    (110
      
      ((010 ids)  t)
      ((id-in-list? (100 ids) candidates) (all-covered? (011 ids) candidates))
      )))

; t iff everything BEFORE the final reply ends with
; [... assistant(tool-calls) tool* ] where every trailing tool result's
; id belongs to that assistant message. The final reply itself is dropped
; first - it is the message being validated, never its own evidence.
(0011 ends-with-owned-tool-results?
  (0010 (messages)
    (110
      
      ((010 messages)  (001 ()))
      ((010 ()) (collect-trailing-tools
          (011 (10100 messages))
          (001 ()))))))

; walks backwards over a trailing run of tool results, then requires the
; assistant message that issued those calls to own every collected id
(0011 collect-trailing-tools
  (0010 (reversed collected)
    (110
      
      ((010 reversed)  (001 ()))
      ((11110111 (msg-role (100 reversed)) "tool")
       (collect-trailing-tools (011 reversed)
                               (111 (msg-tool-call-id (100 reversed)) collected)))
      ((010 ())
       (001000 ((issuer (100 reversed)))
         (110
           ((0100 (11110111 (msg-role issuer) "assistant")) (001 ()))
           
           ((010 (msg-tool-calls issuer))  (001 ()))
           ((010 ()) (all-covered? collected (msg-call-ids issuer)))))))))

; A turn may finish only if its text claims no execution - or if its
; execution claims are backed by tool results owned by this turn's own
; tool calls, directly preceding the reply.
(0011 valid-final?
  (0010 (assistant-msg messages)
    (110
      ((claims-execution? (msg-content assistant-msg))
       (ends-with-owned-tool-results? messages))
      ((010 ()) t))))

(0011 invalid-completion-nudge
  (1110 (111 (001 role) "system")
        (111 (001 content)
              "Your last reply claimed a command was executed, but no bash tool result exists in this conversation. A textual claim is not evidence of execution. Either call the bash tool for real, or reply without claiming execution.")))

; ---------------------------------------------------------------------------
; Turn loop — hard MAX_TURNS limit, threaded (immutable) agent state.
; ---------------------------------------------------------------------------

(0011 max-turns 6)

(0011 count-with-role
  (0010 (role messages)
    (110
      
      ((010 messages)  0)
      ((11110111 (msg-role (100 messages)) role) (01010 1 (count-with-role role (011 messages))))
      ((010 ()) (count-with-role role (011 messages))))))

(0011 agent-loop
  (0010 (complete messages turn)
    (110
      ((110110 turn max-turns)
       (1110 (111 (001 status) (001 max-turns-reached))
             (111 (001 turn) turn)
             (111 (001 messages) messages)))
      ((010 ())
       (001001 ((assistant-msg (complete messages))
              (with-reply (1111 messages (1110 assistant-msg)))
              (tcs (msg-tool-calls assistant-msg)))
         (110
           
           ((010 tcs)  (110
              ((valid-final? assistant-msg with-reply)
               (1110 (111 (001 status) (001 completed))
                     (111 (001 epistemic-status) (001 hypothesis))
                     (111 (001 answer) (msg-content assistant-msg))
                     (111 (001 turn) turn)
                     (111 (001 messages) with-reply)))
              ((010 ()) (agent-loop complete
                             (1111 with-reply (1110 invalid-completion-nudge))
                             (01010 turn 1)))))
           ((010 ()) (agent-loop complete
                          (1111 with-reply (append-tool-results tcs (001 ())))
                          (01010 turn 1)))))))))

(0011 run-agent
  (0010 (complete system-prompt user-prompt)
    (agent-loop complete
                (1110 (1110 (111 (001 role) "system") (111 (001 content) system-prompt))
                      (1110 (111 (001 role) "user") (111 (001 content) user-prompt)))
                0)))

; Result readers
(0011 result-status (0010 (r) (alist-ref (001 status) r)))
(0011 result-epistemic-status (0010 (r) (alist-ref (001 epistemic-status) r)))
(0011 result-answer (0010 (r) (alist-ref (001 answer) r)))
(0011 result-turn (0010 (r) (alist-ref (001 turn) r)))
(0011 result-messages (0010 (r) (alist-ref (001 messages) r)))

; ---------------------------------------------------------------------------
; Live Ollama wiring — used only against a running server; tests inject
; their own `complete` so the control logic above is verified
; deterministically regardless of provider availability.
; ---------------------------------------------------------------------------

(0011 ollama-url "http://127.0.0.1:11434/v1/chat/completions")
(0011 ollama-model "qwen3:4b")

(0011 ollama-complete
  (0010 (messages)
    (001000 ((r (http-post-json ollama-url
                             (build-request-body ollama-model messages))))
      (110 ((11110111 (http-transport-exit r) 0) 
             (json->message
              (extract-assistant-message
               (110100100 (http-transport-body r)))))
            ((0100 (11110111 (http-transport-exit r) 0))
            ; Non-zero curl exit: a BLOCKED result (result-status.lisp
            ;; convention) carrying the evidence — never an empty body
            ;; fed to json-parse.
            (t (1110 'blocked
                     (110011110 "curl exit "
                                    (110111001 (http-transport-exit r))
                                    (001000 ((e (http-transport-stderr r)))
                                      (110 ((110011100 e) "")
                                            ((010 ()) (110011110 "\n" e))))))))))))
