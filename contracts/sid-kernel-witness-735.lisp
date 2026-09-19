; #735 — Експериментальна карта SID → kernel witness.
; Повноваження: цей файл відображає, *хто може виконати* семантичну
; ідентичність, а НЕ *що вона означає*. Семантична влада лишається у
; lib/surface/semantic-registry.lisp (sr/2) та законах мови.
;
; Схема одного запису:
;   (sid-witness
;     (sid        . "BITSTRING")       ; непрозорий 8-бітний SID з sr/2
;     (en-name    . SYMBOL)            ; лише довідково, поле en з registry
;     (witnesses  . LIST)              ; нуль або більше executable witness-ів
;     (note       . "STRING"))         ; необов'язкове пояснення
;
; Кожен witness:
;   (witness
;     (kernel    . SYMBOL)   ; my-lisp | common-lisp | prolog | clips | datalog
;     (probe-id  . BITSTRING) ; байт u8 для ядра (має збігатися з ABI test)
;     (status    . SYMBOL))  ; live | integration-gated | historical | absent
;
; Відсутність witness-а коректна: вона фіксує, що жодне ядро поки не
; виконує цю ідентичність, а не те, що ідентичність не визначена.
;
; Зміни карти не можуть перенумеровувати SID. Колонка SID read-only;
; колонку witnesses можна змінювати вільно.

(sid-kernel-witness-map/1

  ; --- Canon 0 ---

  (sid-witness
    (sid      . "00000000")
    (en-name  . ())
    (witnesses
      (witness (kernel . my-lisp)     (probe-id . "00000000") (status . live)))
    (note . "Canon 0 — первинний ground object. Жоден island поки не виконує ()."))

  ; --- Сім примітивів Маккарті (SID 00000001..00000111) ---

  (sid-witness
    (sid      . "00000001")
    (en-name  . quote)
    (witnesses
      (witness (kernel . my-lisp)     (probe-id . "00000001") (status . live))
      (witness (kernel . common-lisp) (probe-id . "00000001") (status . integration-gated)))
    (note . "quote: my-lisp evaluator є live witness; CL gated через WSM_COMMON_LISP_INTEGRATION."))

  (sid-witness
    (sid      . "00000010")
    (en-name  . atom)
    (witnesses
      (witness (kernel . my-lisp)     (probe-id . "00000010") (status . live))
      (witness (kernel . prolog)      (probe-id . "00000010") (status . absent))
      (witness (kernel . clips)       (probe-id . "00000010") (status . absent)))
    (note . "atom: Prolog/CLIPS мають native atom-check, але ABI witness ще не відображено."))

  (sid-witness
    (sid      . "00000011")
    (en-name  . eq)
    (witnesses
      (witness (kernel . my-lisp)     (probe-id . "00000011") (status . live))
      (witness (kernel . prolog)      (probe-id . "00000011") (status . live)
        (evidence . "crates/wsm-prolog-kernel/tests/c_abi_semantic_witness.rs")))
    (note . "eq: Prolog ABI witness live — PROBE_ID=0b00000011 у c_abi_semantic_witness.rs."))

  (sid-witness
    (sid      . "00000100")
    (en-name  . cons)
    (witnesses
      (witness (kernel . my-lisp)     (probe-id . "00000100") (status . live))
      (witness (kernel . common-lisp) (probe-id . "00000100") (status . integration-gated))
      (witness (kernel . datalog)     (probe-id . "00000100") (status . live)
        (evidence . "crates/wsm-datalog-kernel/tests/c_abi_semantic_witness.rs")))
    (note . "cons: Datalog ABI live (PROBE_ID=0b00000100). CL gated через env var."))

  (sid-witness
    (sid      . "00000101")
    (en-name  . car)
    (witnesses
      (witness (kernel . my-lisp)     (probe-id . "00000101") (status . live))
      (witness (kernel . common-lisp) (probe-id . "00000101") (status . integration-gated)))
    (note . "car: CL witness live коли задано WSM_COMMON_LISP_INTEGRATION — CL:CAR adapter."))

  (sid-witness
    (sid      . "00000110")
    (en-name  . cdr)
    (witnesses
      (witness (kernel . my-lisp)     (probe-id . "00000110") (status . live))
      (witness (kernel . common-lisp) (probe-id . "00000110") (status . integration-gated))
      (witness (kernel . clips)       (probe-id . "00000110") (status . live)
        (evidence . "crates/wsm-clips-kernel/tests/c_abi_semantic_witness.rs")))
    (note . "cdr: CLIPS ABI live (PROBE_ID=0b00000110). CL gated."))

  (sid-witness
    (sid      . "00000111")
    (en-name  . cond)
    (witnesses
      (witness (kernel . my-lisp)     (probe-id . "00000111") (status . live))
      (witness (kernel . prolog)      (probe-id . "00000111") (status . absent))
      (witness (kernel . clips)       (probe-id . "00000111") (status . absent)))
    (note . "cond: Prolog/CLIPS мають native branching, але ABI probe ще немає."))

  ; --- Родина lambda / def / let (SID 00001000..00001010) ---

  (sid-witness
    (sid      . "00001000")
    (en-name  . lambda)
    (witnesses
      (witness (kernel . my-lisp)     (probe-id . "00001000") (status . live))
      (witness (kernel . common-lisp) (probe-id . "00001000") (status . integration-gated)))
    (note . "lambda: CL має native lambda; witness gated через integration env var."))

  (sid-witness
    (sid      . "00001001")
    (en-name  . def)
    (witnesses
      (witness (kernel . my-lisp)     (probe-id . "00001001") (status . live)))
    (note . "def: my-lisp-owned binding form. Island-відповідник не відображено."))

  (sid-witness
    (sid      . "00001010")
    (en-name  . let)
    (witnesses
      (witness (kernel . my-lisp)     (probe-id . "00001010") (status . live))
      (witness (kernel . common-lisp) (probe-id . "00001010") (status . integration-gated))
      (witness (kernel . prolog)      (probe-id . "00001010") (status . absent)))
    (note . "let: CL має native let. Prolog не має прямого відповідника."))

  ; --- defmacro (SID 00001011) ---

  (sid-witness
    (sid      . "00001011")
    (en-name  . defmacro)
    (witnesses
      (witness (kernel . my-lisp)     (probe-id . "00001011") (status . live))
      (witness (kernel . common-lisp) (probe-id . "00001011") (status . integration-gated)))
    (note . "defmacro: CL має defmacro, але CL ABI witness ще його не виконує."))

)
