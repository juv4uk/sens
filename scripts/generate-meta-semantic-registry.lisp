; #76 — Lisp-owned meta semantic registry projection for sr/2.
;
; Authority stays in lib/surface/semantic-registry.lisp.
; This script owns projection mechanics only: it reads the registry as
; ordinary my-lisp data and never re-parses source text with host regexes.
;
; sr/2 rows are:
;   ("SID" (namespace surface) ...)
; Empty surfaces are omitted. The reader-only apostrophe is represented as
; a string and is omitted because the reader consumes it as quote syntax.
; Every other admitted symbol is projected in registry order.

(def surface-word
  (lambda (surface)
    (car (cdr surface))))

(def surface-namespace
  (lambda (surface)
    (car surface)))

(def surface-included?
  (lambda (surface)
    (cond
      ((atom surface) ())
      ((equal? (surface-word surface) (quote ())) ())
      ((equal? (surface-word surface) "'") ())
      (t t))))

(def collect-surfaces
  (lambda (sid surfaces rows)
    (cond
      ((atom surfaces) rows)
      (t
       (let ((surface (car surfaces)))
         (cond
           ((surface-included? surface)
            (collect-surfaces
              sid
              (cdr surfaces)
              (cons
                (list
                  (surface-word surface)
                  sid
                  (surface-namespace surface))
                rows)))
           (t
            (collect-surfaces sid (cdr surfaces) rows))))))))

(def collect-entries
  (lambda (entries rows)
    (cond
      ((atom entries) rows)
      (t
       (let ((entry (car entries)))
         (collect-entries
           (cdr entries)
           (collect-surfaces (car entry) (cdr entry) rows)))))))

(def str+
  (lambda args
    (reduce
      (lambda (acc part)
        (string-append acc part))
      ""
      args)))

(def render-row
  (lambda (row)
    (str+
      "    ("
      (write-to-string (car row))
      " \""
      (second row)
      "\") ; "
      (write-to-string (third row))
      "\n")))

(def join-rows
  (lambda (rows)
    (cond
      ((atom rows) "")
      ((atom (cdr rows))
       (render-row (car rows)))
      (t
       (str+
         (render-row (car rows))
         (join-rows (cdr rows)))))))

(def render-projection
  (lambda (rows)
    (str+
      "; GENERATED FILE — DO NOT EDIT.\n"
      "; Source authority: lib/surface/semantic-registry.lisp\n"
      "; Generator: scripts/generate-meta-semantic-registry.lisp\n"
      "; sr/2 surfaces; empty and reader-only apostrophe surfaces omitted.\n\n"
      "(def my-semantic-surface-registry\n"
      "  (quote (\n"
      (join-rows (reverse rows))
      "  )))\n\n"
      "(def my-semantic-id-for-surface\n"
      "  (lambda (name)\n"
      "    (let ((entry (assoc name my-semantic-surface-registry)))\n"
      "      (cond\n"
      "        ((atom entry) (quote ()))\n"
      "        (t (second entry))))))\n")))

(def registry-form
  (car (read-all (read-file "lib/surface/semantic-registry.lisp"))))

(cond
  ((eq (car registry-form) (quote sr/2))
   (identity-relation same)
   ())
  (t
   (print "meta semantic registry: expected sr/2")
   (car (quote ()))))

(def projection-rows
  (collect-entries (cdr registry-form) (quote ())))

(def generated
  (render-projection projection-rows))

(def output-path "lib/generated/meta-semantic-registry.lisp")

(cond
  ((atom *argv*)
   (write-file output-path generated)
   (print "meta semantic registry projection written"))
  ((equal? (car *argv*) "--check")
   (let ((current (read-file output-path)))
     (cond
       ((equal? current generated)
        (print "meta semantic registry projection is current"))
       (t
        (print "meta semantic registry projection is stale")
        (car (quote ())))))
  (t
   (write-file output-path generated)
   (print "meta semantic registry projection written"))))