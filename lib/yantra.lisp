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

(def json-escape-char
  (lambda (ch)
    (cond
      ((eq? ch "\"") "\\\"")
      ((eq? ch "\\") "\\\\")
      ((eq? ch "\n") "\\n")
      ((eq? ch "\r") "\\r")
      ((eq? ch "\t") "\\t")
      (t ch))))

(def json-escape-onto
  (lambda (s acc)
    (cond
      ((string-empty? s) acc)
      (t (json-escape-onto (string-rest s)
                           (string-append acc (json-escape-char (string-first s))))))))

(def json-escape
  (lambda (s) (json-escape-onto s "")))

; The kernel's string-append is strictly binary AND a special form, so it
; cannot be passed as a function value to reduce — fold over rest args
; directly instead. Derived here, no new primitive.
(def strcat-onto
  (lambda (items acc)
    (cond
      ((atom? items) () acc)
      ((atom? items) (1) acc)
      (t (strcat-onto (cdr items) (string-append acc (car items)))))))

(def strcat
  (lambda args
    (strcat-onto args "")))

(def json-encode-string
  (lambda (s) (string-append "\"" (string-append (json-escape s) "\""))))

(def json-encode-key
  (lambda (k)
    (cond
      ((symbol? k) (json-encode-string (symbol->string k)))
      (t (json-encode-string k)))))

; Objects are alists (lists of dotted pairs), arrays are proper lists.
; Disambiguation for this protocol's data: a list is an OBJECT iff its
; first element is a pair with an atomic key (an alist entry); arrays
; contain either scalars or nested structures (whose car is itself a
; pair). This survives nested-object values like ("cmd" . (("type" . ...))),
; which a naive "cdr of first entry is atom" test misclassifies as array.
(def json-object?
  (lambda (v)
    (cond
      ((atom? v) () (quote ()))
      ((atom? v) (1) (quote ()))
      ((atom? (car v)) () (quote ()))
      ((atom? (car v)) (1) (quote ()))
      ((atom? (car (car v))) () t)
      ((atom? (car (car v))) (1) t)
      (t (quote ())))))

(def json-encode-value
  (lambda (v)
    (cond
      ((atom? v) () (cond
         ((eq? v t) "true")
         ((eq? v (quote ())) "null")
         ((string-membership-helper v)
          (class-membership string member)
          (json-encode-string v))
         (t (write-to-string v))))
      ((atom? v) (1) (cond
         ((eq? v t) "true")
         ((eq? v (quote ())) "null")
         ((string-membership-helper v)
          (class-membership string member)
          (json-encode-string v))
         (t (write-to-string v))))
      ((json-object? v) (json-encode-object v))
      (t (json-encode-array v)))))

(def json-encode-object-entries
  (lambda (entries acc)
    (cond
      ((atom? entries) () acc)
      ((atom? entries) (1) acc)
      (t (let ((entry (car entries)))
           (json-encode-object-entries
            (cdr entries)
            (strcat acc
                    (cond ((string-empty? acc) "")
                          (t ","))
                    (json-encode-key (car entry))
                    ":"
                    (json-encode-value (cdr entry)))))))))

(def json-encode-object
  (lambda (alist)
    (strcat "{" (json-encode-object-entries alist "") "}")))

(def json-encode-array-items
  (lambda (items acc)
    (cond
      ((atom? items) () acc)
      ((atom? items) (1) acc)
      (t (json-encode-array-items
          (cdr items)
          (strcat acc
                  (cond ((string-empty? acc) "")
                        (t ","))
                  (json-encode-value (car items))))))))

(def json-encode-array
  (lambda (items)
    (strcat "[" (json-encode-array-items items "") "]")))

(def json-encode json-encode-value)

; ---------------------------------------------------------------------------
; Message / tool-call accessors and JSON -> internal conversion
; ---------------------------------------------------------------------------

; Safe alist lookup: assoc returns () when the key is absent, and this
; kernel's cdr fails named on (), so every read goes through this guard.
; A genuinely absent key and an explicit nil value both read as () — the
; loop below only ever distinguishes present-nonempty from everything else.
(def alist-ref
  (lambda (key alist)
    (cond
      ((assoc key alist) (cdr (assoc key alist)))
      (t (quote ())))))

(def msg-role (lambda (m) (alist-ref (quote role) m)))
(def msg-content (lambda (m) (alist-ref (quote content) m)))
(def msg-tool-calls (lambda (m) (alist-ref (quote tool-calls) m)))
(def msg-tool-call-id (lambda (m) (alist-ref (quote tool-call-id) m)))

