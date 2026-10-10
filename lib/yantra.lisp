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

(00001001 json-escape-char
  (00001000 (ch)
    (00000111
      ((00000011 ch "\"") "\\\"")
      ((00000011 ch "\\") "\\\\")
      ((00000011 ch "\n") "\\n")
      ((00000011 ch "\r") "\\r")
      ((00000011 ch "\t") "\\t")
      ((00000010 ()) ch))))

(00001001 json-escape-onto
  (00001000 (s acc)
    (00000111
      ((00111100 s) acc)
      ((00000010 ()) (json-escape-onto (01000000 s)
                           (00111010 acc (json-escape-char (00111111 s))))))))

(00001001 json-escape
  (00001000 (s) (json-escape-onto s "")))

; The kernel's string-append is strictly binary AND a special form, so it
; cannot be passed as a function value to reduce — fold over rest args
; directly instead. Derived here, no new primitive.
(00001001 strcat-onto
  (00001000 (items acc)
    (00000111
      
      ((00000010 items)  acc)
      ((00000010 ()) (strcat-onto (00000110 items) (00111010 acc (00000101 items)))))))

(00001001 strcat
  (00001000 args
    (strcat-onto args "")))

(00001001 json-encode-string
  (00001000 (s) (00111010 "\"" (00111010 (json-escape s) "\""))))

(00001001 json-encode-key
  (00001000 (k)
    (00000111
      ((00100011 k) (json-encode-string (01000010 k)))
      ((00000010 ()) (json-encode-string k)))))

; Objects are alists (lists of dotted pairs), arrays are proper lists.
; Disambiguation for this protocol's data: a list is an OBJECT iff its
; first element is a pair with an atomic key (an alist entry); arrays
; contain either scalars or nested structures (whose car is itself a
; pair). This survives nested-object values like ("cmd" . (("type" . ...))),
; which a naive "cdr of first entry is atom" test misclassifies as array.
(00001001 json-object?
  (00001000 (v)
    (00000111
      
      ((00000010 ()) (00000001 ()))
      
      ((00000010 (00000101 v))  (00000001 ()))
      
      ((00000010 (00000101 (00000101 v)))  t)
      )))

(00001001 json-encode-value
  (00001000 (v)
    (00000111
      
      ((00000010 v)  (00000111
         ((00000011 v t) "true")
         ((00000011 v (00000001 ())) "null")
         ((string-membership-helper v)
          
          (json-encode-string v))
         ((00000010 ()) (01001100 v))))
      ((json-object? v) (json-encode-object v))
      ((00000010 ()) (json-encode-array v)))))

(00001001 json-encode-object-entries
  (00001000 (entries acc)
    (00000111
      
      ((00000010 entries)  acc)
      ((00000010 ()) (10011100 ((entry (00000101 entries)))
           (json-encode-object-entries
            (00000110 entries)
            (strcat acc
                    (00000111 ((00111100 acc) "")
                          (1 ","))
                    (json-encode-key (00000101 entry))
                    ":"
                    (json-encode-value (00000110 entry)))))))))

(00001001 json-encode-object
  (00001000 (alist)
    (strcat "{" (json-encode-object-entries alist "") "}")))

(00001001 json-encode-array-items
  (00001000 (items acc)
    (00000111
      
      ((00000010 items)  acc)
      ((00000010 ()) (json-encode-array-items
          (00000110 items)
          (strcat acc
                  (00000111 ((00111100 acc) "")
                        (1 ","))
                  (json-encode-value (00000101 items))))))))

(00001001 json-encode-array
  (00001000 (items)
    (strcat "[" (json-encode-array-items items "") "]")))

(00001001 json-encode json-encode-value)

; ---------------------------------------------------------------------------
; Message / tool-call accessors and JSON -> internal conversion
; ---------------------------------------------------------------------------

; Safe alist lookup: assoc returns () when the key is absent, and this
; kernel's cdr fails named on (), so every read goes through this guard.
; A genuinely absent key and an explicit nil value both read as () — the
; loop below only ever distinguishes present-nonempty from everything else.
(00001001 alist-ref
  (00001000 (key alist)
    (00000111
      ((00101101 key alist) (00000110 (00101101 key alist)))
      )))

(00001001 msg-role (00001000 (m) (alist-ref (00000001 role) m)))
(00001001 msg-content (00001000 (m) (alist-ref (00000001 content) m)))
(00001001 msg-tool-calls (00001000 (m) (alist-ref (00000001 tool-calls) m)))
(00001001 msg-tool-call-id (00001000 (m) (alist-ref (00000001 tool-call-id) m)))

(00001001 tc-id (00001000 (tc) (alist-ref (00000001 id) tc)))
(00001001 tc-name (00001000 (tc) (alist-ref (00000001 name) tc)))
(00001001 tc-arguments (00001000 (tc) (alist-ref (00000001 arguments) tc)))

