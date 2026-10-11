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

(0011 surface-word
  (0010 (surface)
    (100 (011 surface))))

(0011 surface-namespace
  (0010 (surface)
    (100 surface)))

(0011 surface-included?
  (0010 (surface)
    (110
      ((010 surface) () ())
      ((010 surface) (1) ())
      ((11110111 (surface-word surface) (001 ())) ())
      ((11110111 (surface-word surface) "'") ())
      (t t))))

(0011 collect-surfaces
  (0010 (sid surfaces rows)
    (110
      ((010 surfaces) () rows)
      ((010 surfaces) (1) rows)
      (t
       (001000 ((surface (100 surfaces)))
         (110
           ((surface-included? surface)
            (collect-surfaces
              sid
              (011 surfaces)
              (111
                (1110
                  (surface-word surface)
                  sid
                  (surface-namespace surface))
                rows)))
           (t
            (collect-surfaces sid (011 surfaces) rows))))))))

(0011 collect-entries
  (0010 (entries rows)
    (110
      ((010 entries) () rows)
      ((010 entries) (1) rows)
      (t
       (001000 ((entry (100 entries)))
         (collect-entries
           (011 entries)
           (collect-surfaces (100 entry) (011 entry) rows)))))))

(0011 str+
  (0010 args
    (101110
      (0010 (acc part)
        (110011110 acc part))
      ""
      args)))

(0011 render-row
  (0010 (row)
    (str+
      "    ("
      (11110100 (100 row))
      " "
      (11110100 (1001 row))
      ") ; "
      (11110100 (10011 row))
      "\n")))

(0011 join-rows
  (0010 (rows)
    (101110
      (0010 (acc row)
        (110011110 acc (render-row row)))
      ""
      rows)))

(0011 render-projection
  (0010 (rows)
    (str+
      "; GENERATED FILE — DO NOT EDIT.\n"
      "; Source authority: lib/surface/semantic-registry.lisp\n"
      "; Generator: scripts/generate-meta-semantic-registry.lisp\n"
      "; Registry surfaces; empty and reader-only apostrophe surfaces omitted.\n\n"
      "(00001001 my-semantic-surface-registry\n"
      "  (00000001 (\n"
      (join-rows (10100 rows))
      "  )))\n\n"
      "(00001001 my-semantic-id-for-surface\n"
      "  (00001000 (name)\n"
      "    (10011100 ((entry (00101101 name my-semantic-surface-registry)))\n"
      "      (00000111\n"
      "        ((00000010 entry) () (00000001 ()))\n"
      "        ((00000010 entry) (0) (00101111 entry))))))\n")))

(0011 registry-form
  (100 (110101001 (110110111 "lib/surface/semantic-registry.lisp"))))

(0011 projection-rows
  (collect-entries
    registry-form
    (001 ())))

(0011 generated
  (render-projection projection-rows))

(0011 output-path "lib/generated/meta-semantic-registry.lisp")

(110
  ((010 *argv*)
   ()
   (1001
     (1110
       (110111100 output-path generated)
       (11011011 "meta semantic registry projection written"))))
  ((010 *argv*)
   (1)
   (1001
     (1110
       (110111100 output-path generated)
       (11011011 "meta semantic registry projection written"))))
  ((11110111 (100 *argv*) "--check")
   (1)
   (001000 ((current (110110111 output-path)))
     (110
       ((11110111 current generated)
        (1)
        (11011011 "meta semantic registry projection is current"))
       ((11110111 current generated)
        (0)
        (1001
          (1110
            (11011011 "meta semantic registry projection is stale")
            (100 (001 ()))))))))
  ((11110111 (100 *argv*) "--check")
   (0)
   (1001
     (1110
       (110111100 output-path generated)
       (11011011 "meta semantic registry projection written")))))
