; SENS-owned witness for the actual Lisp predicate world?.
; All primitive operators retain exact identities: D3 EQ/QUOTE and D1 bits.
; world? is a local Lisp binding, not an admitted D10 callable identity; do not
; invent a D10 call head merely to force this fixture into the pure .bits reader.
;
; Each form is a self-verdict: EQ compares world?'s actual D1 result to the
; expected D1 bit. The host runner checks only that every form returns D1 YES.

(тотожне? (світ? (як-є (world () () ()))) так)
(тотожне? (світ? (як-є (world))) ні)
(тотожне? (світ? (як-є (world parent))) ні)
(тотожне? (світ? (як-є (world parent journal))) ні)
(тотожне? (світ? (як-є (world parent journal metadata extra))) ні)
(тотожне? (світ? (як-є (not-world parent journal metadata))) ні)
(тотожне? (світ? (як-є ())) ні)

; Existing observable world behavior stays a SENS-owned assertion too.
(тотожне? (внутрішня-рівність-версій (порожній-світ) (як-є (world () () ()))) так)
(тотожне? (внутрішня-рівність-версій (світ-батько (порожній-світ)) (як-є ())) так)
(тотожне? (внутрішня-рівність-версій (світ-журнал (порожній-світ)) (як-є ())) так)
(тотожне? (внутрішня-рівність-версій (світ-метадані (порожній-світ)) (як-є ())) так)
(тотожне? (world-module-missing? (порожній-світ) (як-є unknown)) так)
(тотожне? (внутрішня-рівність-версій
      (world-remove-first (як-є x) (як-є (a x b)))
      (як-є (a b))) так)

; SENS verifies the actual aligned-ancestor law, not a Rust/Python truth table.
(тотожне?
  (внутрішня-рівність-версій
    (вирівняний-спільний-предок-двох-світів (порожній-світ) (порожній-світ))
    (порожній-світ))
  так)

; Two distinct children share their immutable parent.
(тотожне?
  (внутрішня-рівність-версій
    (вирівняний-спільний-предок-двох-світів
      (світ-повідомити (порожній-світ) (як-є astronomy) (як-є (planet earth)))
      (світ-повідомити (порожній-світ) (як-є physics) (як-є (mass earth))))
    (порожній-світ))
  так)

; Divergent roots must return the named negative result.
(тотожне?
  (вирівняний-спільний-предок-двох-світів
    (створити-світ (як-є ()) (як-є (alpha)) (як-є ()))
    (створити-світ (як-є ()) (як-є (beta)) (як-є ())))
  (як-є World-no-common-ancestor))

; The recognition function returns exactly D1:YES or D1:NO.
(тотожне? (світи-не-мають-спільного-предка? (як-є World-no-common-ancestor)) так)
(тотожне? (світи-не-мають-спільного-предка? (порожній-світ)) ні)
(тотожне? (світи-не-мають-спільного-предка? (як-є unrelated-atom)) ні)

; NIL must not be dereferenced as an immutable world.
(тотожне?
  (вирівняний-спільний-предок-двох-світів (як-є ()) (порожній-світ))
  (як-є World-no-common-ancestor))

; Cross-depth LCA: a grandchild and its direct parent share the parent.
(тотожне?
  (внутрішня-рівність-версій
    (світ-спільний-предок
      (світ-повідомити
        (світ-повідомити (порожній-світ) (як-є astronomy) (як-є (planet earth)))
        (як-є biology)
        (як-є (living earth)))
      (світ-повідомити (порожній-світ) (як-є astronomy) (як-є (planet earth))))
    (світ-повідомити (порожній-світ) (як-є astronomy) (як-є (planet earth))))
  так)

; Symmetry: argument order cannot change the semantic common ancestor.
(тотожне?
  (внутрішня-рівність-версій
    (світ-спільний-предок
      (світ-повідомити (порожній-світ) (як-є astronomy) (як-є (planet earth)))
      (світ-повідомити
        (світ-повідомити (порожній-світ) (як-є astronomy) (як-є (planet earth)))
        (як-є biology)
        (як-є (living earth))))
    (світ-повідомити (порожній-світ) (як-є astronomy) (як-є (planet earth))))
  так)

; Distinct self-rooted worlds have no shared parent.
(тотожне?
  (світ-спільний-предок
    (створити-світ (як-є ()) (як-є (alpha)) (як-є ()))
    (створити-світ (як-є ()) (як-є (beta)) (як-є ())))
  (як-є World-no-common-ancestor))

; Empty non-world input must stop without invoking a parent selector.
(тотожне?
  (світ-спільний-предок (як-є ()) (порожній-світ))
  (як-є World-no-common-ancestor))

; Українські D8-проєкції перевіряються фізичним SENS-виконанням World.
; D8:11101101 текст-у-символ; D8:11110100 значення-у-текст.
; Ні бітова ширина, ні T5M не надають нової семантики цих викликів.
(тотожне? (внутрішній-символ? (як-є зірка)) так)
(тотожне? (внутрішній-символ? (як-є (зірка))) ні)
(тотожне? (внутрішній-символ? (як-є ())) ні)
(тотожне? (текст-у-символ (значення-у-текст (як-є зірка))) (як-є зірка))
(текст? (знання-вміст-адреса (як-є (зірка))))
(текст? (світ-вміст-адреса (порожній-світ)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити порожній-світ empty-world)
(визначити знання-вміст-адреса knowledge-content-address)
(визначити створити-світ make-world)
(визначити світ-спільний-предок world-common-ancestor)
(визначити вирівняний-спільний-предок-двох-світів world-common-ancestor-aligned)
(визначити світ-вміст-адреса world-content-address)
(визначити світ-журнал world-journal)
(визначити світ-метадані world-metadata)
(визначити світи-не-мають-спільного-предка? world-no-common-ancestor?)
(визначити світ-батько world-parent)
(визначити світ-повідомити world-tell)
(визначити світ? world?)
