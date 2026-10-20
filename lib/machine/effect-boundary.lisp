; #4342 — канонічна межа машинних ефектів, незалежна від цільової платформи.
;
; Файл описує тільки межу повноважень. Він не встановлює перелік
; інструкцій процесора й не ратифікує універсальну віртуальну ISA.
;
; Семантику вже визначають контракт мови й ратифіковані точнодоменні
; закони. Машинний ефект описує лише механізм виконання відомого значення.
; Форми конкретної платформи є наступною проєкцією: вони можуть
; відмовити у виконанні, не змінюючи самого мовного закону.

(machine-effect-boundary/1
  (role target-neutral-machine-mechanism)
  (semantic-authority upstream-only)
  (semantic-input language-contract.lisp+ratified-domain-laws)
  (machine-effect-semantic-authority forbidden)

  (canonical-machine-effect target-neutral)
  (machine-effect-contract-owner sens)
  (effect-vocabulary-status bounded-derived-from-witness)
  (effect-vocabulary-from-isa forbidden)
  (effect-vocabulary-from-target-profile forbidden)
  (effect-vocabulary-from-compiler-ir forbidden)
  (global-machine-opcode-enum forbidden)
  (semantic-id-from-machine-effect forbidden)
  (semantic-id-from-target-projection forbidden)

  (projection-direction machine-effect-to-target)
  (reverse-projection-authority forbidden)
  (target-specific-register-before-projection forbidden)
  (target-specific-encoding-before-projection forbidden)
  (target-specific-feature-before-projection forbidden)

  (target-projection-admission fail-closed)
  (target-projection-rejection named)
  (target-projection-may-be-replaceable required)
  (semantic-observable-preserved required)

  ; #4381 — через композицію ефектів не можна передавати неявний стан цілі.
  ; Усі семантично значущі виходи належать канонічному об'єкту ефекту.
  ; Цільова машина може здійснити їх через прапорці процесора,
  ; перенесення розрядів, маски предикатів або явні провідники.
  ; Наступний ефект споживає лише явно названі канонічні виходи.
  (effect-output-contract explicit-complete)
  (effect-explicit-outputs required)
  (effect-hidden-target-state forbidden)
  (effect-output-consumer explicit-only)
  (target-hidden-state-materialization projection-only)
  (target-hidden-state-semantic-channel forbidden)
  (effect-output-arity target-invariant)

  (machine-block-container lib/machine/block.lisp)
  (first-proof-slice bounded-vertical-witness)
  (first-proof-status contract-seam-only)
  (diagnostic machine-effect-boundary-violation))
