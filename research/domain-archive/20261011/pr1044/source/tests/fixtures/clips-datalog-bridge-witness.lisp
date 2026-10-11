; Executable witness for #718 bounded CLIPS / Datalog / Lisp bridge projections.

(def clips-datalog-bridge-witness
  (lambda ()
    (list
      (clips-working-memory-to-datalog-facts
        (quote
          (clips-working-memory-observation
            (source-ref clips:17)
            (facts ((person alice) (person bob)))
            (agenda-fired 2))))
      (clips-working-memory-to-datalog-facts
        (quote
          (clips-working-memory-observation
            (source-ref clips:18)
            (facts-before 1)
            (facts-after 2)
            (agenda-fired 1))))
      (clips-working-memory-to-datalog-facts
        (quote
          (clips-working-memory-observation
            (source-ref clips:19)
            (facts atom-not-a-list))))
      (datalog-relation-to-clips-facts
        (quote
          (datalog-relation-observation
            (source-ref datalog:21)
            (relation person)
            (tuples ((alice) (bob)))
            (derivation-generation 3))))
      (datalog-relation-to-clips-facts
        (quote
          (datalog-relation-observation
            (source-ref datalog:22)
            (relation person)
            (relation-count 2))))
      (lisp-data-to-clips-fact
        (quote
          (lisp-fact-candidate
            (relation sensor)
            (arguments (temperature 21)))))
      (lisp-data-to-clips-fact
        (quote
          (lisp-fact-candidate
            (relation sensor)))))))
