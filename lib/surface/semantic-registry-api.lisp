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

(00001001 semantic-registry-source-path
  "lib/surface/semantic-registry.lisp")

(00001001 semantic-registry-read-source
  (00001000 (source)
    (00000101
      (01001011 source))))

(00001001 semantic-registry-read
  (00001000 ()
    (semantic-registry-read-source
      (10100110 semantic-registry-source-path))))

(00001001 semantic-registry-rows
  (00001000 (registry)
    registry))

(00001001 semantic-registry-namespaces
  (00001000 ()
    (00000001 (en ук укр sa sym))))

(00001001 semantic-registry-row-namespaces
  (00001000 (surfaces)
    (00000111
      ((00000010 surfaces) ()
       (00000001 ()))
      ((00000010 surfaces) (0)
       (00000100
         (00000101 (00000101 surfaces))
         (semantic-registry-row-namespaces
           (00000110 surfaces)))))))

(00001001 semantic-registry-row-namespaces-from-row
  (00001000 (row)
    (semantic-registry-row-namespaces
      (semantic-registry-row-surfaces row))))

(00001001 semantic-registry-row-id
  (00001000 (row)
    (00000101 row)))

(00001001 semantic-registry-row-surfaces
  (00001000 (row)
    (00000110 row)))

(00001001 semantic-registry-find-surface
  (00001000 (namespace surfaces)
    (00000111
      ((00000010 surfaces) ()
       (00000001 ()))
      ((00000010 surfaces) (0)
       (00000111
         ((00000011 namespace (00000101 (00000101 surfaces))) (1)
          (00000101 surfaces))
         ((00000011 namespace (00000101 (00000101 surfaces))) (0)
          (semantic-registry-find-surface namespace (00000110 surfaces))))))))

(00001001 semantic-registry-surface-name
  (00001000 (namespace row)
    (10011100 ((entry
            (semantic-registry-find-surface
              namespace
              (semantic-registry-row-surfaces row))))
      (00000111
        ((00000010 entry) ()
         (00000001 ()))
        ((00000010 entry) (0)
         (00101111 entry))))))

(00001001 semantic-registry-find-row
  (00001000 (sens-ref rows)
    (00000111
      ((00000010 rows) ()
       (00000001 ()))
      ((00000010 rows) (0)
       (00000111
         ((00100010 sens-ref (semantic-registry-row-id (00000101 rows)))
          (00000101 rows))
         ((00100001 (00100010 sens-ref (semantic-registry-row-id (00000101 rows))))
          (semantic-registry-find-row sens-ref (00000110 rows))))))))

(00001001 semantic-registry-find-id-in-namespaces
  (00001000 (name row namespaces)
    (00000111
      ((00000010 namespaces) ()
       (00000001 ()))
      ((00000010 namespaces) (0)
       (10011100 ((candidate
               (semantic-registry-surface-name
                 (00000101 namespaces)
                 row)))
         (00000111
           ((00100010 name candidate)
            (semantic-registry-row-id row))
           ((00100001 (00100010 name candidate))
            (semantic-registry-find-id-in-namespaces
              name
              row
              (00000110 namespaces)))))))))

(00001001 semantic-registry-id-for-surface
  (00001000 (name rows)
    (00000111
      ((00000010 rows) ()
       (00000001 ()))
      ((00000010 rows) (0)
       (10011100 ((sens-ref
               (semantic-registry-find-id-in-namespaces
                 name
                 (00000101 rows)
                 (00000001 (en ук укр sa sym)))))
         (00000111
           ((00000010 sens-ref) ()
            (semantic-registry-id-for-surface name (00000110 rows)))
           ((00000010 sens-ref) (1)
            sens-ref)
           ((00000010 sens-ref) (0)
            (semantic-registry-id-for-surface name (00000110 rows)))))))))

(00001001 semantic-registry-round-trip
  (00001000 (sens-ref)
    (10011101 ((printed (01001100 sens-ref))
           (forms
             (01001011 printed)))
      (00000101 forms))))

; Query already-read registry data without re-entering host I/O.
(00001001 semantic-registry-row-in
  (00001000 (registry sens-ref)
    (semantic-registry-find-row
      sens-ref
      (semantic-registry-rows registry))))

(00001001 semantic-registry-id-in
  (00001000 (registry surface)
    (semantic-registry-id-for-surface
      surface
      (semantic-registry-rows registry))))

; Convenience wrappers for ordinary runtime use.
(00001001 semantic-registry-row
  (00001000 (sens-ref)
    (semantic-registry-row-in
      (semantic-registry-read)
      sens-ref)))

(00001001 semantic-registry-id
  (00001000 (surface)
    (semantic-registry-id-in
      (semantic-registry-read)
      surface)))
