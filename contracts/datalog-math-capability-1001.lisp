; Чинна семантична адреса арифметичної операції — точна драбина D5/D6.
; Це проєкція машинерії Datalog, а не нові резиденти чи ратифікація.
; Історичний плоский SID8 не визначає семантичної тотожності.
; Наявний C ABI v2 з полем semantic_id:u8 є НЕПЕРЕНЕСЕНИМ механізмом.
; До typed ingress його 8-бітні запити не мають статусу доказу D5/D6.
; Числові операнди у SENS належать D24+; signed-i64 лише машинерія острова.

(datalog-math-capability-3
  ((kernel . wsm-datalog-kernel)
   (machine-number-carrier . signed-i64)
   (sens-numeric-operand-domains . d24-plus)
   (expression-evaluator . native-island-mechanism)
   (semantic-authority . sens-exact-domain-ladder)
   (semantic-operation-selector . exact-domain-and-bits)
   (semantic-identity-fields . (domain bits))
   (payload-role . arguments-only)
   (operator-text-as-semantic-identity . forbidden)
   (historical-flat-sid8-authority . forbidden)
   (c-abi-v2-byte-selector . legacy-unmigrated)
   (c-abi-v2-is-domain-proof . ні)
   (unsupported-extension-policy . explicit)
   (witness . crates/wsm-datalog-kernel/tests/arithmetic_execution_1001.rs))

  ((domain . D5) (bits . 01010) (укр . додати) (mechanism . integer-add))
  ((domain . D5) (bits . 01011) (укр . відняти) (mechanism . integer-subtract))
  ((domain . D5) (bits . 10110) (укр . помножити) (mechanism . integer-multiply))
  ((domain . D5) (bits . 10111) (укр . частка)
   (mechanisms . (integer-divide integer-quotient)))
  ((domain . D6) (bits . 010011) (укр . модуль) (mechanism . integer-abs))
  ((domain . D6) (bits . 110101) (укр . найменше) (mechanism . integer-min))
  ((domain . D6) (bits . 110111) (укр . найбільше) (mechanism . integer-max))
  ((domain . D6) (bits . 010100) (укр . остача) (mechanism . integer-mod))

  ((failure . division-by-zero)
   (status . typed-kernel-error)
   (identity . datalog-math-division-by-zero))
  ((failure . overflow)
   (status . typed-kernel-error)
   (identity . datalog-math-overflow))
)
