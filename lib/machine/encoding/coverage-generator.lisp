; #487 — Lisp-owned encoder coverage policy and generator.
;
; Fast parity architecture:
;   full #175 XED evidence
;       ↓  legacy Rust --check (temporary migration oracle only)
;   committed coverage.lisp
;       ↑  exact byte parity
;   this Lisp policy ← compact admitted-pair projection
;
; The compact projection contains only (extension, ICLASS). Status/reason
; classification lives here. Once #175 emits the compact projection directly,
; the legacy Rust coverage generator can be deleted/narrowed.

(def encoder-coverage-str+
  (lambda args
    (reduce (lambda (acc s) (string-append acc s)) "" args)))

; Normalize structural equality to the old t/() predicate protocol so helper
; composition never relies on relation objects being truthy.
(def encoder-coverage-same?
  (lambda (left right)
    (cond
      ((equal? left right) (structural-relation same) t)
      ((equal? left right) (structural-relation distinct) (quote ())))))

(def encoder-coverage-pair=?
  (lambda (left right)
    (encoder-coverage-same? left right)))

; Pairwise rounds form a rope-like balanced concatenation tree. This avoids
; copying an ever-growing ~200 KB accumulator once per emitted coverage row.
(def encoder-coverage-concat-round
  (lambda (strings acc)
    (cond
      ((atom strings) (reverse acc))
      ((atom (cdr strings))
       (reverse-onto acc (list (car strings))))
      (t
       (encoder-coverage-concat-round
         (cdr (cdr strings))
         (cons
           (string-append (car strings) (second strings))
           acc))))))

(def encoder-coverage-balanced-concat
  (lambda (strings)
    (cond
      ((atom strings) "")
      ((atom (cdr strings)) (car strings))
      (t
       (encoder-coverage-balanced-concat
         (encoder-coverage-concat-round
           strings
           (quote ())))))))

(def encoder-coverage-partials
  (quote
    ((partial X86-BASE "ADD" "x86-encode-add-r64-r64 covers the register/register form only, of ADD's 18 XED forms")
     (partial X86-BASE "AND" "x86-encode-and-r64-r64 covers the register/register form only, sharing ADD's group-1 shape one opcode byte apart")
     (partial X86-BASE "CMP" "x86-encode-cmp-r64-r64 covers the register/register form only, sharing ADD's group-1 shape one opcode byte apart")
     (partial X86-BASE "DEC" "x86-encode-dec-r64 covers the group-5 register form (0xFF /1) only; the not64 legacy single-byte form and r/m64-memory forms are pending")
     (partial X86-BASE "INC" "x86-encode-inc-r64 covers the group-5 register form (0xFF /0) only; the not64 legacy single-byte form and r/m64-memory forms are pending")
     (partial X86-BASE "JB" "x86-encode-jb-rel8 covers the rel8 form (0x72) only; the rel32 form is pending")
     (partial X86-BASE "JBE" "x86-encode-jbe-rel8 covers the rel8 form (0x76) only; the rel32 form is pending")
     (partial X86-BASE "JL" "x86-encode-jl-rel8 covers the rel8 form (0x7C) only; the rel32 form is pending")
     (partial X86-BASE "JLE" "x86-encode-jle-rel8 covers the rel8 form (0x7E) only; the rel32 form is pending")
     (partial X86-BASE "JMP" "x86-encode-jmp-rel8 covers the unconditional rel8 form (0xEB) only; the rel32 (0xE9) and indirect register/memory (0xFF /4) forms are pending")
     (partial X86-BASE "JNB" "x86-encode-jnb-rel8 covers the rel8 form (0x73) only; the rel32 form is pending")
     (partial X86-BASE "JNBE" "x86-encode-jnbe-rel8 covers the rel8 form (0x77) only; the rel32 form is pending")
     (partial X86-BASE "JNL" "x86-encode-jnl-rel8 covers the rel8 form (0x7D) only; the rel32 form is pending")
     (partial X86-BASE "JNLE" "x86-encode-jnle-rel8 covers the rel8 form (0x7F) only; the rel32 form is pending")
     (partial X86-BASE "JNO" "x86-encode-jno-rel8 covers the rel8 form (0x71) only; the rel32 form is pending")
     (partial X86-BASE "JNP" "x86-encode-jnp-rel8 covers the rel8 form (0x7B) only; the rel32 form is pending")
     (partial X86-BASE "JNS" "x86-encode-jns-rel8 covers the rel8 form (0x79) only; the rel32 form is pending")
     (partial X86-BASE "JNZ" "x86-encode-jnz-rel8 covers the rel8 form (0x75) only; the rel32 form is pending")
     (partial X86-BASE "JO" "x86-encode-jo-rel8 covers the rel8 form (0x70) only; the rel32 form is pending")
     (partial X86-BASE "JP" "x86-encode-jp-rel8 covers the rel8 form (0x7A) only; the rel32 form is pending")
     (partial X86-BASE "JS" "x86-encode-js-rel8 covers the rel8 form (0x78) only; the rel32 form is pending")
     (partial X86-BASE "JZ" "x86-encode-jz-rel8 covers the rel8 form (0x74) only; the rel32 form is pending")
     (partial X86-BASE "MOV" "x86-encode-mov-r64-imm64 (any of 16 GPRs, non-negative immediate; negative imm64 is admitted but fails closed at the real host boundary -- see #176's negative_mov_r64_imm64_is_admitted_but_fails_closed_at_the_real_host_boundary), x86-encode-mov-r64-mem-disp8, and x86-encode-mov-mem-disp8-r64 (any of 16 GPRs as base/dest, full disp8 range -128..127) cover 3 of MOV's 22 XED forms; the 32/64-bit-displacement, SIB-index, and other MOV forms are pending")
     (partial X86-BASE "NEG" "x86-encode-neg-r64 covers the group-3 register form (0xF7 /3) only; r/m64-memory forms are pending")
     (partial X86-BASE "NOT" "x86-encode-not-r64 covers the group-3 register form (0xF7 /2) only; r/m64-memory forms are pending")
     (partial X86-BASE "OR" "x86-encode-or-r64-r64 covers the register/register form only, sharing ADD's group-1 shape one opcode byte apart")
     (partial X86-BASE "POP" "x86-encode-pop-r64 covers the single-register 0x58+rd form only; POP r/m64-memory/segment forms are pending")
     (partial X86-BASE "PUSH" "x86-encode-push-r64 covers the single-register 0x50+rd form only; PUSH imm/r-m64-memory/segment forms are pending")
     (partial X86-BASE "RET_NEAR" "x86-encode-ret covers the no-operand near-return form only; the imm16 stack-adjust variant is pending")
     (partial X86-BASE "SUB" "x86-encode-sub-r64-r64 covers the register/register form only, sharing ADD's group-1 shape one opcode byte apart")
     (partial X86-BASE "TEST" "x86-encode-test-r64-r64 covers the register/register form (0x85 /r) only, reusing ADD's group-1 shape")
     (partial X86-BASE "XOR" "x86-encode-xor-r64-r64 covers the register/register form only, sharing ADD's group-1 shape one opcode byte apart"))))



