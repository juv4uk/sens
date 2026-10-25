; КОНТРАКТ SENS 12.0 — ВЛАСНИЦЬКИ РАТИФІКОВАНО 2026-10-25.
; Пряме рішення власника 2026-10-25: «затвердити». Контракт чинний.
; Це нормативні декларативні дані SENS, не нові функціональні opcode
; і не доказ, що всі фізичні міграції вже завершені.
;
; Ратифіковані джерела-попередники та збережена спадкоємність:
; language-contract.lisp (11.9 — історичний стан до контракту 12.0);
; contracts/answer-contract.lisp;
; contracts/bija3-l1-l5-ratification.lisp;
; contracts/numeric-domains-ratification.lisp (D12 від 2026-10-24).

(
  (schema . sens-language-contract-12/1)
  ; Version is textual contract metadata, never a numeric SENS operand.
  (version . "12.0")
  (date . "2026-10-25")
  (status . owner-ratified-active)
  (owner-decision-requested . fulfilled)
  (owner-ratification . "Пряме рішення власника у розмові 2026-10-25: затвердити")
  (authority-path . "contracts/language-contract-12.lisp")
  (implementation-completeness . not-asserted)
  (legacy-runtime-removal . required-not-yet-verified)
  (supersedes . ("language-contract.lisp:11.9" "legacy-SID8-Sens8-execution-admission"))
  (preserves . ("D1-D11 ratified resident identities" "D3 L1-L5" "D10 whole-domain authority" "D12 numeric-first decision 2026-10-24"))
  (scope . (semantic-identity predicates derived-results control binary-machine legacy-retirement numeric-ladder execution-evidence))

  ; K12.1. Предикат не є пошуком і не має третього значення істинності.
  (d1-predicates
    . ((domain . D1)
       (yes . D1:1)
       (no . D1:0)
       (result-set . (D1:0 D1:1))
       (role . exact-answer-to-admitted-predicate)
       (number-coercion . forbidden)
       (list-coercion . forbidden)
       (generic-truthiness . forbidden)
       (empty-as-false . forbidden)
       (empty-as-third-predicate-value . forbidden)))

  ; K12.2. () — структурний пустий список; пошук може ним відповісти.
  ; Значення no-witness виникає в законі ПОХІДНОЇ функції, не в D1.
  (d3-empty
    . ((identity . D3:000)
       (value . ())
       (role . empty-list)
       (structural-owner . D3)
       (predicate-answer . no)
       (derived-query-result . admissible-under-specific-function-law)
       (no-match . admissible)
       (insufficient-evidence . admissible-under-named-query-completeness-law)
       (multiple-candidates-no-unique-choice . admissible-under-named-query-law)
       (unknown-default-without-law . forbidden)
       (error-as-empty . forbidden)
       (distinguish-from-D1:0 . mandatory)))

  ; K12.3. Найпростіший D3 не стає тризначним чи тричастинним.
  (primitive-control
    . ((atom-result . (D1:0 D1:1))
       (eq-result . (D1:0 D1:1))
       (eq-operands . admitted-atoms-only)
       (eq-outside-domain . named-Type)
       (cond-clause . (test expression))
       (cond-test . (D1:0 D1:1))
       (cond-on-D1:1 . select-expression)
       (cond-on-D1:0 . continue)
       (cond-on-D3:000 . named-Type)
       (cond-after-exhaustion . D3:000)
       (cond-three-part . forbidden)
       (predicate-with-unknown-bit . forbidden)))

  ; K12.4. Розумні відповіді є композицією, а не новим EQ/ATOM/COND.
  (derived-reasoning
    . ((allowed-results . (D1:1 D1:0 D3:000 domain-value structured-result))
       (d1-yes . proved-by-query-law)
       (d1-no . disproved-by-query-law)
       (empty-query-result . no-selected-witness-under-query-law)
       (minimal-answer . existing-result-only)
       (explanation . separate-derived-query-on-request)
       (explanation-content . evidence-or-reason-when-available)
       (explanation-does-not-change-answer . mandatory)
       (no-new-explanation-primitive . mandatory)
       (no-proof-is-not-refutation . mandatory)
       (conflicting-evidence . preserve-as-data-or-empty-only-under-named-law)
       (invalid-input . named-error)
       (unavailable-mechanism . blocked-mechanism)
       (empty-is-not-error . mandatory)
       (no-implicit-D3-to-D1 . mandatory)))

  ; K12.5. Тотожність SENS тільки двійкова й доменно-кваліфікована.
  (binary-source-and-machine
    . ((semantic-identity . (exact-domain exact-width exact-bit-word admitted-law))
       (canonical-language . exact-domain-qualified-binary)
       (machine-execution . binary-only)
       (d2-role . exact-structural-framing)
       (d7-role . text-data-only)
       (unicode-surfaces . projection-only)
       (lisp-human-readable . temporary-reversible-projection-and-migration-source)
       (width-tags-as-language . forbidden)
       (sid-slot-as-language . forbidden)
       (binary-to-decimal-to-binary-semantic-bridge . forbidden)
       (leading-zero-loss . forbidden)
       (codec-assigns-semantics . forbidden)
       (source-parser-infers-domain-from-byte-width . forbidden)))

  ; K12.6. Видаляємо спадщину з АКТИВНОГО виконання, не з історії.
  (flat-eight-retirement
    . ((retired-identities . (SID8 Sens8 Function8))
       (active-semantic-identity . forbidden)
       (active-reader-fallback . forbidden)
       (active-evaluator-fallback . forbidden)
       (active-compiler-fallback . forbidden)
       (active-zig-transport-lowering . forbidden)
       (active-runtime-compatibility-toggle . forbidden)
       (flat8-to-current-domain-implicit-conversion . forbidden)
       (historical-provenance . archive-only)
       (archived-files-as-executable . forbidden)
       (old-corpus-migration . explicit-with-source-and-target-and-negative-witness)
       (unmigrated-execution . fail-closed)
       (eight-bit-physical-byte . allowed-as-transport-not-as-semantic-identity)))

  ; K12.7. Числова драбина починається з D12, а не D24.
  (numeric-mathematics
    . ((authority . "contracts/numeric-domains-ratification.lisp:numeric-d12-start-extension-1")
       (first-domain . D12)
       (domain-sequence . (D12 D24 D48 D96 D192))
       (successor-rule . double-width)
       (integer-representation . signed-twos-complement)
       (exact-arithmetic . mandatory)
       (overflow . promote-to-smallest-admitted-successor)
       (truncation . forbidden)
       (implicit-rounded-float . forbidden)
       (exact-ratio . reduced-composition)
       (denominator-zero . named-error)
       (mixed-domain-implicit-coercion . forbidden)
       (D1-as-number . forbidden)
       (D7-digits-as-number . forbidden)
       (D12-as-callable-codebook . forbidden)
       (host-decimal-intermediate-as-semantics . forbidden)
       (numeric-physical-admission . proof-required-per-route)))

  ; K12.8. Міграція і реліз — окремі від зміни тексту контракту.
  (ratification-and-implementation
    . ((contract-activation . owner-approved-2026-10-25)
       (historical-11.9-record . retained-readonly-as-provenance)
       (native-sens-required . yes)
       (codec-roundtrip-required . yes)
       (positive-negative-witnesses . yes)
       (source-sha-and-physical-sha . required)
       (d1-d3-cond-legacy-triple-rejection . required)
       (sid8-sens8-active-execution-inventory . required-zero)
       (d12-exact-boundary-tests . required)
       (release-GO . forbidden-until-owner-decision)
       (partial-implementation-is-ratification . no)
       (CI-green-on-old-SHA-is-current-proof . no)))
)
