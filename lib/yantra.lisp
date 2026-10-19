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

(визначити json-escape-char
  (функція (ch)
    (за-умовою
      ((тотожне? ch "\"") "\\\"")
      ((тотожне? ch "\\") "\\\\")
      ((тотожне? ch "\n") "\\n")
      ((тотожне? ch "\r") "\\r")
      ((тотожне? ch "\t") "\\t")
      (так ch))))

(визначити json-escape-onto
  (функція (s acc)
    (за-умовою
      ((рядок-порожній? s) acc)
      (так (json-escape-onto (рядок-решта s)
                           (рядок-додати acc (екранувати-знак-формат-обміну-даними (рядок-перший s))))))))

(визначити json-escape
  (функція (s) (json-escape-onto s "")))

; The kernel's string-append is strictly binary AND a special form, so it
; cannot be passed as a function value to reduce — fold over rest args
; directly instead. Derived here, no new primitive.
(визначити strcat-onto
  (функція (items acc)
    (за-умовою
      
      ((атом? items)  acc)
      (так (strcat-onto (решта items) (рядок-додати acc (перше items)))))))

(визначити strcat
  (функція args
    (strcat-onto args "")))

(визначити json-encode-string
  (функція (s) (рядок-додати "\"" (рядок-додати (екранувати-формат-обміну-даними s) "\""))))

(визначити json-encode-key
  (функція (k)
    (за-умовою
      ((символ? k) (кодувати-рядок-формат-обміну-даними (символ-у-текст k)))
      (так (кодувати-рядок-формат-обміну-даними k)))))

; Objects are alists (lists of dotted pairs), arrays are proper lists.
; Disambiguation for this protocol's data: a list is an OBJECT iff its
; first element is a pair with an atomic key (an alist entry); arrays
; contain either scalars or nested structures (whose car is itself a
; pair). This survives nested-object values like ("cmd" . (("type" . ...))),
; which a naive "cdr of first entry is atom" test misclassifies as array.
(визначити json-object?
  (функція (v)
    (за-умовою
      
      (так (як-є ()))
      
      ((атом? (перше v))  (як-є ()))
      
      ((атом? (перше (перше v)))  t)
      )))

(визначити json-encode-value
  (функція (v)
    (за-умовою
      
      ((атом? v)  (за-умовою
         ((тотожне? v t) "true")
         ((тотожне? v (як-є ())) "null")
         ((класифікувати-рядкове-значення v)
          
          (кодувати-рядок-формат-обміну-даними v))
         (так (значення-у-текст v))))
      ((об'єкт-формат-обміну-даними? v) (кодувати-об'єкт-формат-обміну-даними v))
      (так (кодувати-масив-формат-обміну-даними v)))))

(визначити json-encode-object-entries
  (функція (entries acc)
    (за-умовою
      
      ((атом? entries)  acc)
      (так (нехай ((entry (перше entries)))
           (json-encode-object-entries
            (решта entries)
            (strcat acc
                    (за-умовою ((рядок-порожній? acc) "")
                          (так ","))
                    (json-encode-key (перше entry))
                    ":"
                    (кодувати-значення-формат-обміну-даними (решта entry)))))))))

(визначити json-encode-object
  (функція (alist)
    (strcat "{" (json-encode-object-entries alist "") "}")))

(визначити json-encode-array-items
  (функція (items acc)
    (за-умовою
      
      ((атом? items)  acc)
      (так (json-encode-array-items
          (решта items)
          (strcat acc
                  (за-умовою ((рядок-порожній? acc) "")
                        (так ","))
                  (кодувати-значення-формат-обміну-даними (перше items))))))))

(визначити json-encode-array
  (функція (items)
    (strcat "[" (json-encode-array-items items "") "]")))

(визначити json-encode кодувати-значення-формат-обміну-даними)

; ---------------------------------------------------------------------------
; Message / tool-call accessors and JSON -> internal conversion
; ---------------------------------------------------------------------------

