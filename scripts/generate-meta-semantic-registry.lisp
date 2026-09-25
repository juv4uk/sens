; #76 — Lisp-owned meta semantic registry projection from the canonical semantic registry.
;
; Authority stays in lib/surface/semantic-registry.lisp.
; This script owns projection mechanics only: it reads the registry as
; ordinary my-lisp data and never re-parses source text with host regexes.
;
; Registry rows are:
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
      ((atom? surface) ())
      ((equal? (surface-word surface) (quote ())) ())
      ((equal? (surface-word surface) "'") ())
      (t t))))

(def collect-surfaces
  (lambda (sid surfaces rows)
    (cond
      ((atom? surfaces) rows)
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
      ((atom? entries) rows)
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
      " "
      (write-to-string (second row))
      ") ; "
      (write-to-string (third row))
      "\n")))

(def join-rows
  (lambda (rows)
    (reduce
      (lambda (acc row)
        (string-append acc (render-row row)))
      ""
      rows)))

(def render-projection
  (lambda (rows)
    (str+
      "; GENERATED FILE — DO NOT EDIT.\n"
      "; Source authority: lib/surface/semantic-registry.lisp\n"
      "; Generator: scripts/generate-meta-semantic-registry.lisp\n"
      "; Registry surfaces; empty and reader-only apostrophe surfaces omitted.\n\n"
      "(def my-semantic-surface-registry\n"
      "  (quote (\n"
      (join-rows (reverse rows))
      "  )))\n\n"
      "(def my-semantic-id-for-surface\n"
      "  (lambda (name)\n"
      "    (let ((entry (assoc name my-semantic-surface-registry)))\n"
      "      (cond\n"
      "        ((atom entry) (structural-kind empty-list) (quote ()))\n"
      "        ((atom entry) (structural-kind pair) (second entry))))))\n")))

(def registry-form
  (car (read-all (read-file "lib/surface/semantic-registry.lisp"))))

(def projection-rows
  (collect-entries
    registry-form
    (quote ())))

(def generated
  (render-projection projection-rows))

(def output-path "lib/generated/meta-semantic-registry.lisp")

(cond
  ((atom? *argv*)
   (structural-kind empty-list)
   (second
     (list
       (write-file output-path generated)
       (print "meta semantic registry projection written"))))
  ((atom? *argv*)
   (structural-kind atom)
   (second
     (list
       (write-file output-path generated)
       (print "meta semantic registry projection written"))))
  ((equal? (car *argv*) "--check")
   (structural-relation same)
   (let ((current (read-file output-path)))
     (cond
       ((equal? current generated)
        (structural-relation same)
        (print "meta semantic registry projection is current"))
       ((equal? current generated)
        (structural-relation distinct)
        (second
          (list
            (print "meta semantic registry projection is stale")
            (car (quote ()))))))))
  ((equal? (car *argv*) "--check")
   (structural-relation distinct)
   (second
     (list
       (write-file output-path generated)
       (print "meta semantic registry projection written")))))
