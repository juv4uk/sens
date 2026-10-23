; #735 — Свідки точнодоменних функцій SENS та окреме походження ABI.
; Семантичні координати і повні імена «укр» походять винятково з
; ратифікованих lib/domains/d3.lisp, d4.lisp, d6.lisp.
; Відображення свідка не створює функції чи механізму виконання.
; identity — (домен, точні біти) у перевірюваному записі «D*:біти»;
; probe-id — старий 8-бітний ключ **лише** історичного ABI-випробування,
; він не дорівнює identity і не може переадресувати виклик у SENS.
; Живе виконання SENS має бути підтверджене незалежним runtime-свідком.

(domain-kernel-witness-map-2

  ; --- Canon 0 ---

  (domain-witness
    (identity . "D3:000")
    (укр . ())
    (en-name  . ())
    (witnesses
      (witness (kernel . sens)     (probe-id . 00000000) (status . historical)))
    (note . "Canon 0 — первинний ground object. Жоден island поки не виконує ()."))

  ; --- Примітиви Д3 з українськими викличними іменами ---

  (domain-witness
    (identity . "D3:001")
    (укр . як-є)
    (en-name  . quote)
    (witnesses
      (witness (kernel . sens)     (probe-id . 00000001) (status . live))
      (witness (kernel . common-lisp) (probe-id . 00000001) (status . integration-gated)))
    (note . "quote: my-lisp evaluator є live witness; CL gated через WSM_COMMON_LISP_INTEGRATION."))

  (domain-witness
    (identity . "D3:010")
    (укр . атом?)
    (en-name  . atom)
    (witnesses
      (witness (kernel . sens)     (probe-id . 00000010) (status . live))
      (witness (kernel . prolog)      (probe-id . 00000010) (status . absent))
      (witness (kernel . clips)       (probe-id . 00000010) (status . absent)))
    (note . "atom: Prolog/CLIPS мають native atom-check, але ABI witness ще не відображено."))

  (domain-witness
    (identity . "D3:101")
    (укр . тотожне?)
    (en-name  . eq)
    (witnesses
      (witness (kernel . sens)     (probe-id . 00000011) (status . live)))
    (note . "eq: current Prolog PROBE_ID=00000011 is transport provenance only; no Prolog EQ semantic witness is claimed."))

  (domain-witness
    (identity . "D3:111")
    (укр . сполучити)
    (en-name  . cons)
    (witnesses
      (witness (kernel . sens)     (probe-id . 00000100) (status . live))
      (witness (kernel . common-lisp) (probe-id . 00000100) (status . integration-gated)))
    (note . "cons: CL is a bounded semantic witness. Datalog PROBE_ID=00000100 is transport provenance only."))

  (domain-witness
    (identity . "D3:100")
    (укр . перше)
    (en-name  . car)
    (witnesses
      (witness (kernel . sens)     (probe-id . 00000101) (status . live))
      (witness (kernel . common-lisp) (probe-id . 00000101) (status . integration-gated)))
    (note . "car: CL witness live коли задано WSM_COMMON_LISP_INTEGRATION — CL:CAR adapter."))

  (domain-witness
    (identity . "D3:011")
    (укр . решта)
    (en-name  . cdr)
    (witnesses
      (witness (kernel . sens)     (probe-id . 00000110) (status . live))
      (witness (kernel . common-lisp) (probe-id . 00000110) (status . integration-gated)))
    (note . "cdr: CL is a bounded semantic witness. CLIPS PROBE_ID=00000110 is transport provenance only."))

  (domain-witness
    (identity . "D3:110")
    (укр . за-умовою)
    (en-name  . cond)
    (witnesses
      (witness (kernel . sens)     (probe-id . 00000111) (status . live))
      (witness (kernel . prolog)      (probe-id . 00000111) (status . absent))
      (witness (kernel . clips)       (probe-id . 00000111) (status . absent)))
    (note . "cond: Prolog/CLIPS мають native branching, але ABI probe ще немає."))

  ; --- Д4 функція/визначити та Д6 нехай ---

  (domain-witness
    (identity . "D4:0010")
    (укр . функція)
    (en-name  . lambda)
    (witnesses
      (witness (kernel . sens)     (probe-id . 00001000) (status . live))
      (witness (kernel . common-lisp) (probe-id . 00001000) (status . integration-gated)))
    (note . "lambda: CL має native lambda; witness gated через integration env var."))

  (domain-witness
    (identity . "D4:0011")
    (укр . визначити)
    (en-name  . def)
    (witnesses
      (witness (kernel . sens)     (probe-id . 00001001) (status . live)))
    (note . "def: my-lisp-owned binding form. Island-відповідник не відображено."))

  (domain-witness
    (identity . "D6:001000")
    (укр . нехай)
    (en-name  . let)
    (witnesses
      (witness (kernel . sens)     (probe-id . 00001010) (status . live))
      (witness (kernel . common-lisp) (probe-id . 00001010) (status . integration-gated))
      (witness (kernel . prolog)      (probe-id . 00001010) (status . absent)))
    (note . "let: CL має native let. Prolog не має прямого відповідника."))

  ; Старий DEFMACRO/SID8:00001011 не отримує вигаданої сучасної
  ; координати. Історичний witness лишається у попередньому Git blob.

)


; ---------------------------------------------------------------------------
; Механічне походження ABI — явно НЕ семантичні свідки виконання.
; Ці рядки доводять лише, що непрозорий u8 переживає спільну межу, поки
; рідне корисне навантаження виконується названим ядром.
; ---------------------------------------------------------------------------

(opaque-kernel-probe-evidence-1
  (probe
    (kernel . prolog)
    (probe-id . "00000011")
    (semantic-witness . no)
    (evidence . "crates/wsm-prolog-kernel/tests/c_abi_semantic_witness.rs"))
  (probe
    (kernel . datalog)
    (probe-id . "00000100")
    (semantic-witness . no)
    (evidence . "crates/wsm-datalog-kernel/tests/c_abi_semantic_witness.rs"))
  (probe
    (kernel . clips)
    (probe-id . "00000110")
    (semantic-witness . no)
    (evidence . "crates/wsm-clips-kernel/tests/c_abi_semantic_witness.rs")))
