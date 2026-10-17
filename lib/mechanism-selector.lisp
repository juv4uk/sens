; #1047 — mechanism selection after Canon()/function-table identity resolution.
; Exact parent: #1046 function-table mechanism authority.
; This file never decides what a SID means. It only selects among executor
; routes already admitted by transitional #1046 mechanism metadata.
;
; Migrated: duplicate mutually-exclusive EQ arms removed; NOT(ATOM) guard
; replaced by exact two-field D3 COND + D1 ATOM for empty. Fallback uses
; (010 (001 ())) = D1:1. Width is identity; every bit of domain address valued.

(0011 mechanism-selector-registry
  (перше (читати-всі (читати-файл "lib/surface/semantic-registry.lisp"))))

(0011 mechanism-selector-metadata
  (перше (читати-всі (читати-файл "lib/function-table-mechanisms.lisp"))))

(0011 mechanism-selector-registry-rows
  mechanism-selector-registry)

(0011 mechanism-selector-find-section
  (0010 (name sections)
    (за-умовою
      ((атом? sections) (як-є ()))
      ((тотожне? (перше (перше sections)) name) (перше sections))
      ((атом? (як-є ()))
       (mechanism-selector-find-section name (решта sections))))))

(0011 mechanism-selector-routes
  (решта (mechanism-selector-find-section
         (як-є rows)
         mechanism-selector-metadata)))

(0011 mechanism-selector-registry-has-sid?
  (0010 (sid rows)
    (за-умовою
      ((атом? rows) (як-є no))
      ((тотожне? sid (перше (перше rows))) (як-є yes))
      ((атом? (як-є ()))
       (mechanism-selector-registry-has-sid? sid (решта rows))))))

(0011 mechanism-selector-find-route
  (0010 (sid executor rows)
    (за-умовою
      ((атом? rows) (як-є ()))
      ((атом? (як-є ()))
       ((0010 (row)
          (за-умовою
            ((тотожне? sid (перше row))
             (за-умовою
               ((тотожне? executor (друге row)) row)
               ((атом? (як-є ()))
                (mechanism-selector-find-route sid executor (решта rows)))))
            ((атом? (як-є ()))
             (mechanism-selector-find-route sid executor (решта rows)))))
        (перше rows))))))

(0011 mechanism-select
  (0010 (sid executor)
    (за-умовою
      ((тотожне?
         (mechanism-selector-registry-has-sid?
           sid mechanism-selector-registry-rows)
         (як-є no))
       (список
         (як-є mechanism-selection-failure)
         (як-є sid-not-in-function-table)
         sid))
      ((атом? (як-є ()))
       ((0010 (route)
          (за-умовою
            ((атом? route)
             (список (як-є mechanism-unavailable) sid executor))
            ((атом? (як-є ()))
             (список (як-є mechanism-selected)
               sid executor (10011 route)))))
        (mechanism-selector-find-route
          sid executor mechanism-selector-routes))))))