; Safe alist lookup: assoc returns () when the key is absent, and this
; kernel's cdr fails named on (), so every read goes through this guard.
; A genuinely absent key and an explicit nil value both read as () — the
; loop below only ever distinguishes present-nonempty from everything else.
(визначити alist-ref
  (функція (key alist)
    (за-умовою
      ((знайти-за-ключем key alist) (решта (знайти-за-ключем key alist)))
      )))

(визначити msg-role (функція (m) (alist-ref (як-є role) m)))
(визначити msg-content (функція (m) (alist-ref (як-є content) m)))
(визначити msg-tool-calls (функція (m) (alist-ref (як-є tool-calls) m)))
(визначити msg-tool-call-id (функція (m) (alist-ref (як-є tool-call-id) m)))

(визначити tc-id (функція (tc) (alist-ref (як-є id) tc)))
(визначити tc-name (функція (tc) (alist-ref (як-є name) tc)))
(визначити tc-arguments (функція (tc) (alist-ref (як-є arguments) tc)))

; OpenAI's content field is null when the assistant emits only tool calls.
(визначити json-message-content
  (функція (jm)
    ((функція (c)
      (за-умовою
        ((тотожне? c (як-є ())) "")
        (так c)))
     (alist-ref "content" jm))))

(визначити json->tool-call
  (функція (jtc)
    ((функція (fn)
      (список (сполучити (як-є id) (alist-ref "id" jtc))
            (сполучити (як-є name) (alist-ref "name" fn))
            (сполучити (як-є arguments) (alist-ref "arguments" fn))))
     (alist-ref "function" jtc))))

(визначити json->message
  (функція (jm)
    ((функція (tcs)
      (приєднати (список (сполучити (як-є role) (alist-ref "role" jm))
                    (сполучити (як-є content) (зміст-повідомлення-формат-обміну-даними jm)))
              (за-умовою
                (tcs (список (сполучити (як-є tool-calls) (відобразити виклик-інструмента-з-формат-обміну-даними tcs))))
                )))
     (alist-ref "tool_calls" jm))))

(визначити extract-assistant-message
  (функція (response-json)
    (нехай-послідовно ((choices (alist-ref "choices" response-json))
           (choice (перше choices)))
      (alist-ref "message" choice))))

; ---------------------------------------------------------------------------
; Request encoding (raw-data builders; one json-encode at the leaf)
; ---------------------------------------------------------------------------

(визначити encode-tool-call
  (функція (tc)
    (список (сполучити "id" (tc-id tc))
          (сполучити "type" "function")
          (сполучити "function" (список (сполучити "name" (tc-name tc))
                                 (сполучити "arguments" (tc-arguments tc)))))))

(визначити encode-message
  (функція (m)
    (за-умовою
      ((однакові? (msg-role m) "tool")
       (список (сполучити "role" "tool")
             (сполучити "tool_call_id" (msg-tool-call-id m))
             (сполучити "content" (msg-content m))))
      (так (нехай ((tcs (msg-tool-calls m)))
           (приєднати (список (сполучити "role" (msg-role m))
                         (сполучити "content" (msg-content m)))
                   (за-умовою (tcs (список (сполучити "tool_calls" (відобразити encode-tool-call tcs))))
                         )))))))

(визначити bash-tool-schema
  (функція ()
    (список (сполучити "type" "function")
          (сполучити "function"
                (список (сполучити "name" "bash")
                      (сполучити "description" "Run one bash command; returns combined stdout and stderr.")
                      (сполучити "parameters"
                            (список (сполучити "type" "object")
                                  (сполучити "properties"
                                        (список (сполучити "cmd" (список (сполучити "type" "string")
                                                                (сполучити "description" "The bash command to execute")))))
                                  (сполучити "required" (список "cmd")))))))))

(визначити build-request-body
  (функція (model messages)
    (json-encode
     (список (сполучити "model" model)
           (сполучити "messages" (відобразити encode-message messages))
           (сполучити "tools" (список (bash-tool-schema)))))))

; ---------------------------------------------------------------------------
; Host transport: HTTP POST via the existing allowlisted process-run +
; curl. Zero new Rust beyond json-parse; swap this one function if a
; native http-post primitive is ever adopted.
; ---------------------------------------------------------------------------