(def tc-id (lambda (tc) (alist-ref (quote id) tc)))
(def tc-name (lambda (tc) (alist-ref (quote name) tc)))
(def tc-arguments (lambda (tc) (alist-ref (quote arguments) tc)))

; OpenAI's content field is null when the assistant emits only tool calls.
(def json-message-content
  (lambda (jm)
    (let ((c (alist-ref "content" jm)))
      (cond
        ((eq? c (quote ())) "")
        (t c)))))

(def json->tool-call
  (lambda (jtc)
    (let ((fn (alist-ref "function" jtc)))
      (list (cons (quote id) (alist-ref "id" jtc))
            (cons (quote name) (alist-ref "name" fn))
            (cons (quote arguments) (alist-ref "arguments" fn))))))

(def json->message
  (lambda (jm)
    (let ((tcs (alist-ref "tool_calls" jm)))
      (append (list (cons (quote role) (alist-ref "role" jm))
                    (cons (quote content) (json-message-content jm)))
              (cond
                (tcs (list (cons (quote tool-calls) (map json->tool-call tcs))))
                (t (quote ())))))))

(def extract-assistant-message
  (lambda (response-json)
    (let* ((choices (alist-ref "choices" response-json))
           (choice (car choices)))
      (alist-ref "message" choice))))

; ---------------------------------------------------------------------------
; Request encoding (raw-data builders; one json-encode at the leaf)
; ---------------------------------------------------------------------------

(def encode-tool-call
  (lambda (tc)
    (list (cons "id" (tc-id tc))
          (cons "type" "function")
          (cons "function" (list (cons "name" (tc-name tc))
                                 (cons "arguments" (tc-arguments tc)))))))

(def encode-message
  (lambda (m)
    (cond
      ((equal? (msg-role m) "tool")
       (list (cons "role" "tool")
             (cons "tool_call_id" (msg-tool-call-id m))
             (cons "content" (msg-content m))))
      (t (let ((tcs (msg-tool-calls m)))
           (append (list (cons "role" (msg-role m))
                         (cons "content" (msg-content m)))
                   (cond (tcs (list (cons "tool_calls" (map encode-tool-call tcs))))
                         (t (quote ())))))))))

(def bash-tool-schema
  (lambda ()
    (list (cons "type" "function")
          (cons "function"
                (list (cons "name" "bash")
                      (cons "description" "Run one bash command; returns combined stdout and stderr.")
                      (cons "parameters"
                            (list (cons "type" "object")
                                  (cons "properties"
                                        (list (cons "cmd" (list (cons "type" "string")
                                                                (cons "description" "The bash command to execute")))))
                                  (cons "required" (list "cmd")))))))))

(def build-request-body
  (lambda (model messages)
    (json-encode
     (list (cons "model" model)
           (cons "messages" (map encode-message messages))
           (cons "tools" (list (bash-tool-schema)))))))

; ---------------------------------------------------------------------------
; Host transport: HTTP POST via the existing allowlisted process-run +
; curl. Zero new Rust beyond json-parse; swap this one function if a
; native http-post primitive is ever adopted.
; ---------------------------------------------------------------------------

(def http-post-json
  (lambda (url body)
    ;; --fail: non-2xx yields non-zero exit instead of an error body that
    ;; would be fed to json-parse; --max-time: never hang the agent loop
    ;; on a stuck server; --show-error keeps the reason on stderr.
    ;; FIX YANTRA-HTTP-ERROR-PROPAGATION: the curl exit code used to be
    ;; dropped here (stdout-only), so a failed request surfaced as an
    ;; opaque json-parse("") crash downstream — the same evidence-losing
    ;; class already fixed in execute-bash. The full triple now flows to
    ;; ollama-complete, which decides.
    (let ((result (process-run "curl"
                               (list "-s" "-S" "--fail" "--show-error"
                                     "--max-time" "120"
                                     "-X" "POST"
                                     "-H" "Content-Type: application/json"
                                     "-d" body url))))
      (list (nth 0 result) (nth 1 result) (nth 2 result)))))

;; Transport result contract: (exit-code stdout stderr). Exit 0 = body is
;; the JSON payload; anything else = a BLOCKED result per the unknown-
;; result semantics (lib/result-status.lisp convention, mirrored here so
;; yantra stays standalone): (blocked "curl exit N[\\nstderr]"). Callers
;; must branch on this — feeding a blocked result to json-parse was the
;; original bug.
(def http-transport-exit (lambda (r) (car r)))
(def http-transport-body (lambda (r) (car (cdr r))))
(def http-transport-stderr (lambda (r) (car (cdr (cdr r)))))