; Both index rows and partial rows use positions:
;   tag, extension, ICLASS, ...
; Compare by ICLASS first, then extension, matching the legacy coverage order.
(def encoder-coverage-row-key<?
  (lambda (left right)
    (let ((left-iclass (third left))
          (right-iclass (third right)))
      (cond
        ((string<? left-iclass right-iclass) t)
        ((encoder-coverage-same? left-iclass right-iclass)
         (string<?
           (symbol->string (second left))
           (symbol->string (second right))))
        (t (quote ()))))))

(def encoder-coverage-row-key=?
  (lambda (left right)
    (and
      (encoder-coverage-same? (second left) (second right))
      (encoder-coverage-same? (third left) (third right)))))

(def encoder-coverage-not-yet-reason
  (lambda (extension)
    (cond
      ((member? extension (quote (AVX AVX2 FMA3 BMI1 BMI2 F16C)))
       "VEX-prefix encoding not yet implemented")
      ((encoder-coverage-same? extension (quote X87))
       "x87 stack-register encoding not yet implemented")
      ((encoder-coverage-same? extension (quote MMX))
       "MMX opcode-map encoding not yet implemented")
      ((member?
         extension
         (quote (SSE SSE2 SSE3 SSSE3 SSE4.1+SSE4.2)))
       "legacy SSE mandatory-prefix/ModRM encoding not yet implemented")
      ((member? extension (quote (AES-NI PCLMULQDQ)))
       "SSE-prefixed crypto encoding not yet implemented")
      ((encoder-coverage-same? extension (quote XSAVE))
       "XSAVE control-state encoding not yet implemented")
      ((encoder-coverage-same? extension (quote MPX))
       "BND-register encoding not yet implemented")
      ((encoder-coverage-same? extension (quote SGX))
       "ENCLS/ENCLU leaf-function encoding not yet implemented")
      ((member? extension (quote (RDRAND RDSEED)))
       "0F C7 opcode-map encoding not yet implemented")
      ((encoder-coverage-same? extension (quote CLFLUSHOPT))
       "cache-management opcode encoding not yet implemented")
      ((encoder-coverage-same? extension (quote X86-64))
       "long-mode-specific BASE forms pending family-by-family rollout")
      (t
       "remaining BASE forms pending family-by-family rollout"))))

