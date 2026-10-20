; #211 — replaceability witness.
; CI runs this after physically moving lib/machine out of the checkout.
; Ukrainian projection only: no SID8 binary call heads, no #b machine width tags.
; Exact decimal arithmetic and D3 surfaces.

(визначити machine-replaceability-add
  (додати 2 3))

(визначити machine-replaceability-eq-cond
  (за-умовою
    ((тотожне? 2 2)
     111)))

(визначити machine-replaceability-car-cons
  (перше (сполучити 2 3)))

; Every assertion is a strict one-clause COND. If any assertion is NO, COND
; yields (), so the shell's exact pass-envelope check fails closed.
(визначити machine-replaceability-verdict
  (за-умовою
    ((тотожне? machine-replaceability-add 5)
     (за-умовою
       ((тотожне? machine-replaceability-eq-cond 111)
        (за-умовою
          ((тотожне? machine-replaceability-car-cons 2)
           (як-є (machine-replaceability-witness (status pass))))))))))

machine-replaceability-verdict