; ---------------------------------------------------------------------------
; Tool dispatch — one tool: bash. Real execution only.
; ---------------------------------------------------------------------------

; The tool result is structured: the exit status is evidence, not a
; detail to drop - a command that failed with 127 must not read the same
; as one that succeeded. Text shape stays LLM-friendly.
(def execute-bash
  (lambda (arguments-json)
    (let* ((args (json-parse arguments-json))
           (cmd (alist-ref "cmd" args))
           (result (process-run "bash" (list "-c" cmd)))
           (exit-code (nth 0 result))
           (stdout (nth 1 result))
           (stderr (nth 2 result)))
      (strcat "[exit-code " (number->string exit-code)
              "]\n"
              stdout
              (cond ((string-empty? stderr) "")
                    (t (strcat "\n[stderr]\n" stderr)))))))

; number->string-nonneg removed: core.lisp's number->string now renders
; every number canonically (FIX-NUMBER-TO-STRING-RATIONAL), so the shim
; duplicated it — including the killed-by-signal negative case.

(def dispatch-tool
  (lambda (name arguments-json)
    (cond
      ((equal? name "bash") (execute-bash arguments-json))
      (t (string-append "error: unknown tool: " name)))))

(def execute-tool-call
  (lambda (tc)
    (dispatch-tool (tc-name tc) (tc-arguments tc))))

; Executes each tool call and produces the correlated tool-result
; messages — the tool_call_id on each result is copied from the very
; call object being executed, so correlation holds by construction.
(def append-tool-results
  (lambda (tcs acc)
    (cond
      ((atom? tcs) () acc)
      ((atom? tcs) (1) acc)
      (t (append-tool-results
          (cdr tcs)
          (append acc
                  (list (list (cons (quote role) "tool")
                              (cons (quote tool-call-id) (tc-id (car tcs)))
                              (cons (quote content) (execute-tool-call (car tcs)))))))))))

; ---------------------------------------------------------------------------
; Completion validation — the key rule.
; ---------------------------------------------------------------------------

(def claim-markers
  (quote ("ran " "executed" "command output" "output of the command" "виконав" "виконано")))

(def markers-contained?
  (lambda (markers text)
    (cond
      ((atom? markers) () (quote ()))
      ((atom? markers) (1) (quote ()))
      ((string-contains? (car markers) text) t)
      (t (markers-contained? (cdr markers) text)))))

(def claims-execution?
  (lambda (text) (markers-contained? claim-markers text)))


; Does the conversation contain any tool result at all? Coarse - kept
; for callers that only need existence; the claim validator below uses
; the stricter owned-evidence rule instead.
(def has-tool-result?
  (lambda (messages)
    (cond
      ((atom? messages) () (quote ()))
      ((atom? messages) (1) (quote ()))
      ((equal? (msg-role (car messages)) "tool") t)
      (t (has-tool-result? (cdr messages))))))

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

(def msg-call-ids
  (lambda (m) (map tc-id (msg-tool-calls m))))

(def id-in-list?
  (lambda (id ids)
    (cond
      ((atom? ids) () (quote ()))
      ((atom? ids) (1) (quote ()))
      ((equal? id (car ids)) t)
      (t (id-in-list? id (cdr ids))))))

(def all-covered?
  (lambda (ids candidates)
    (cond
      ((atom? ids) () t)
      ((atom? ids) (1) t)
      ((id-in-list? (car ids) candidates) (all-covered? (cdr ids) candidates))
      (t (quote ())))))

; t iff everything BEFORE the final reply ends with
; [... assistant(tool-calls) tool* ] where every trailing tool result's
; id belongs to that assistant message. The final reply itself is dropped
; first - it is the message being validated, never its own evidence.
(def ends-with-owned-tool-results?
  (lambda (messages)
    (cond
      ((atom? messages) () (quote ()))
      ((atom? messages) (1) (quote ()))
      (t (collect-trailing-tools
          (cdr (reverse messages))
          (quote ()))))))

; walks backwards over a trailing run of tool results, then requires the
; assistant message that issued those calls to own every collected id
(def collect-trailing-tools
  (lambda (reversed collected)
    (cond
      ((atom? reversed) () (quote ()))
      ((atom? reversed) (1) (quote ()))
      ((equal? (msg-role (car reversed)) "tool")
       (collect-trailing-tools (cdr reversed)
                               (cons (msg-tool-call-id (car reversed)) collected)))
      (t
       (let ((issuer (car reversed)))
         (cond
           ((not? (equal? (msg-role issuer) "assistant")) (quote ()))
           ((atom? (msg-tool-calls issuer)) () (quote ()))
           ((atom? (msg-tool-calls issuer)) (1) (quote ()))
           (t (all-covered? collected (msg-call-ids issuer)))))))))