; OpenAI's content field is null when the assistant emits only tool calls.
(00001001 json-message-content
  (00001000 (jm)
    (10011100 ((c (alist-ref "content" jm)))
      (00000111
        ((00000011 c (00000001 ())) "")
        ((00000010 ()) c)))))

(00001001 json->tool-call
  (00001000 (jtc)
    (10011100 ((fn (alist-ref "function" jtc)))
      (00100111 (00000100 (00000001 id) (alist-ref "id" jtc))
            (00000100 (00000001 name) (alist-ref "name" fn))
            (00000100 (00000001 arguments) (alist-ref "arguments" fn))))))

(00001001 json->message
  (00001000 (jm)
    (10011100 ((tcs (alist-ref "tool_calls" jm)))
      (00101001 (00100111 (00000100 (00000001 role) (alist-ref "role" jm))
                    (00000100 (00000001 content) (json-message-content jm)))
              (00000111
                (tcs (00100111 (00000100 (00000001 tool-calls) (00110111 json->tool-call tcs))))
                )))))

(00001001 extract-assistant-message
  (00001000 (response-json)
    (10011101 ((choices (alist-ref "choices" response-json))
           (choice (00000101 choices)))
      (alist-ref "message" choice))))

; ---------------------------------------------------------------------------
; Request encoding (raw-data builders; one json-encode at the leaf)
; ---------------------------------------------------------------------------

(00001001 encode-tool-call
  (00001000 (tc)
    (00100111 (00000100 "id" (tc-id tc))
          (00000100 "type" "function")
          (00000100 "function" (00100111 (00000100 "name" (tc-name tc))
                                 (00000100 "arguments" (tc-arguments tc)))))))

(00001001 encode-message
  (00001000 (m)
    (00000111
      ((00100010 (msg-role m) "tool")
       (00100111 (00000100 "role" "tool")
             (00000100 "tool_call_id" (msg-tool-call-id m))
             (00000100 "content" (msg-content m))))
      ((00000010 ()) (10011100 ((tcs (msg-tool-calls m)))
           (00101001 (00100111 (00000100 "role" (msg-role m))
                         (00000100 "content" (msg-content m)))
                   (00000111 (tcs (00100111 (00000100 "tool_calls" (00110111 encode-tool-call tcs))))
                         )))))))

(00001001 bash-tool-schema
  (00001000 ()
    (00100111 (00000100 "type" "function")
          (00000100 "function"
                (00100111 (00000100 "name" "bash")
                      (00000100 "description" "Run one bash command; returns combined stdout and stderr.")
                      (00000100 "parameters"
                            (00100111 (00000100 "type" "object")
                                  (00000100 "properties"
                                        (00100111 (00000100 "cmd" (00100111 (00000100 "type" "string")
                                                                (00000100 "description" "The bash command to execute")))))
                                  (00000100 "required" (00100111 "cmd")))))))))

(00001001 build-request-body
  (00001000 (model messages)
    (json-encode
     (00100111 (00000100 "model" model)
           (00000100 "messages" (00110111 encode-message messages))
           (00000100 "tools" (00100111 (bash-tool-schema)))))))

; ---------------------------------------------------------------------------
; Host transport: HTTP POST via the existing allowlisted process-run +
; curl. Zero new Rust beyond json-parse; swap this one function if a
; native http-post primitive is ever adopted.
; ---------------------------------------------------------------------------

(00001001 http-post-json
  (00001000 (url body)
    ;; --fail: non-2xx yields non-zero exit instead of an error body that
    ;; would be fed to json-parse; --max-time: never hang the agent loop
    ;; on a stuck server; --show-error keeps the reason on stderr.
    ;; FIX YANTRA-HTTP-ERROR-PROPAGATION: the curl exit code used to be
    ;; dropped here (stdout-only), so a failed request surfaced as an
    ;; opaque json-parse("") crash downstream — the same evidence-losing
    ;; class already fixed in execute-bash. The full triple now flows to
    ;; ollama-complete, which decides.
    (10011100 ((result (10100010 "curl"
                               (00100111 "-s" "-S" "--fail" "--show-error"
                                     "--max-time" "120"
                                     "-X" "POST"
                                     "-H" "Content-Type: application/json"
                                     "-d" body url))))
      (00100111 (00101011 0 result) (00101011 1 result) (00101011 2 result)))))

;; Transport result contract: (exit-code stdout stderr). Exit 0 = body is
;; the JSON payload; anything else = a BLOCKED result per the unknown-
;; result semantics (lib/result-status.lisp convention, mirrored here so
;; yantra stays standalone): (blocked "curl exit N[\\nstderr]"). Callers
;; must branch on this — feeding a blocked result to json-parse was the
;; original bug.
(00001001 http-transport-exit (00001000 (r) (00000101 r)))
(00001001 http-transport-body (00001000 (r) (00000101 (00000110 r))))
(00001001 http-transport-stderr (00001000 (r) (00000101 (00000110 (00000110 r)))))

