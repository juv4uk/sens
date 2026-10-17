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

(визначити semantic-registry-source-path
  "lib/surface/semantic-registry.lisp")

(визначити semantic-registry-read-source
  (функція (source)
    (100
      (110101001 source))))

(визначити semantic-registry-read
  (функція ()
    (semantic-registry-read-source
      (110110111 semantic-registry-source-path))))

(визначити semantic-registry-rows
  (функція (registry)
    registry))

(визначити semantic-registry-namespaces
  (функція ()
    (як-є (en ук укр sa sym))))

(визначити semantic-registry-row-namespaces
  (функція (surfaces)
    (110
      
      ((0100 (010 surfaces))
       (111
         (перше (перше surfaces))
         (semantic-registry-row-namespaces
           (решта surfaces)))))))

(визначити semantic-registry-row-namespaces-from-row
  (функція (row)
    (semantic-registry-row-namespaces
      (semantic-registry-row-surfaces row))))

(визначити semantic-registry-row-id
  (функція (row)
    (перше row)))

(визначити semantic-registry-row-surfaces
  (функція (row)
    (решта row)))

(визначити semantic-registry-find-surface
  (функція (namespace surfaces)
    (110
      
      ((0100 (010 surfaces))
       (110
         ((тотожне? namespace (перше (перше surfaces))) 
          (перше surfaces))
         ((0100 (101 namespace (100 (100 surfaces))))
          (semantic-registry-find-surface namespace (решта surfaces))))))))

(визначити semantic-registry-surface-name
  (функція (namespace row)
    (10011100 ((entry
            (semantic-registry-find-surface
              namespace
              (semantic-registry-row-surfaces row))))
      (110
        
        ((0100 (010 entry))
         (1001 entry))))))

(визначити semantic-registry-find-row
  (функція (sens-ref rows)
    (110
      
      ((0100 (010 rows))
       (110
         ((11110111 sens-ref (semantic-registry-row-id (100 rows)))
          
          (перше rows))
         (#d1:1
          (semantic-registry-find-row sens-ref (решта rows))))))))

(визначити semantic-registry-find-id-in-namespaces
  (функція (name row namespaces)
    (110
      
      ((0100 (010 namespaces))
       (10011100 ((candidate
               (semantic-registry-surface-name
                 (перше namespaces)
                 row)))
         (110
           ((11110111 name candidate) 
            (semantic-registry-row-id row))
           ((0100 (11110111 name candidate))
            (semantic-registry-find-id-in-namespaces
              name
              row
              (решта namespaces)))))))))

(визначити semantic-registry-id-for-surface
  (функція (name rows)
    (110
      
      ((0100 (010 rows))
       (10011100 ((sens-ref
               (semantic-registry-find-id-in-namespaces
                 name
                 (перше rows)
                 (як-є (en ук укр sa sym)))))
         (110
           ((0100 (010 sens-ref))
            (semantic-registry-id-for-surface name (решта rows)))
           ((атом? sens-ref) 
            sens-ref)
           ((0100 (010 sens-ref))
            (semantic-registry-id-for-surface name (решта rows)))))))))

(визначити semantic-registry-round-trip
  (функція (sens-ref)
    (001001 ((printed (write-to-string sens-ref))
           (forms
             (110101001 printed)))
      (перше forms))))

; Query already-read registry data without re-entering host I/O.
(визначити semantic-registry-row-in
  (функція (registry sens-ref)
    (semantic-registry-find-row
      sens-ref
      (semantic-registry-rows registry))))

(визначити semantic-registry-id-in
  (функція (registry surface)
    (semantic-registry-id-for-surface
      surface
      (semantic-registry-rows registry))))

; Convenience wrappers for ordinary runtime use.
(визначити semantic-registry-row
  (функція (sens-ref)
    (semantic-registry-row-in
      (semantic-registry-read)
      sens-ref)))

(визначити semantic-registry-id
  (функція (surface)
    (semantic-registry-id-in
      (semantic-registry-read)
      surface)))
