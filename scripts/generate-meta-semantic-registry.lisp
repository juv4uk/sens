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

(00001001 surface-word
  (00001000 (surface)
    (00000101 (00000110 surface))))

(00001001 surface-namespace
  (00001000 (surface)
    (00000101 surface)))

(00001001 surface-included?
  (00001000 (surface)
    (00000111
      ((00000010 surface) () ())
      ((00000010 surface) (1) ())
      ((00100010 (surface-word surface) (00000001 ())) ())
      ((00100010 (surface-word surface) "'") ())
      (t t))))

(00001001 collect-surfaces
  (00001000 (sid surfaces rows)
    (00000111
      ((00000010 surfaces) () rows)
      ((00000010 surfaces) (1) rows)
      (t
       (10011100 ((surface (00000101 surfaces)))
         (00000111
           ((surface-included? surface)
            (collect-surfaces
              sid
              (00000110 surfaces)
              (00000100
                (00100111
                  (surface-word surface)
                  sid
                  (surface-namespace surface))
                rows)))
           (t
            (collect-surfaces sid (00000110 surfaces) rows))))))))

(00001001 collect-entries
  (00001000 (entries rows)
    (00000111
      ((00000010 entries) () rows)
      ((00000010 entries) (1) rows)
      (t
       (10011100 ((entry (00000101 entries)))
         (collect-entries
           (00000110 entries)
           (collect-surfaces (00000101 entry) (00000110 entry) rows)))))))

(00001001 str+
  (00001000 args
    (00111001
      (00001000 (acc part)
        (00111010 acc part))
      ""
      args)))

(00001001 render-row
  (00001000 (row)
    (str+
      "    ("
      (01001100 (00000101 row))
      " "
      (01001100 (00101111 row))
      ") ; "
      (01001100 (00110000 row))
      "\n")))

(00001001 join-rows
  (00001000 (rows)
    (00111001
      (00001000 (acc row)
        (00111010 acc (render-row row)))
      ""
      rows)))

(00001001 render-projection
  (00001000 (rows)
    (str+
      "; GENERATED FILE — DO NOT EDIT.\n"
      "; Source authority: lib/surface/semantic-registry.lisp\n"
      "; Generator: scripts/generate-meta-semantic-registry.lisp\n"
      "; Registry surfaces; empty and reader-only apostrophe surfaces omitted.\n\n"
      "(def my-semantic-surface-registry\n"
      "  (quote (\n"
      (join-rows (00101010 rows))
      "  )))\n\n"
      "(def my-semantic-id-for-surface\n"
      "  (lambda (name)\n"
      "    (let ((entry (assoc name my-semantic-surface-registry)))\n"
      "      (cond\n"
      "        ((atom? entry) () (quote ()))\n"
      "        ((atom? entry) (0) (second entry))))))\n")))

(00001001 registry-form
  (00000101 (01001011 (10100110 "lib/surface/semantic-registry.lisp"))))

(00001001 projection-rows
  (collect-entries
    registry-form
    (00000001 ())))

(00001001 generated
  (render-projection projection-rows))

(00001001 output-path "lib/generated/meta-semantic-registry.lisp")

(00000111
  ((00000010 *argv*)
   ()
   (00101111
     (00100111
       (10100111 output-path generated)
       (01001000 "meta semantic registry projection written"))))
  ((00000010 *argv*)
   (1)
   (00101111
     (00100111
       (10100111 output-path generated)
       (01001000 "meta semantic registry projection written"))))
  ((00100010 (00000101 *argv*) "--check")
   (1)
   (10011100 ((current (10100110 output-path)))
     (00000111
       ((00100010 current generated)
        (1)
        (01001000 "meta semantic registry projection is current"))
       ((00100010 current generated)
        (0)
        (00101111
          (00100111
            (01001000 "meta semantic registry projection is stale")
            (00000101 (00000001 ()))))))))
  ((00100010 (00000101 *argv*) "--check")
   (0)
   (00101111
     (00100111
       (10100111 output-path generated)
       (01001000 "meta semantic registry projection written")))))