; ---------------------------------------------------------------------------
; Tool dispatch — one tool: bash. Real execution only.
; ---------------------------------------------------------------------------

; The tool result is structured: the exit status is evidence, not a
; detail to drop - a command that failed with 127 must not read the same
; as one that succeeded. Text shape stays LLM-friendly.
(00001001 execute-bash
  (00001000 (arguments-json)
    (10011101 ((args (10100000 arguments-json))
           (cmd (alist-ref "cmd" args))
           (result (10100010 "bash" (00100111 "-c" cmd)))
           (exit-code (00101011 0 result))
           (stdout (00101011 1 result))
           (stderr (00101011 2 result)))
      (strcat "[exit-code " (01000110 exit-code)
              "]\n"
              stdout
              (00000111 ((00111100 stderr) "")
                    ((00000010 ()) (strcat "\n[stderr]\n" stderr)))))))

; number->string-nonneg removed: core.lisp's number->string now renders
; every number canonically (FIX-NUMBER-TO-STRING-RATIONAL), so the shim
; duplicated it — including the killed-by-signal negative case.

(00001001 dispatch-tool
  (00001000 (name arguments-json)
    (00000111
      ((00100010 name "bash") (execute-bash arguments-json))
      ((00000010 ()) (00111010 "error: unknown tool: " name)))))

(00001001 execute-tool-call
  (00001000 (tc)
    (dispatch-tool (tc-name tc) (tc-arguments tc))))

; Executes each tool call and produces the correlated tool-result
; messages — the tool_call_id on each result is copied from the very
; call object being executed, so correlation holds by construction.
(00001001 append-tool-results
  (00001000 (tcs acc)
    (00000111
      
      ((00000010 tcs)  acc)
      ((00000010 ()) (append-tool-results
          (00000110 tcs)
          (00101001 acc
                  (00100111 (00100111 (00000100 (00000001 role) "tool")
                              (00000100 (00000001 tool-call-id) (tc-id (00000101 tcs)))
                              (00000100 (00000001 content) (execute-tool-call (00000101 tcs)))))))))))

; ---------------------------------------------------------------------------
; Completion validation — the key rule.
; ---------------------------------------------------------------------------

(00001001 claim-markers
  (00000001 ("ran " "executed" "command output" "output of the command" "виконав" "виконано")))

(00001001 markers-contained?
  (00001000 (markers text)
    (00000111
      
      ((00000010 markers)  (00000001 ()))
      ((00111110 (00000101 markers) text) t)
      ((00000010 ()) (markers-contained? (00000110 markers) text)))))

(00001001 claims-execution?
  (00001000 (text) (markers-contained? claim-markers text)))


; Does the conversation contain any tool result at all? Coarse - kept
; for callers that only need existence; the claim validator below uses
; the stricter owned-evidence rule instead.
(00001001 has-tool-result?
  (00001000 (messages)
    (00000111
      
      ((00000010 messages)  (00000001 ()))
      ((00100010 (msg-role (00000101 messages)) "tool") t)
      ((00000010 ()) (has-tool-result? (00000110 messages))))))

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

(00001001 msg-call-ids
  (00001000 (m) (00110111 tc-id (msg-tool-calls m))))

(00001001 id-in-list?
  (00001000 (id ids)
    (00000111
      
      ((00000010 ids)  (00000001 ()))
      ((00100010 id (00000101 ids)) t)
      ((00000010 ()) (id-in-list? id (00000110 ids))))))

(00001001 all-covered?
  (00001000 (ids candidates)
    (00000111
      
      ((00000010 ids)  t)
      ((id-in-list? (00000101 ids) candidates) (all-covered? (00000110 ids) candidates))
      )))

; t iff everything BEFORE the final reply ends with
; [... assistant(tool-calls) tool* ] where every trailing tool result's
; id belongs to that assistant message. The final reply itself is dropped
; first - it is the message being validated, never its own evidence.
(00001001 ends-with-owned-tool-results?
  (00001000 (messages)
    (00000111
      
      ((00000010 messages)  (00000001 ()))
      ((00000010 ()) (collect-trailing-tools
          (00000110 (00101010 messages))
          (00000001 ()))))))

; walks backwards over a trailing run of tool results, then requires the
; assistant message that issued those calls to own every collected id
(00001001 collect-trailing-tools
  (00001000 (reversed collected)
    (00000111
      
      ((00000010 reversed)  (00000001 ()))
      ((00100010 (msg-role (00000101 reversed)) "tool")
       (collect-trailing-tools (00000110 reversed)
                               (00000100 (msg-tool-call-id (00000101 reversed)) collected)))
      ((00000010 ())
       (10011100 ((issuer (00000101 reversed)))
         (00000111
           ((00100001 (00100010 (msg-role issuer) "assistant")) (00000001 ()))
           
           ((00000010 (msg-tool-calls issuer))  (00000001 ()))
           ((00000010 ()) (all-covered? collected (msg-call-ids issuer)))))))))