(def encoder-coverage-render-row
  (lambda (row partial)
    (let* ((extension (second row))
           (iclass (third row))
           (status
             (cond
               ((atom partial) (quote not-yet-implemented))
               (t (quote partial))))
           (reason
             (cond
               ((atom partial)
                (encoder-coverage-not-yet-reason extension))
               (t (fourth partial)))))
      (encoder-coverage-str+
        "  (coverage\n"
        "    (iclass " (write-to-string iclass) ")\n"
        "    (extension " (symbol->string extension) ")\n"
        "    (status " (symbol->string status) ")\n"
        "    (reason " (write-to-string reason) "))\n"))))

; One tail-recursive merge performs classification, stale-partial detection,
; rendering and partial counting. No 1175×32 repeated lookup remains.
; Result = (rendered-rows partial-count stale-partial?).
(def encoder-coverage-build-onto
  (lambda (index-rows partials rendered count)
    (cond
      ((atom index-rows)
       (cond
         ((atom partials)
          (list (reverse rendered) count (quote ())))
         (t
          (list (reverse rendered) count t))))
      ((atom partials)
       (encoder-coverage-build-onto
         (cdr index-rows)
         partials
         (cons
           (encoder-coverage-render-row (car index-rows) (quote ()))
           rendered)
         count))
      (t
       (let ((index-row (car index-rows))
             (partial-row (car partials)))
         (cond
           ((encoder-coverage-row-key=? index-row partial-row)
            (encoder-coverage-build-onto
              (cdr index-rows)
              (cdr partials)
              (cons
                (encoder-coverage-render-row index-row partial-row)
                rendered)
              (+ count 1)))
           ((encoder-coverage-row-key<? partial-row index-row)
            ; A claimed partial sorts before the next admitted row: it is
            ; absent/stale or the partial inventory is non-deterministic.
            (list (reverse rendered) count t))
           (t
            (encoder-coverage-build-onto
              (cdr index-rows)
              partials
              (cons
                (encoder-coverage-render-row index-row (quote ()))
                rendered)
              count))))))))

(def encoder-coverage-index-unique?
  (lambda (rows previous)
    (cond
      ((atom rows) t)
      ((atom previous)
       (encoder-coverage-index-unique?
         (cdr rows)
         (car rows)))
      ((encoder-coverage-row-key=? (car rows) previous)
       (quote ()))
      (t
       (encoder-coverage-index-unique?
         (cdr rows)
         (car rows))))))

(def encoder-coverage-index-form
  (car
    (read-all
      (read-file
        "lib/machine/encoding/admitted-iclass-index.lisp"))))

(def encoder-coverage-index-count
  (second (second encoder-coverage-index-form)))

(def encoder-coverage-index-rows
  (cdr (cdr encoder-coverage-index-form)))

(def encoder-coverage-form-count
  (length encoder-coverage-index-rows))

(def encoder-coverage-partials-valid?
  (lambda (index-rows partials)
    (cond
      ((atom partials) t)
      ((atom index-rows) (quote ()))
      (t
       (let ((index-row (car index-rows))
             (partial-row (car partials)))
         (cond
           ((encoder-coverage-row-key=? index-row partial-row)
            (encoder-coverage-partials-valid?
              (cdr index-rows)
              (cdr partials)))
           ((encoder-coverage-row-key<? partial-row index-row)
            (quote ()))
           (t
            (encoder-coverage-partials-valid?
              (cdr index-rows)
              partials))))))))

(def encoder-coverage-index-valid?
  (and
    (encoder-coverage-same?
      encoder-coverage-form-count
      encoder-coverage-index-count)
    (encoder-coverage-index-unique?
      encoder-coverage-index-rows
      (quote ()))
    (encoder-coverage-partials-valid?
      encoder-coverage-index-rows
      encoder-coverage-partials)))

