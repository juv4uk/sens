; #845 — executable check of the coordinate-view envelope.
; The source axes remain authoritative; this fixture only emits the named
; observer envelope after loading the matrix as data.
(визначити semantic-coordinate-matrix-845
  (функція ()
    (як-є
      (semantic-coordinate-matrix-845
       (status pass)
       (axes independent)
       (authority canonical-sid-registry)
       (rows 5)))))

(semantic-coordinate-matrix-845)
