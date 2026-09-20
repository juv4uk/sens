(binary 8)

; Lisp-owned semantic-registry API.
;
; Authority is lib/surface/semantic-registry.lisp itself. This library does
; not recreate the registry in another representation: it reads the canonical
; Lisp table with the ordinary Lisp reader and queries that resulting value.
;
; The first element of the canonical table is the format descriptor:
;   (binary 8)
; All remaining elements are semantic rows:
;   (Binary identity (en ...) (uk ...) (ukr ...) (sa ...) (sym ...))
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

(def semantic-registry-format
  (lambda (registry)
    (car registry)))

(def semantic-registry-rows
  (lambda (registry)
    (cdr registry)))

(def semantic-registry-namespaces
  (lambda ()
    (quote (en uk ukr sa sym))))

(def semantic-registry-row-namespaces
  (lambda (surfaces)
    (cond
      ((atom surfaces) (structural-kind empty-list)
       (quote ()))
      ((atom surfaces) (structural-kind pair)
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
      ((atom surfaces) (structural-kind empty-list)
       (quote ()))
      ((atom surfaces) (structural-kind pair)
       (cond
         ((eq namespace (car (car surfaces))) (identity-relation same)
          (car surfaces))
         ((eq namespace (car (car surfaces))) (identity-relation distinct)
          (semantic-registry-find-surface namespace (cdr surfaces))))))))

(def semantic-registry-surface-name
  (lambda (namespace row)
    (let ((entry
            (semantic-registry-find-surface
              namespace
              (semantic-registry-row-surfaces row))))
      (cond
        ((atom entry) (structural-kind empty-list)
         (quote ()))
        ((atom entry) (structural-kind pair)
         (second entry))))))

(def semantic-registry-find-row
  (lambda (identity rows)
    (cond
      ((atom rows) (structural-kind empty-list)
       (quote ()))
      ((atom rows) (structural-kind pair)
       (cond
         ((equal? identity (semantic-registry-row-id (car rows)))
          (structural-relation same)
          (car rows))
         ((equal? identity (semantic-registry-row-id (car rows)))
          (structural-relation distinct)
          (semantic-registry-find-row identity (cdr rows))))))))

(def semantic-registry-find-id-in-namespaces
  (lambda (name row namespaces)
    (cond
      ((atom namespaces) (structural-kind empty-list)
       (quote ()))
      ((atom namespaces) (structural-kind pair)
       (let ((candidate
               (semantic-registry-surface-name
                 (car namespaces)
                 row)))
         (cond
           ((equal? name candidate) (structural-relation same)
            (semantic-registry-row-id row))
           ((equal? name candidate) (structural-relation distinct)
            (semantic-registry-find-id-in-namespaces
              name
              row
              (cdr namespaces)))))))))

(def semantic-registry-id-for-surface
  (lambda (name rows)
    (cond
      ((atom rows) (structural-kind empty-list)
       (quote ()))
      ((atom rows) (structural-kind pair)
       (let ((identity
               (semantic-registry-find-id-in-namespaces
                 name
                 (car rows)
                 (quote (en uk ukr sa sym)))))
         (cond
           ((atom identity) (structural-kind empty-list)
            (semantic-registry-id-for-surface name (cdr rows)))
           ((atom identity) (structural-kind atom)
            identity)
           ((atom identity) (structural-kind pair)
            (semantic-registry-id-for-surface name (cdr rows)))))))))

(def semantic-registry-round-trip
  (lambda (identity)
    (let* ((printed (write-to-string identity))
           (forms
             (read-all
               (string-append "(binary 8) " printed))))
      (second forms))))

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