(визначити http-post-json
  (функція (url body)
    ;; --fail: non-2xx yields non-zero exit instead of an error body that
    ;; would be fed to json-parse; --max-time: never hang the agent loop
    ;; on a stuck server; --show-error keeps the reason on stderr.
    ;; FIX YANTRA-HTTP-ERROR-PROPAGATION: the curl exit code used to be
    ;; dropped here (stdout-only), so a failed request surfaced as an
    ;; opaque json-parse("") crash downstream — the same evidence-losing
    ;; class already fixed in execute-bash. The full triple now flows to
    ;; ollama-complete, which decides.
    (нехай ((result (процес-запустити "curl"
                               (список "-s" "-S" "--fail" "--show-error"
                                     "--max-time" "120"
                                     "-X" "POST"
                                     "-H" "Content-Type: application/json"
                                     "-d" body url))))
      (список (елемент-списку-за-індексом 0 result) (елемент-списку-за-індексом 1 result) (елемент-списку-за-індексом 2 result)))))

;; Transport result contract: (exit-code stdout stderr). Exit 0 = body is
;; the JSON payload; anything else = a BLOCKED result per the unknown-
;; result semantics (lib/result-status.lisp convention, mirrored here so
;; yantra stays standalone): (blocked "curl exit N[\\nstderr]"). Callers
;; must branch on this — feeding a blocked result to json-parse was the
;; original bug.
(визначити http-transport-exit (функція (r) (перше r)))
(визначити http-transport-body (функція (r) (перше (решта r))))
(визначити http-transport-stderr (функція (r) (перше (решта (решта r)))))

; ---------------------------------------------------------------------------
; Tool dispatch — one tool: bash. Real execution only.
; ---------------------------------------------------------------------------

; The tool result is structured: the exit status is evidence, not a
; detail to drop - a command that failed with 127 must not read the same
; as one that succeeded. Text shape stays LLM-friendly.
(визначити execute-bash
  (функція (arguments-json)
    (нехай-послідовно ((args (формат-обміну-даними-розібрати arguments-json))
           (cmd (alist-ref "cmd" args))
           (result (процес-запустити "bash" (список "-c" cmd)))
           (exit-code (елемент-списку-за-індексом 0 result))
           (stdout (елемент-списку-за-індексом 1 result))
           (stderr (елемент-списку-за-індексом 2 result)))
      (strcat "[exit-code " (число-рядок exit-code)
              "]\n"
              stdout
              (за-умовою ((рядок-порожній? stderr) "")
                    (так (strcat "\n[stderr]\n" stderr)))))))

; number->string-nonneg removed: core.lisp's number->string now renders
; every number canonically (FIX-NUMBER-TO-STRING-RATIONAL), so the shim
; duplicated it — including the killed-by-signal negative case.

(визначити dispatch-tool
  (функція (name arguments-json)
    (за-умовою
      ((однакові? name "bash") (execute-bash arguments-json))
      (так (рядок-додати "error: unknown tool: " name)))))

(визначити execute-tool-call
  (функція (tc)
    (dispatch-tool (tc-name tc) (tc-arguments tc))))

; Executes each tool call and produces the correlated tool-result
; messages — the tool_call_id on each result is copied from the very
; call object being executed, so correlation holds by construction.
(визначити append-tool-results
  (функція (tcs acc)
    (за-умовою
      
      ((атом? tcs)  acc)
      (так (append-tool-results
          (решта tcs)
          (приєднати acc
                  (список (список (сполучити (як-є role) "tool")
                              (сполучити (як-є tool-call-id) (tc-id (перше tcs)))
                              (сполучити (як-є content) (execute-tool-call (перше tcs)))))))))))

; ---------------------------------------------------------------------------
; Completion validation — the key rule.
; ---------------------------------------------------------------------------

(визначити claim-markers
  (як-є ("ran " "executed" "command output" "output of the command" "виконав" "виконано")))

