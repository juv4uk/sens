; #1047 — mechanism selection after Canon()/function-table identity resolution.
; Exact parent: #1046 function-table mechanism authority.
; This file never decides what a SID means. It only selects among executor
; routes already admitted by transitional #1046 mechanism metadata.
;
; Migrated: duplicate mutually-exclusive EQ arms removed; NOT(ATOM) guard
; replaced by exact two-field D3 COND + D1 ATOM for empty. Fallback uses
; (010 (001 ())) = D1:1. Width is identity; every bit of domain address valued.

(0011 mechanism-selector-registry
  (100 (110101001 (110110111 "lib/surface/semantic-registry.lisp"))))

(0011 mechanism-selector-metadata
  (100 (110101001 (110110111 "lib/function-table-mechanisms.lisp"))))

(0011 mechanism-selector-registry-rows
  mechanism-selector-registry)

(0011 mechanism-selector-find-section
  (0010 (name sections)
    (110
      ((010 sections) (001 ()))
      ((101 (100 (100 sections)) name) (100 sections))
      ((010 (001 ()))
       (mechanism-selector-find-section name (011 sections))))))

(0011 mechanism-selector-routes
  (011 (mechanism-selector-find-section
         (001 rows)
         mechanism-selector-metadata)))

(0011 mechanism-selector-registry-has-sid?
  (0010 (sid rows)
    (110
      ((010 rows) (001 no))
      ((101 sid (100 (100 rows))) (001 yes))
      ((010 (001 ()))
       (mechanism-selector-registry-has-sid? sid (011 rows))))))

(0011 mechanism-selector-find-route
  (0010 (sid executor rows)
    (110
      ((010 rows) (001 ()))
      ((010 (001 ()))
       ((0010 (row)
          (110
            ((101 sid (100 row))
             (110
               ((101 executor (1001 row)) row)
               ((010 (001 ()))
                (mechanism-selector-find-route sid executor (011 rows)))))
            ((010 (001 ()))
             (mechanism-selector-find-route sid executor (011 rows)))))
        (100 rows))))))

(0011 mechanism-select
  (0010 (sid executor)
    (110
      ((101
         (mechanism-selector-registry-has-sid?
           sid mechanism-selector-registry-rows)
         (001 no))
       (1110
         (001 mechanism-selection-failure)
         (001 sid-not-in-function-table)
         sid))
      ((010 (001 ()))
       ((0010 (route)
          (110
            ((010 route)
             (1110 (001 mechanism-unavailable) sid executor))
            ((010 (001 ()))
             (1110 (001 mechanism-selected)
               sid executor (10011 route)))))
        (mechanism-selector-find-route
          sid executor mechanism-selector-routes))))))