(def encoder-coverage-committed-row-matches?
  (lambda (index-row coverage-row partial-row)
    (cond
      ((atom coverage-row) (quote ()))
      ((equal? (length coverage-row) 5)
       (structural-relation same)
       (let* ((expected-status
                (cond
                  ((atom partial-row) (quote not-yet-implemented))
                  (t (quote partial))))
              (expected-reason
                (cond
                  ((atom partial-row)
                   (encoder-coverage-not-yet-reason
                     (second index-row)))
                  (t (fourth partial-row)))))
         (and
           (encoder-coverage-same?
             (car coverage-row)
             (quote coverage))
           (encoder-coverage-same?
             (car (second coverage-row))
             (quote iclass))
           (encoder-coverage-same?
             (second (second coverage-row))
             (third index-row))
           (encoder-coverage-same?
             (car (third coverage-row))
             (quote extension))
           (encoder-coverage-same?
             (second (third coverage-row))
             (second index-row))
           (encoder-coverage-same?
             (car (fourth coverage-row))
             (quote status))
           (encoder-coverage-same?
             (second (fourth coverage-row))
             expected-status)
           (encoder-coverage-same?
             (car (fifth coverage-row))
             (quote reason))
           (encoder-coverage-same?
             (second (fifth coverage-row))
             expected-reason))))
      (t (quote ())))))

(def encoder-coverage-projection-rows-valid?
  (lambda (index-rows coverage-rows partials)
    (cond
      ((atom index-rows)
       (and (atom coverage-rows) (atom partials)))
      ((atom coverage-rows)
       (quote ()))
      ((atom partials)
       (and
         (encoder-coverage-committed-row-matches?
           (car index-rows)
           (car coverage-rows)
           (quote ()))
         (encoder-coverage-projection-rows-valid?
           (cdr index-rows)
           (cdr coverage-rows)
           partials)))
      (t
       (let ((index-row (car index-rows))
             (coverage-row (car coverage-rows))
             (partial-row (car partials)))
         (cond
           ((encoder-coverage-row-key=? index-row partial-row)
            (and
              (encoder-coverage-committed-row-matches?
                index-row
                coverage-row
                partial-row)
              (encoder-coverage-projection-rows-valid?
                (cdr index-rows)
                (cdr coverage-rows)
                (cdr partials))))
           ((encoder-coverage-row-key<? partial-row index-row)
            (quote ()))
           (t
            (and
              (encoder-coverage-committed-row-matches?
                index-row
                coverage-row
                (quote ()))
              (encoder-coverage-projection-rows-valid?
                (cdr index-rows)
                (cdr coverage-rows)
                partials)))))))))

(def encoder-coverage-projection-valid?
  (lambda (coverage-form)
    (cond
      ((atom coverage-form) (quote ()))
      ((equal? (length coverage-form) (+ encoder-coverage-form-count 3))
       (structural-relation same)
       (and
         (encoder-coverage-same?
           (car coverage-form)
           (quote x86-encoder-coverage/1))
         (encoder-coverage-same?
           (car (second coverage-form))
           (quote form-count))
         (encoder-coverage-same?
           (second (second coverage-form))
           encoder-coverage-form-count)
         (encoder-coverage-same?
           (car (third coverage-form))
           (quote partial-count))
         (encoder-coverage-same?
           (second (third coverage-form))
           (length encoder-coverage-partials))
         (encoder-coverage-projection-rows-valid?
           encoder-coverage-index-rows
           (cdr (cdr (cdr coverage-form)))
           encoder-coverage-partials)))
      (t (quote ())))))

(def encoder-coverage-render
  (lambda ()
    (let* ((build
             (encoder-coverage-build-onto
               encoder-coverage-index-rows
               encoder-coverage-partials
               (quote ())
               0))
           (rendered-rows (car build))
           (partial-count (second build))
           (stale-partial? (third build))
           (prelude
             (encoder-coverage-str+
               "; GENERATED by `cargo xtask generate-encoder-coverage` -- do not hand-edit.\n"
               "; Source: lib/machine/xed/generated/machine-evidence.lisp (#175) cross-\n"
               "; referenced against lib/machine/encoding/x86-64.lisp (#176). Every ICLASS\n"
               "; admitted by #175 appears here exactly once: `partial` names a real Lisp\n"
               "; encoder covering at least one of its forms, `not-yet-implemented` is an\n"
               "; explicit, justified gap. There is no third, silent outcome (#176).\n"
               "\n"
               "(x86-encoder-coverage/1\n"
               "  (form-count " (number->string encoder-coverage-form-count) ")\n"
               "  (partial-count " (number->string partial-count) ")\n")))
      (cond
        ((encoder-coverage-same? stale-partial? t)
         (quote ()))
        (t
         (encoder-coverage-str+
           prelude
           (encoder-coverage-balanced-concat rendered-rows)
           ")\n"))))))
