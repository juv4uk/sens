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

(визначити surface-word
  (функція (surface)
    (перше (решта surface))))

(визначити surface-namespace
  (функція (surface)
    (перше surface)))

(визначити surface-included?
  (функція (surface)
    (за-умовою
      ((атом? surface) ())
      
      ((однакові? (surface-word surface) (як-є ())) ())
      ((однакові? (surface-word surface) "'") ())
      ((атом? (як-є ())) t))))

(визначити collect-surfaces
  (функція (sid surfaces rows)
    (за-умовою
      ((атом? surfaces) rows)
      
      ((атом? (як-є ()))
       (001000 ((surface (100 surfaces)))
         (за-умовою
           ((surface-included? surface)
            (collect-surfaces
              sid
              (решта surfaces)
              (сполучити
                (список
                  (surface-word surface)
                  sid
                  (surface-namespace surface))
                rows)))
           ((атом? (як-є ()))
            (collect-surfaces sid (решта surfaces) rows))))))))

(визначити collect-entries
  (функція (entries rows)
    (за-умовою
      ((атом? entries) rows)
      
      ((атом? (як-є ()))
       (001000 ((entry (100 entries)))
         (collect-entries
           (решта entries)
           (collect-surfaces (перше entry) (решта entry) rows)))))))

(визначити str+
  (функція args
    (101110
      (функція (acc part)
        (110011110 acc part))
      ""
      args)))

(визначити render-row
  (функція (row)
    (str+
      "    ("
      (значення-у-текст (перше row))
      " "
      (значення-у-текст (друге row))
      ") ; "
      (значення-у-текст (третє row))
      "\n")))

(визначити join-rows
  (функція (rows)
    (101110
      (функція (acc row)
        (110011110 acc (render-row row)))
      ""
      rows)))

(визначити render-projection
  (функція (rows)
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

(визначити registry-form
  (100 (110101001 (110110111 "lib/surface/semantic-registry.lisp"))))

(визначити projection-rows
  (collect-entries
    registry-form
    (як-є ())))

(визначити generated
  (render-projection projection-rows))

(визначити output-path "lib/generated/meta-semantic-registry.lisp")

(за-умовою
  ((атом? *argv*) (друге
     (список
       (110111100 output-path generated)
       (11011011 "meta semantic registry projection written"))))
  
  ((тотожне? (перше *argv*) "--check")
   (001000 ((current (110110111 output-path)))
     (за-умовою
       ((тотожне? current generated)
        (11011011 "meta semantic registry projection is current"))
       ((атом? (як-є ()))
        (друге
          (список
            (11011011 "meta semantic registry projection is stale")
            (перше (як-є ()))))))))
  ((атом? (як-є ()))
   (друге
     (список
       (110111100 output-path generated)
       (11011011 "meta semantic registry projection written")))))
