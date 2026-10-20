; #1132 — Контракт початкового завантаження першого ядра.
; Дані контракту; історичні назви лишаються як дані, не call-heads.

(core1-bootstrap-contract/1
  ((identity . authority)
   (owner . sens)
   (profile . core1)
   (semantic-authority-transfer . forbidden)
   (seed-may-mint-sid . forbidden)
   (seed-may-redefine-current-sid . forbidden))

  ((identity . stage-lineage)
   (stages .
     (s0-mccarthy-eval
      s1-core1-lisp
      s2-lisp-authored-compiler
      s3-compiled-compiler
      s4-self-compiled-compiler
      s5-fixed-point-comparison))
   (generation-provenance . required)
   (same-source-fixed-point . required))

  ((identity . s0-substrate)
   (repository . juv4uk/mccarthy-eval)
   (pinned-commit . "1ae9745b66a1439c1929b0d9038c680567118a58")
   (surface-case . exact-uppercase)
   (historical-forms .
     (як-є ATOM EQ COND CAR CDR CONS LABEL LAMBDA DEFINE FUNCTION FUNARG))
   (historical-control-values . (T NIL))
   (first-class-closures . explicit-function-funarg)
   (naked-lambda-as-value . historically-unavailable))

  ((identity . uk-projection)
   (current-forms .
     (як-є атом? тотожне? за-умовою перше решта сполучити визначити функція))
   (decimals . required)
   (sid8-call-heads . retired)))