; A turn may finish only if its text claims no execution - or if its
; execution claims are backed by tool results owned by this turn's own
; tool calls, directly preceding the reply.
(def valid-final?
  (lambda (assistant-msg messages)
    (cond
      ((claims-execution? (msg-content assistant-msg))
       (ends-with-owned-tool-results? messages))
      (t t))))

(def invalid-completion-nudge
  (list (cons (quote role) "system")
        (cons (quote content)
              "Your last reply claimed a command was executed, but no bash tool result exists in this conversation. A textual claim is not evidence of execution. Either call the bash tool for real, or reply without claiming execution.")))

; ---------------------------------------------------------------------------
; Turn loop — hard MAX_TURNS limit, threaded (immutable) agent state.
; ---------------------------------------------------------------------------

(def max-turns 6)

(def count-with-role
  (lambda (role messages)
    (cond
      ((atom? messages) () 0)
      ((atom? messages) (1) 0)
      ((equal? (msg-role (car messages)) role) (+ 1 (count-with-role role (cdr messages))))
      (t (count-with-role role (cdr messages))))))

(def agent-loop
  (lambda (complete messages turn)
    (cond
      ((>= turn max-turns)
       (list (cons (quote status) (quote max-turns-reached))
             (cons (quote turn) turn)
             (cons (quote messages) messages)))
      (t
       (let* ((assistant-msg (complete messages))
              (with-reply (append messages (list assistant-msg)))
              (tcs (msg-tool-calls assistant-msg)))
         (cond
           ((atom? tcs) () (cond
              ((valid-final? assistant-msg with-reply)
               (list (cons (quote status) (quote completed))
                     (cons (quote epistemic-status) (quote hypothesis))
                     (cons (quote answer) (msg-content assistant-msg))
                     (cons (quote turn) turn)
                     (cons (quote messages) with-reply)))
              (t (agent-loop complete
                             (append with-reply (list invalid-completion-nudge))
                             (+ turn 1)))))
           ((atom? tcs) (1) (cond
              ((valid-final? assistant-msg with-reply)
               (list (cons (quote status) (quote completed))
                     (cons (quote epistemic-status) (quote hypothesis))
                     (cons (quote answer) (msg-content assistant-msg))
                     (cons (quote turn) turn)
                     (cons (quote messages) with-reply)))
              (t (agent-loop complete
                             (append with-reply (list invalid-completion-nudge))
                             (+ turn 1)))))
           (t (agent-loop complete
                          (append with-reply (append-tool-results tcs (quote ())))
                          (+ turn 1)))))))))

(def run-agent
  (lambda (complete system-prompt user-prompt)
    (agent-loop complete
                (list (list (cons (quote role) "system") (cons (quote content) system-prompt))
                      (list (cons (quote role) "user") (cons (quote content) user-prompt)))
                0)))

; Result readers
(def result-status (lambda (r) (alist-ref (quote status) r)))
(def result-epistemic-status (lambda (r) (alist-ref (quote epistemic-status) r)))
(def result-answer (lambda (r) (alist-ref (quote answer) r)))
(def result-turn (lambda (r) (alist-ref (quote turn) r)))
(def result-messages (lambda (r) (alist-ref (quote messages) r)))

; ---------------------------------------------------------------------------
; Live Ollama wiring — used only against a running server; tests inject
; their own `complete` so the control logic above is verified
; deterministically regardless of provider availability.
; ---------------------------------------------------------------------------

(def ollama-url "http://127.0.0.1:11434/v1/chat/completions")
(def ollama-model "qwen3:4b")

(def ollama-complete
  (lambda (messages)
    (let ((r (http-post-json ollama-url
                             (build-request-body ollama-model messages))))
      (cond ((= (http-transport-exit r) 0) 1
             (json->message
              (extract-assistant-message
               (json-parse (http-transport-body r)))))
            ((= (http-transport-exit r) 0) 0
            ; Non-zero curl exit: a BLOCKED result (result-status.lisp
            ;; convention) carrying the evidence — never an empty body
            ;; fed to json-parse.
            (t (list 'blocked
                     (string-append "curl exit "
                                    (number->string (http-transport-exit r))
                                    (let ((e (http-transport-stderr r)))
                                      (cond ((string-empty? e) "")
                                            (t (string-append "\n" e))))))))))))
