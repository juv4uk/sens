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

(визначити екранувати-знак-формат-обміну-даними
  (функція (знак)
    (за-умовою
      ((тотожне? знак "\"") "\\\"")
      ((тотожне? знак "\\") "\\\\")
      ((тотожне? знак "\n") "\\n")
      ((тотожне? знак "\r") "\\r")
      ((тотожне? знак "\t") "\\t")
      (так знак))))

(визначити json-escape-onto
  (функція (вхідний-текст накопичений-текст)
    (за-умовою
      ((рядок-порожній? вхідний-текст) накопичений-текст)
      (так (json-escape-onto (рядок-решта вхідний-текст)
                           (рядок-додати накопичений-текст (екранувати-знак-формат-обміну-даними (рядок-перший вхідний-текст))))))))

(визначити екранувати-формат-обміну-даними
  (функція (вхідний-текст) (json-escape-onto вхідний-текст "")))

; The kernel's string-append is strictly binary AND a special form, so it
; cannot be passed as a function value to reduce — fold over rest args
; directly instead. Derived here, no new primitive.
(визначити strcat-onto
  (функція (частини-рядка накопичений-текст)
    (за-умовою
      
      ((атом? частини-рядка)  накопичений-текст)
      (так (strcat-onto (решта частини-рядка) (рядок-додати накопичений-текст (перше частини-рядка)))))))

(визначити strcat
  (функція частини-тексту
    (strcat-onto частини-тексту "")))

(визначити кодувати-рядок-формат-обміну-даними
  (функція (рядок-для-кодування) (рядок-додати "\"" (рядок-додати (екранувати-формат-обміну-даними рядок-для-кодування) "\""))))

(визначити json-encode-key
  (функція (ключ-для-кодування)
    (за-умовою
      ((символ? ключ-для-кодування) (кодувати-рядок-формат-обміну-даними (символ-у-текст ключ-для-кодування)))
      (так (кодувати-рядок-формат-обміну-даними ключ-для-кодування)))))

; Objects are alists (lists of dotted pairs), arrays are proper lists.
; Disambiguation for this protocol's data: a list is an OBJECT iff its
; first element is a pair with an atomic key (an alist entry); arrays
; contain either scalars or nested structures (whose car is itself a
; pair). This survives nested-object values like ("cmd" . (("type" . ...))),
; which a naive "cdr of first entry is atom" test misclassifies as array.
; Об'єкт JSON — непорожній список пар із атомарним першим ключем.
; Безумовна гілка мусить бути останньою, інакше всі структури стають «ні».
; Це мовна функція: наявність імені в D10 не надає автоматичної виконуваності.
(визначити об'єкт-формат-обміну-даними?
  (функція (перевірювана-структура)
    (за-умовою
      ((атом? перевірювана-структура) ні)
      ((атом? (перше перевірювана-структура)) ні)
      ((атом? (перше (перше перевірювана-структура))) так)
      (так ні))))

(визначити кодувати-значення-формат-обміну-даними
  (функція (значення-для-кодування)
    (за-умовою
      
      ((атом? значення-для-кодування)  (за-умовою
         ((тотожне? значення-для-кодування так) "true")
         ((тотожне? значення-для-кодування (як-є ())) "null")
         ((класифікувати-рядкове-значення значення-для-кодування)
          
          (кодувати-рядок-формат-обміну-даними значення-для-кодування))
         (так (значення-у-текст значення-для-кодування))))
      ((об'єкт-формат-обміну-даними? значення-для-кодування) (кодувати-об'єкт-формат-обміну-даними значення-для-кодування))
      (так (кодувати-масив-формат-обміну-даними значення-для-кодування)))))

