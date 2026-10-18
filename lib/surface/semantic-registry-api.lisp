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
    (перше
      (читати-всі source))))

(визначити semantic-registry-read
  (функція ()
    (semantic-registry-read-source
      (читати-файл semantic-registry-source-path))))

(визначити semantic-registry-rows
  (функція (registry)
    registry))

(визначити semantic-registry-namespaces
  (функція ()
    (як-є (en ук укр sa sym))))

(визначити semantic-registry-row-namespaces
  (функція (surfaces)
    (за-умовою
      
      ((хибне? (атом? surfaces))
       (сполучити
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
    (за-умовою
      
      ((хибне? (атом? surfaces))
       (за-умовою
         ((тотожне? namespace (перше (перше surfaces))) 
          (перше surfaces))
         ((хибне? (тотожне? namespace (перше (перше surfaces))))
          (semantic-registry-find-surface namespace (решта surfaces))))))))

(визначити semantic-registry-surface-name
  (функція (namespace row)
    (нехай ((entry
            (semantic-registry-find-surface
              namespace
              (semantic-registry-row-surfaces row))))
      (за-умовою
        
        ((хибне? (атом? entry))
         (друге entry))))))

(визначити semantic-registry-find-row
  (функція (sens-ref rows)
    (за-умовою
      
      ((хибне? (атом? rows))
       (за-умовою
         ((однакові? sens-ref (semantic-registry-row-id (перше rows)))
          
          (перше rows))
         (так
          (semantic-registry-find-row sens-ref (решта rows))))))))

(визначити semantic-registry-find-id-in-namespaces
  (функція (name row namespaces)
    (за-умовою
      
      ((хибне? (атом? namespaces))
       (нехай ((candidate
               (semantic-registry-surface-name
                 (перше namespaces)
                 row)))
         (за-умовою
           ((однакові? name candidate) 
            (semantic-registry-row-id row))
           ((хибне? (однакові? name candidate))
            (semantic-registry-find-id-in-namespaces
              name
              row
              (решта namespaces)))))))))

(визначити semantic-registry-id-for-surface
  (функція (name rows)
    (за-умовою
      
      ((хибне? (атом? rows))
       (нехай ((sens-ref
               (semantic-registry-find-id-in-namespaces
                 name
                 (перше rows)
                 (як-є (en ук укр sa sym)))))
         (за-умовою
           ((хибне? (атом? sens-ref))
            (semantic-registry-id-for-surface name (решта rows)))
           ((атом? sens-ref) 
            sens-ref)
           ((хибне? (атом? sens-ref))
            (semantic-registry-id-for-surface name (решта rows)))))))))

(визначити semantic-registry-round-trip
  (функція (sens-ref)
    (нехай-послідовно ((printed (write-to-string sens-ref))
           (forms
             (читати-всі printed)))
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