(визначити markers-contained?
  (функція (markers text)
    (за-умовою
      
      ((атом? markers)  (як-є ()))
      ((рядок-містить? (перше markers) text) t)
      (так (markers-contained? (решта markers) text)))))

(визначити claims-execution?
  (функція (text) (markers-contained? claim-markers text)))


; Does the conversation contain any tool result at all? Coarse - kept
; for callers that only need existence; the claim validator below uses
; the stricter owned-evidence rule instead.
(визначити has-tool-result?
  (функція (messages)
    (за-умовою
      
      ((атом? messages)  (як-є ()))
      ((однакові? (msg-role (перше messages)) "tool") t)
      (так (є-результат-інструмента? (решта messages))))))

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

(визначити msg-call-ids
  (функція (m) (відобразити tc-id (msg-tool-calls m))))

(визначити id-in-list?
  (функція (id ids)
    (за-умовою
      
      ((атом? ids)  (як-є ()))
      ((однакові? id (перше ids)) t)
      (так (id-in-list? id (решта ids))))))

(визначити all-covered?
  (функція (ids candidates)
    (за-умовою
      
      ((атом? ids)  t)
      ((id-in-list? (перше ids) candidates) (усі-ідентифікатори-покриті? (решта ids) candidates))
      )))

; t iff everything BEFORE the final reply ends with
; [... assistant(tool-calls) tool* ] where every trailing tool result's
; id belongs to that assistant message. The final reply itself is dropped
; first - it is the message being validated, never its own evidence.
(визначити ends-with-owned-tool-results?
  (функція (messages)
    (за-умовою
      
      ((атом? messages)  (як-є ()))
      (так (collect-trailing-tools
          (решта (зворот messages))
          (як-є ()))))))

; walks backwards over a trailing run of tool results, then requires the
; assistant message that issued those calls to own every collected id
(визначити collect-trailing-tools
  (функція (reversed collected)
    (за-умовою
      
      ((атом? reversed)  (як-є ()))
      ((однакові? (msg-role (перше reversed)) "tool")
       (collect-trailing-tools (решта reversed)
                               (сполучити (msg-tool-call-id (перше reversed)) collected)))
      (так
       ((функція (issuer)
         (за-умовою
           ((хибне? (однакові? (msg-role issuer) "assistant")) (як-є ()))
           
           ((атом? (msg-tool-calls issuer))  (як-є ()))
           (так (усі-ідентифікатори-покриті? collected (msg-call-ids issuer))))) (перше reversed))))))

; A turn may finish only if its text claims no execution - or if its
; execution claims are backed by tool results owned by this turn's own
; tool calls, directly preceding the reply.
(визначити valid-final?
  (функція (assistant-msg messages)
    (за-умовою
      ((стверджує-виконання? (msg-content assistant-msg))
       (завершується-власними-результатами? messages))
      (так t))))

(визначити invalid-completion-nudge
  (список (сполучити (як-є role) "system")
        (сполучити (як-є content)
              "Your last reply claimed a command was executed, but no bash tool result exists in this conversation. A textual claim is not evidence of execution. Either call the bash tool for real, or reply without claiming execution.")))

; ---------------------------------------------------------------------------
; Turn loop — hard MAX_TURNS limit, threaded (immutable) agent state.
; ---------------------------------------------------------------------------

(визначити max-turns 6)

(визначити count-with-role
  (функція (role messages)
    (за-умовою
      
      ((атом? messages)  0)
      ((однакові? (msg-role (перше messages)) role) (додати 1 (count-with-role role (решта messages))))
      (так (count-with-role role (решта messages))))))