(визначити json-encode-object-entries
  (функція (записи-об'єкта накопичений-рядок)
    (за-умовою
      
      ((атом? записи-об'єкта)  накопичений-рядок)
      (так (нехай ((поточний-запис (перше записи-об'єкта)))
           (json-encode-object-entries
            (решта записи-об'єкта)
            (strcat накопичений-рядок
                    (за-умовою ((рядок-порожній? накопичений-рядок) "")
                          (так ","))
                    (json-encode-key (перше поточний-запис))
                    ":"
                    (кодувати-значення-формат-обміну-даними (решта поточний-запис)))))))))

(визначити кодувати-об'єкт-формат-обміну-даними
  (функція (пари-об'єкта)
    (strcat "{" (json-encode-object-entries пари-об'єкта "") "}")))

(визначити json-encode-array-items
  (функція (елементи-масиву накопичений-рядок)
    (за-умовою
      
      ((атом? елементи-масиву)  накопичений-рядок)
      (так (json-encode-array-items
          (решта елементи-масиву)
          (strcat накопичений-рядок
                  (за-умовою ((рядок-порожній? накопичений-рядок) "")
                        (так ","))
                  (кодувати-значення-формат-обміну-даними (перше елементи-масиву))))))))

(визначити кодувати-масив-формат-обміну-даними
  (функція (елементи-масиву)
    (strcat "[" (json-encode-array-items елементи-масиву "") "]")))


; ---------------------------------------------------------------------------
; Message / tool-call accessors and JSON -> internal conversion
; ---------------------------------------------------------------------------

; Safe alist lookup: assoc returns () when the key is absent, and this
; kernel's cdr fails named on (), so every read goes through this guard.
; A genuinely absent key and an explicit nil value both read as () — the
; loop below only ever distinguishes present-nonempty from everything else.
(визначити alist-ref
  (функція (ключ пари-списку)
    ((функція (знайдений-запис)
       (за-умовою
         ((порожній? знайдений-запис) (як-є ()))
         (так (решта знайдений-запис))))
     (знайти-за-ключем ключ пари-списку))))

(визначити msg-role (функція (повідомлення) (alist-ref (як-є role) повідомлення)))
(визначити msg-content (функція (повідомлення) (alist-ref (як-є content) повідомлення)))
(визначити msg-tool-calls (функція (повідомлення) (alist-ref (як-є tool-calls) повідомлення)))
(визначити msg-tool-call-id (функція (повідомлення) (alist-ref (як-є tool-call-id) повідомлення)))

(визначити tc-id (функція (виклик-інструмента) (alist-ref (як-є id) виклик-інструмента)))
(визначити tc-name (функція (виклик-інструмента) (alist-ref (як-є name) виклик-інструмента)))
(визначити tc-arguments (функція (виклик-інструмента) (alist-ref (як-є arguments) виклик-інструмента)))

; OpenAI's content field is null when the assistant emits only tool calls.
(визначити зміст-повідомлення-формат-обміну-даними
  (функція (джерельне-повідомлення)
    ((функція (прочитаний-зміст)
      (за-умовою
        ((тотожне? прочитаний-зміст (як-є ())) "")
        (так прочитаний-зміст)))
     (alist-ref "content" джерельне-повідомлення))))

(визначити виклик-інструмента-з-формат-обміну-даними
  (функція (джерельний-виклик)
    ((функція (опис-функції)
      (список (сполучити (як-є id) (alist-ref "id" джерельний-виклик))
            (сполучити (як-є name) (alist-ref "name" опис-функції))
            (сполучити (як-є arguments) (alist-ref "arguments" опис-функції))))
     (alist-ref "function" джерельний-виклик))))

(визначити повідомлення-з-формат-обміну-даними
  (функція (джерельне-повідомлення)
    ((функція (виклики-інструментів)
       (приєднати
         (список
           (сполучити (як-є role) (alist-ref "role" джерельне-повідомлення))
           (сполучити (як-є content)
             (зміст-повідомлення-формат-обміну-даними джерельне-повідомлення)))
         (за-умовою
           ((порожній? виклики-інструментів) (як-є ()))
           (так (список
             (сполучити (як-є tool-calls)
               (відобразити виклик-інструмента-з-формат-обміну-даними
                 виклики-інструментів)))))))
     (alist-ref "tool_calls" джерельне-повідомлення))))

(визначити витягти-відповідь-помічника
  (функція (одержана-відповідь)
    (нехай-послідовно ((варіанти-відповіді (alist-ref "choices" одержана-відповідь))
           (перший-варіант (перше варіанти-відповіді)))
      (alist-ref "message" перший-варіант))))

; ---------------------------------------------------------------------------
; Request encoding (raw-data builders; one json-encode at the leaf)
; ---------------------------------------------------------------------------

(визначити кодувати-виклик-інструмента
  (функція (виклик-інструмента)
    (список (сполучити "id" (tc-id виклик-інструмента))
          (сполучити "type" "function")
          (сполучити "function" (список (сполучити "name" (tc-name виклик-інструмента))
                                 (сполучити "arguments" (tc-arguments виклик-інструмента)))))))

(визначити кодувати-повідомлення
  (функція (повідомлення)
    (за-умовою
      ((однакові? (msg-role повідомлення) "tool")
       (список
         (сполучити "role" "tool")
         (сполучити "tool_call_id" (msg-tool-call-id повідомлення))
         (сполучити "content" (msg-content повідомлення))))
      (так
       ((функція (виклики-інструментів)
          (приєднати
            (список
              (сполучити "role" (msg-role повідомлення))
              (сполучити "content" (msg-content повідомлення)))
            (за-умовою
              ((порожній? виклики-інструментів) (як-є ()))
              (так
               (список
                 (сполучити "tool_calls"
                   (відобразити кодувати-виклик-інструмента
                     виклики-інструментів)))))))
        (msg-tool-calls повідомлення))))))

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

(визначити створити-тіло-запиту
  (функція (модель повідомлення)
    (кодувати-значення-формат-обміну-даними
      (список
        (сполучити "model" модель)
        (сполучити "messages" (відобразити кодувати-повідомлення повідомлення))
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
    (нехай-послідовно ((розібрані-аргументи-виклику (формат-обміну-даними-розібрати arguments-json))
           (cmd (alist-ref "cmd" розібрані-аргументи-виклику))
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
      
      ((атом? markers) ні)
      ((рядок-містить? (перше markers) text) так)
      (так (markers-contained? (решта markers) text)))))

(визначити стверджує-виконання?
  (функція (text) (markers-contained? claim-markers text)))


; Does the conversation contain any tool result at all? Coarse - kept
; for callers that only need existence; the claim validator below uses
; the stricter owned-evidence rule instead.
(визначити є-результат-інструмента?
  (функція (messages)
    (за-умовою
      
      ((атом? messages) ні)
      ((однакові? (msg-role (перше messages)) "tool") так)
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
      
      ((атом? ids) ні)
      ((однакові? id (перше ids)) так)
      (так (id-in-list? id (решта ids))))))

(визначити усі-ідентифікатори-покриті?
  (функція (ідентифікатори кандидати)
    (за-умовою
      ((атом? ідентифікатори) так)
      ((id-in-list? (перше ідентифікатори) кандидати)
       (усі-ідентифікатори-покриті? (решта ідентифікатори) кандидати))
      (так ні))))

; t iff everything BEFORE the final reply ends with
; [... assistant(tool-calls) tool* ] where every trailing tool result's
; id belongs to that assistant message. The final reply itself is dropped
; first - it is the message being validated, never its own evidence.
(визначити завершується-власними-результатами?
  (функція (messages)
    (за-умовою
      
      ((атом? messages) ні)
      (так (collect-trailing-tools
          (решта (зворот messages))
          (як-є ()))))))

; walks backwards over a trailing run of tool results, then requires the
; assistant message that issued those calls to own every collected id
(визначити collect-trailing-tools
  (функція (повідомлення-назад ідентифікатори-результатів)
    (за-умовою
      ((атом? повідомлення-назад) ні)
      ((однакові? (msg-role (перше повідомлення-назад)) "tool")
       (collect-trailing-tools
         (решта повідомлення-назад)
         (сполучити
           (msg-tool-call-id (перше повідомлення-назад))
           ідентифікатори-результатів)))
      (так
       ((функція (повідомлення-виклику)
          (за-умовою
            ((хибне? (однакові? (msg-role повідомлення-виклику) "assistant")) ні)
            ((порожній? ідентифікатори-результатів) ні)
            ((порожній? (msg-tool-calls повідомлення-виклику)) ні)
            ((усі-ідентифікатори-покриті?
               (msg-call-ids повідомлення-виклику)
               ідентифікатори-результатів)
             (усі-ідентифікатори-покриті?
               ідентифікатори-результатів
               (msg-call-ids повідомлення-виклику)))
            (так ні)))
        (перше повідомлення-назад))))))

; A turn may finish only if its text claims no execution - or if its
; execution claims are backed by tool results owned by this turn's own
; tool calls, directly preceding the reply.
(визначити припустима-завершальна-відповідь?
  (функція (assistant-msg messages)
    (за-умовою
      ((стверджує-виконання? (msg-content assistant-msg))
       (завершується-власними-результатами? messages))
      (так так))))

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

; Невдалий HTTP-запит не є повідомленням помічника і не може
; потрапляти до пошуку полів або до статусу completed.
(визначити заблокована-відповідь?
  (функція (відповідь)
    (за-умовою
      ((атом? відповідь) так)
      ((атом? (перше відповідь))
       (тотожне? (перше відповідь) (як-є blocked)))
      (так ні))))

(визначити agent-loop
  (функція (завершити повідомлення крок)
    (за-умовою
      ((не-менше? крок max-turns)
       (список
         (сполучити (як-є status) (як-є max-turns-reached))
         (сполучити (як-є turn) крок)
         (сполучити (як-є messages) повідомлення)))
      (так
       ((функція (відповідь)
          (за-умовою
            ((заблокована-відповідь? відповідь)
             (список
               (сполучити (як-є status) (як-є blocked))
               (сполучити (як-є detail) відповідь)
               (сполучити (як-є turn) крок)
               (сполучити (як-є messages) повідомлення)))
            (так
             ((функція (з-відповіддю)
                ((функція (виклики-інструментів)
                   (за-умовою
                     ((порожній? виклики-інструментів)
                      (за-умовою
                        ((припустима-завершальна-відповідь? відповідь з-відповіддю)
                         (список
                           (сполучити (як-є status) (як-є completed))
                           (сполучити (як-є epistemic-status) (як-є hypothesis))
                           (сполучити (як-є answer) (msg-content відповідь))
                           (сполучити (як-є turn) крок)
                           (сполучити (як-є messages) з-відповіддю)))
                        (так
                         (agent-loop завершити
                           (приєднати з-відповіддю (список invalid-completion-nudge))
                           (додати крок 1)))))
                     (так
                      (agent-loop завершити
                        (приєднати з-відповіддю
                          (append-tool-results виклики-інструментів (як-є ())))
                        (додати крок 1)))))
                 (msg-tool-calls відповідь)))
              (приєднати повідомлення (список відповідь))))))
        (завершити повідомлення))))))

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
  (функція (повідомлення)
    ((функція (транспортний-результат)
       (за-умовою
         ((однакові? (http-transport-exit транспортний-результат) 0)
          (повідомлення-з-формат-обміну-даними
            (витягти-відповідь-помічника
              (формат-обміну-даними-розібрати
                (http-transport-body транспортний-результат)))))
         (так
          (список
            (як-є blocked)
            (рядок-додати
              "curl exit "
              (рядок-додати
                (число-рядок (http-transport-exit транспортний-результат))
                (за-умовою
                  ((рядок-порожній? (http-transport-stderr транспортний-результат)) "")
                  (так
                    (рядок-додати "\n"
                      (http-transport-stderr транспортний-результат)))))))))
     (http-post-json ollama-url
       (створити-тіло-запиту ollama-model повідомлення))))))

; Функції нижче визначені безпосередньо за чинною повною проєкцією укр.

; Повні ратифіковані D10-проєкції чинних Lisp-функцій, не нові машинні інструкції.
; D10:0100010110
; D10:0100011000
; D10:0100010111
; D10:0100011010
; D10:0100011011
; D10:0100011100