; A turn may finish only if its text claims no execution - or if its
; execution claims are backed by tool results owned by this turn's own
; tool calls, directly preceding the reply.
(00001001 valid-final?
  (00001000 (assistant-msg messages)
    (00000111
      ((claims-execution? (msg-content assistant-msg))
       (ends-with-owned-tool-results? messages))
      ((00000010 ()) t))))

(00001001 invalid-completion-nudge
  (00100111 (00000100 (00000001 role) "system")
        (00000100 (00000001 content)
              "Your last reply claimed a command was executed, but no bash tool result exists in this conversation. A textual claim is not evidence of execution. Either call the bash tool for real, or reply without claiming execution.")))

; ---------------------------------------------------------------------------
; Turn loop — hard MAX_TURNS limit, threaded (immutable) agent state.
; ---------------------------------------------------------------------------

(00001001 max-turns 6)

(00001001 count-with-role
  (00001000 (role messages)
    (00000111
      
      ((00000010 messages)  0)
      ((00100010 (msg-role (00000101 messages)) role) (00001100 1 (count-with-role role (00000110 messages))))
      ((00000010 ()) (count-with-role role (00000110 messages))))))

(00001001 agent-loop
  (00001000 (complete messages turn)
    (00000111
      ((00011110 turn max-turns)
       (00100111 (00000100 (00000001 status) (00000001 max-turns-reached))
             (00000100 (00000001 turn) turn)
             (00000100 (00000001 messages) messages)))
      ((00000010 ())
       (10011101 ((assistant-msg (complete messages))
              (with-reply (00101001 messages (00100111 assistant-msg)))
              (tcs (msg-tool-calls assistant-msg)))
         (00000111
           
           ((00000010 tcs)  (00000111
              ((valid-final? assistant-msg with-reply)
               (00100111 (00000100 (00000001 status) (00000001 completed))
                     (00000100 (00000001 epistemic-status) (00000001 hypothesis))
                     (00000100 (00000001 answer) (msg-content assistant-msg))
                     (00000100 (00000001 turn) turn)
                     (00000100 (00000001 messages) with-reply)))
              ((00000010 ()) (agent-loop complete
                             (00101001 with-reply (00100111 invalid-completion-nudge))
                             (00001100 turn 1)))))
           ((00000010 ()) (agent-loop complete
                          (00101001 with-reply (append-tool-results tcs (00000001 ())))
                          (00001100 turn 1)))))))))

(00001001 run-agent
  (00001000 (complete system-prompt user-prompt)
    (agent-loop complete
                (00100111 (00100111 (00000100 (00000001 role) "system") (00000100 (00000001 content) system-prompt))
                      (00100111 (00000100 (00000001 role) "user") (00000100 (00000001 content) user-prompt)))
                0)))

; Result readers
(00001001 result-status (00001000 (r) (alist-ref (00000001 status) r)))
(00001001 result-epistemic-status (00001000 (r) (alist-ref (00000001 epistemic-status) r)))
(00001001 result-answer (00001000 (r) (alist-ref (00000001 answer) r)))
(00001001 result-turn (00001000 (r) (alist-ref (00000001 turn) r)))
(00001001 result-messages (00001000 (r) (alist-ref (00000001 messages) r)))

; ---------------------------------------------------------------------------
; Live Ollama wiring — used only against a running server; tests inject
; their own `complete` so the control logic above is verified
; deterministically regardless of provider availability.
; ---------------------------------------------------------------------------

(00001001 ollama-url "http://127.0.0.1:11434/v1/chat/completions")
(00001001 ollama-model "qwen3:4b")

(00001001 ollama-complete
  (00001000 (messages)
    (10011100 ((r (http-post-json ollama-url
                             (build-request-body ollama-model messages))))
      (00000111 ((00011100 (http-transport-exit r) 0) 
             (json->message
              (extract-assistant-message
               (10100000 (http-transport-body r)))))
            ((0100 (00011100 (http-transport-exit r) 0))
            ; Non-zero curl exit: a BLOCKED result (result-status.lisp
            ;; convention) carrying the evidence — never an empty body
            ;; fed to json-parse.
            (t (00100111 'blocked
                     (00111010 "curl exit "
                                    (01000110 (http-transport-exit r))
                                    (10011100 ((e (http-transport-stderr r)))
                                      (00000111 ((00111100 e) "")
                                            ((00000010 ()) (00111010 "\n" e))))))))))))