(визначити agent-loop
  (функція (complete messages turn)
    (за-умовою
      ((не-менше? turn max-turns)
       (список (сполучити (як-є status) (як-є max-turns-reached))
             (сполучити (як-є turn) turn)
             (сполучити (як-є messages) messages)))
      (так
       (нехай-послідовно ((assistant-msg (complete messages))
              (with-reply (приєднати messages (список assistant-msg)))
              (tcs (msg-tool-calls assistant-msg)))
         (за-умовою
           
           ((атом? tcs)  (за-умовою
              ((припустима-завершальна-відповідь? assistant-msg with-reply)
               (список (сполучити (як-є status) (як-є completed))
                     (сполучити (як-є epistemic-status) (як-є hypothesis))
                     (сполучити (як-є answer) (msg-content assistant-msg))
                     (сполучити (як-є turn) turn)
                     (сполучити (як-є messages) with-reply)))
              (так (agent-loop complete
                             (приєднати with-reply (список invalid-completion-nudge))
                             (додати turn 1)))))
           (так (agent-loop complete
                          (приєднати with-reply (append-tool-results tcs (як-є ())))
                          (додати turn 1)))))))))

(визначити run-agent
  (функція (complete system-prompt user-prompt)
    (agent-loop complete
                (список (список (сполучити (як-є role) "system") (сполучити (як-є content) system-prompt))
                      (список (сполучити (як-є role) "user") (сполучити (як-є content) user-prompt)))
                0)))

; Result readers
(визначити result-status (функція (r) (alist-ref (як-є status) r)))
(визначити result-epistemic-status (функція (r) (alist-ref (як-є epistemic-status) r)))
(визначити result-answer (функція (r) (alist-ref (як-є answer) r)))
(визначити result-turn (функція (r) (alist-ref (як-є turn) r)))
(визначити result-messages (функція (r) (alist-ref (як-є messages) r)))

; ---------------------------------------------------------------------------
; Live Ollama wiring — used only against a running server; tests inject
; their own `complete` so the control logic above is verified
; deterministically regardless of provider availability.
; ---------------------------------------------------------------------------

(визначити ollama-url "http://127.0.0.1:11434/v1/chat/completions")
(визначити ollama-model "qwen3:4b")

(визначити ollama-complete
  (функція (messages)
    (нехай ((r (http-post-json ollama-url
                             (створити-тіло-запиту ollama-model messages))))
      (за-умовою ((однакові? (http-transport-exit r) 0) 
             (повідомлення-з-формат-обміну-даними
              (витягти-відповідь-помічника
               (формат-обміну-даними-розібрати (http-transport-body r)))))
            ((хибне? (однакові? (http-transport-exit r) 0))
            ; Non-zero curl exit: a BLOCKED result (result-status.lisp
            ;; convention) carrying the evidence — never an empty body
            ;; fed to json-parse.
            (так (список 'blocked
                     (рядок-додати "curl exit "
                                    (число-рядок (http-transport-exit r))
                                    (нехай ((e (http-transport-stderr r)))
                                      (за-умовою ((рядок-порожній? e) "")
                                            (так (рядок-додати "\n" e))))))))))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити усі-ідентифікатори-покриті? all-covered?)
(визначити стверджує-виконання? claims-execution?)
(визначити завершується-власними-результатами? ends-with-owned-tool-results?)
(визначити витягти-відповідь-помічника extract-assistant-message)
(визначити є-результат-інструмента? has-tool-result?)
(визначити кодувати-масив-формат-обміну-даними json-encode-array)
(визначити кодувати-об'єкт-формат-обміну-даними json-encode-object)
(визначити кодувати-рядок-формат-обміну-даними json-encode-string)
(визначити кодувати-значення-формат-обміну-даними json-encode-value)
(визначити екранувати-формат-обміну-даними json-escape)
(визначити екранувати-знак-формат-обміну-даними json-escape-char)
(визначити об'єкт-формат-обміну-даними? json-object?)
(визначити припустима-завершальна-відповідь? valid-final?)

; Повні ратифіковані D10-проєкції чинних Lisp-функцій, не нові машинні інструкції.
; D10:0100010110
(визначити зміст-повідомлення-формат-обміну-даними json-message-content)
; D10:0100011000
(визначити повідомлення-з-формат-обміну-даними json->message)
; D10:0100010111
(визначити виклик-інструмента-з-формат-обміну-даними json->tool-call)
; D10:0100011010
(визначити кодувати-виклик-інструмента encode-tool-call)
; D10:0100011011
(визначити кодувати-повідомлення encode-message)
; D10:0100011100
(визначити створити-тіло-запиту build-request-body)
