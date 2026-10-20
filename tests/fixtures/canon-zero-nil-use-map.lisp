; #215 — машинно-читана карта міграції вжитку Nil.
; Це дані класифікації, а не виконувана семантика істини.
; Категорії:
;   structural            — порожній список / термінатор правильного списку; лишити.
;   empty-result          — нуль вироблених значень/заповнювач результату; зберегти, але перевірити контекст.
;   legacy-semantic       — історичне змішання NIL/FALSE; мусить мігрувати.
;   boundary-compatibility— подання хоста/протоколу, наразі зведене до Nil; ізолювати/переглянути.
;
; `owner` називає issue, що має владу над семантикою заміни.

(nil-use
  (path . "crates/my-lisp/src/value.rs")
  (site . list-tail)
  (class . structural)
  (owner . 215)
  (disposition . keep)
  (note . "Value::list folds proper-list tails onto Value::Nil"))

(nil-use
  (path . "crates/my-lisp/src/value.rs")
  (site . render-empty-and-pair-tail)
  (class . structural)
  (owner . 215)
  (disposition . keep)
  (note . "Value::Nil renders as () and terminates proper-list rendering"))

(nil-use
  (path . "crates/my-lisp/src/eval/canon.rs")
  (site . canonical-empty-list)
  (class . structural)
  (owner . 215)
  (disposition . keep)
  (note . "CanonicalIdentity::EmptyList projects to Value::Nil"))

(nil-use
  (path . "crates/my-lisp/src/value.rs")
  (site . is-truthy)
  (class . legacy-semantic)
  (owner . 217)
  (disposition . retire)
  (note . "Value::Nil is currently hard-coded as false; this is the central Nil-as-false debt"))

(nil-use
  (path . "crates/my-lisp/src/value.rs")
  (site . truth-false)
  (class . legacy-semantic)
  (owner . 220)
  (depends-on . 218)
  (disposition . retire)
  (note . "Value::truth(false) currently manufactures Value::Nil"))

(nil-use
  (path . "crates/my-lisp/src/eval/special_forms/core.rs")
  (site . cond-is-truthy)
  (class . legacy-semantic)
  (owner . 217)
  (depends-on . 218)
  (disposition . migrate)
  (note . "public cond currently consumes arbitrary Value through is_truthy"))

(nil-use
  (path . "crates/my-lisp/src/eval/canon.rs")
  (site . atom-eq-value-truth)
  (class . legacy-semantic)
  (owner . 218)
  (disposition . migrate)
  (note . "structural observations currently collapse their negative result to Nil"))

(nil-use
  (path . "crates/my-lisp/src/eval/special_forms/core.rs")
  (site . eq-value-truth)
  (class . legacy-semantic)
  (owner . 218)
  (disposition . migrate)
  (note . "eq_values currently returns Value::truth(left == right)"))

(nil-use
  (path . "crates/my-lisp/src/eval/arithmetic.rs")
  (site . comparison-value-truth)
  (class . legacy-semantic)
  (owner . 216)
  (disposition . migrate)
  (note . "mathematical comparisons currently return historical t/() instead of exact 1/1 or 0/1"))

(nil-use
  (path . "crates/my-lisp/src/eval/special_forms/strings.rs")
  (site . predicate-value-truth)
  (class . legacy-semantic)
  (owner . 218)
  (depends-on . 220)
  (disposition . migrate)
  (note . "string/classification predicates still use Value::truth and inherit Nil-as-false"))

(nil-use
  (path . "crates/my-lisp/src/environment.rs")
  (site . universal-t-binding)
  (class . legacy-semantic)
  (owner . 220)
  (disposition . retire-or-confine)
  (note . "root environment installs historical universal t truth sentinel"))

(nil-use
  (path . "crates/my-lisp/src/eval/mod.rs")
  (site . empty-program-result)
  (class . empty-result)
  (owner . 215)
  (disposition . keep-with-witness)
  (note . "evaluation accumulator begins at Nil; zero-expression result must remain no-answer/empty-result rather than FALSE"))

(nil-use
  (path . "crates/my-lisp/src/eval/closures.rs")
  (site . empty-body-result)
  (class . empty-result)
  (owner . 215)
  (disposition . keep-with-witness)
  (note . "closure body accumulator begins at Nil; audit as empty result, never boolean false"))

(nil-use
  (path . "lib/reason.lisp")
  (site . zero-proof-result)
  (class . empty-result)
  (owner . 219)
  (disposition . preserve-separate-from-logic-state)
  (note . "reasoning may return () when zero answers/proofs are produced; this is not NEITHER/FALSE"))

(nil-use
  (path . "crates/my-lisp/src/layout.rs")
  (site . bool-false-tagged-as-nil)
  (class . boundary-compatibility)
  (owner . 220)
  (disposition . isolate)
  (note . "NanBox projection currently maps host Bool(false) to the Nil tag; must not regain language authority"))

(nil-use
  (path . "crates/my-lisp/src/eval/special_forms/json.rs")
  (site . json-null-to-nil)
  (class . boundary-compatibility)
  (owner . 220)
  (disposition . review)
  (note . "JSON null currently projects to Value::Nil; boundary mapping must stay distinct from truth semantics"))

(nil-use
  (path . "crates/my-lisp-lsp/src/protocol.rs")
  (site . proper-list-walk)
  (class . structural)
  (owner . 215)
  (disposition . keep)
  (note . "host observer stops proper-list traversal at Value::Nil"))

(nil-use
  (path . "crates/my-lisp-host/src/process_raw.rs")
  (site . proper-list-walk)
  (class . structural)
  (owner . 215)
  (disposition . keep)
  (note . "host mechanism stops list traversal at Value::Nil; not a truth decision"))
