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

(def semantic-registry-source-path
  "lib/surface/semantic-registry.lisp")

(def semantic-registry-read-source
  (lambda (source)
    (car
      (read-all source))))

(def semantic-registry-read
  (lambda ()
    (semantic-registry-read-source
      (read-file semantic-registry-source-path))))

(def semantic-registry-rows
  (lambda (registry)
    registry))

(def semantic-registry-namespaces
  (lambda ()
    (quote (en ук укр sa sym))))

(def semantic-registry-row-namespaces
  (lambda (surfaces)
    (cond
      ((atom? surfaces) ()
       (quote ()))
      ((atom? surfaces) (0)
       (cons
         (car (car surfaces))
         (semantic-registry-row-namespaces
           (cdr surfaces)))))))

(def semantic-registry-row-namespaces-from-row
  (lambda (row)
    (semantic-registry-row-namespaces
      (semantic-registry-row-surfaces row))))

(def semantic-registry-row-id
  (lambda (row)
    (car row)))

(def semantic-registry-row-surfaces
  (lambda (row)
    (cdr row)))

(def semantic-registry-find-surface
  (lambda (namespace surfaces)
    (cond
      ((atom? surfaces) ()
       (quote ()))
      ((atom? surfaces) (0)
       (cond
         ((eq? namespace (car (car surfaces))) (1)
          (car surfaces))
         ((eq? namespace (car (car surfaces))) (0)
          (semantic-registry-find-surface namespace (cdr surfaces))))))))

(def semantic-registry-surface-name
  (lambda (namespace row)
    (let ((entry
            (semantic-registry-find-surface
              namespace
              (semantic-registry-row-surfaces row))))
      (cond
        ((atom? entry) ()
         (quote ()))
        ((atom? entry) (0)
         (second entry))))))

(def semantic-registry-find-row
  (lambda (identity rows)
    (cond
      ((atom? rows) ()
       (quote ()))
      ((atom? rows) (0)
       (cond
         ((equal? identity (semantic-registry-row-id (car rows)))
          (1)
          (car rows))
         ((equal? identity (semantic-registry-row-id (car rows)))
          (0)
          (semantic-registry-find-row identity (cdr rows))))))))

(def semantic-registry-find-id-in-namespaces
  (lambda (name row namespaces)
    (cond
      ((atom? namespaces) ()
       (quote ()))
      ((atom? namespaces) (0)
       (let ((candidate
               (semantic-registry-surface-name
                 (car namespaces)
                 row)))
         (cond
           ((equal? name candidate) (1)
            (semantic-registry-row-id row))
           ((equal? name candidate) (0)
            (semantic-registry-find-id-in-namespaces
              name
              row
              (cdr namespaces)))))))))

(def semantic-registry-id-for-surface
  (lambda (name rows)
    (cond
      ((atom? rows) ()
       (quote ()))
      ((atom? rows) (0)
       (let ((identity
               (semantic-registry-find-id-in-namespaces
                 name
                 (car rows)
                 (quote (en ук укр sa sym)))))
         (cond
           ((atom? identity) ()
            (semantic-registry-id-for-surface name (cdr rows)))
           ((atom? identity) (1)
            identity)
           ((atom? identity) (0)
            (semantic-registry-id-for-surface name (cdr rows)))))))))

(def semantic-registry-round-trip
  (lambda (identity)
    (let* ((printed (write-to-string identity))
           (forms
             (read-all printed)))
      (car forms))))

; Query already-read registry data without re-entering host I/O.
(def semantic-registry-row-in
  (lambda (registry identity)
    (semantic-registry-find-row
      identity
      (semantic-registry-rows registry))))

(def semantic-registry-id-in
  (lambda (registry surface)
    (semantic-registry-id-for-surface
      surface
      (semantic-registry-rows registry))))

; Convenience wrappers for ordinary runtime use.
(def semantic-registry-row
  (lambda (identity)
    (semantic-registry-row-in
      (semantic-registry-read)
      identity)))

(def semantic-registry-id
  (lambda (surface)
    (semantic-registry-id-in
      (semantic-registry-read)
      surface)))
