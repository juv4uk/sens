; Lisp-owned semantic-registry API.
;
; Authority is lib/surface/semantic-registry.lisp itself. This library does
; not recreate the registry in another representation: it reads the canonical
; Lisp table with the ordinary Lisp reader and queries that resulting value.
;
; Every element of the canonical table is a semantic row:
;   (Binary identity (en ...) (ук ...) (укр ...) (sa ...) (sym ...))
;
; Runtime implementations may project the Binary identity to an internal byte,
; but the meaning and lookup rules below belong to Lisp.

(0011 semantic-registry-source-path
  "lib/surface/semantic-registry.lisp")

(0011 semantic-registry-read-source
  (0010 (source)
    (100
      (110101001 source))))

(0011 semantic-registry-read
  (0010 ()
    (semantic-registry-read-source
      (110110111 semantic-registry-source-path))))

(0011 semantic-registry-rows
  (0010 (registry)
    registry))

(0011 semantic-registry-namespaces
  (0010 ()
    (001 (en ук укр sa sym))))

(0011 semantic-registry-row-namespaces
  (0010 (surfaces)
    (110
      
      ((0100 (010 surfaces))
       (111
         (100 (100 surfaces))
         (semantic-registry-row-namespaces
           (011 surfaces)))))))

(0011 semantic-registry-row-namespaces-from-row
  (0010 (row)
    (semantic-registry-row-namespaces
      (semantic-registry-row-surfaces row))))

(0011 semantic-registry-row-id
  (0010 (row)
    (100 row)))

(0011 semantic-registry-row-surfaces
  (0010 (row)
    (011 row)))

(0011 semantic-registry-find-surface
  (0010 (namespace surfaces)
    (110
      
      ((0100 (010 surfaces))
       (110
         ((101 namespace (100 (100 surfaces))) 
          (100 surfaces))
         ((0100 (101 namespace (100 (100 surfaces))))
          (semantic-registry-find-surface namespace (011 surfaces))))))))

(0011 semantic-registry-surface-name
  (0010 (namespace row)
    (001000 ((entry
            (semantic-registry-find-surface
              namespace
              (semantic-registry-row-surfaces row))))
      (110
        
        ((0100 (010 entry))
         (1001 entry))))))

(0011 semantic-registry-find-row
  (0010 (sens-ref rows)
    (110
      
      ((0100 (010 rows))
       (110
         ((11110111 sens-ref (semantic-registry-row-id (100 rows)))
          
          (100 rows))
         ((0100 (11110111 sens-ref (semantic-registry-row-id (100 rows))))
          (semantic-registry-find-row sens-ref (011 rows))))))))

(0011 semantic-registry-find-id-in-namespaces
  (0010 (name row namespaces)
    (110
      
      ((0100 (010 namespaces))
       (001000 ((candidate
               (semantic-registry-surface-name
                 (100 namespaces)
                 row)))
         (110
           ((11110111 name candidate) 
            (semantic-registry-row-id row))
           ((0100 (11110111 name candidate))
            (semantic-registry-find-id-in-namespaces
              name
              row
              (011 namespaces)))))))))

(0011 semantic-registry-id-for-surface
  (0010 (name rows)
    (110
      
      ((0100 (010 rows))
       (001000 ((sens-ref
               (semantic-registry-find-id-in-namespaces
                 name
                 (100 rows)
                 (001 (en ук укр sa sym)))))
         (110
           ((0100 (010 sens-ref))
            (semantic-registry-id-for-surface name (011 rows)))
           ((010 sens-ref) 
            sens-ref)
           ((0100 (010 sens-ref))
            (semantic-registry-id-for-surface name (011 rows)))))))))

(0011 semantic-registry-round-trip
  (0010 (sens-ref)
    (001001 ((printed (11110100 sens-ref))
           (forms
             (110101001 printed)))
      (100 forms))))

; Query already-read registry data without re-entering host I/O.
(0011 semantic-registry-row-in
  (0010 (registry sens-ref)
    (semantic-registry-find-row
      sens-ref
      (semantic-registry-rows registry))))

(0011 semantic-registry-id-in
  (0010 (registry surface)
    (semantic-registry-id-for-surface
      surface
      (semantic-registry-rows registry))))

; Convenience wrappers for ordinary runtime use.
(0011 semantic-registry-row
  (0010 (sens-ref)
    (semantic-registry-row-in
      (semantic-registry-read)
      sens-ref)))

(0011 semantic-registry-id
  (0010 (surface)
    (semantic-registry-id-in
      (semantic-registry-read)
      surface)))
