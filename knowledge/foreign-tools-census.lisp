; Foreign-tool governance summary; the per-file machine-readable census is tools/foreign-census.tsv.
; This Lisp-owned record is policy data, not a claim that the foreign adapter is already self-hosted.
(00001001 *foreign-tools-census*
  (00000001
    ((schema . foreign-tools-census/1)
     (status . staged-migration)
     (authority . "knowledge/file-authority-policy.lisp")
     (per-file-census . "tools/foreign-census.tsv")
     (legacy-debt .
       ((foreign-python-existing . 741)
        (noncanonical-important-existing . 261)
        (migration-plan . "Мігрувати перевірювані intake та proof-закони до виконуваних SENS .lisp/.sens через незалежну oracle parity; не видаляти JSON, TSV, XED donor або Core4 FASL без замінного доказу.")))
     (new-foreign-tools .
       (((path . "tools/check_source_policy.py")
         (independence_status . foreign)
         (owner_issue . "#5398")
         (migration_plan . "Замінити повне сканування Git-дерева, census validation і named-fail verdict виконуваною фізичною SENS/T5-програмою; залишити Git дерево лише недовіреним зовнішнім входом; видаляти Python після hosted parity позитивних і негативних свідків."))))
     (new-python-without-entry . blocked)
     (new-python-outside-tools . blocked)
     (oracle-parity-before-host-retirement . required)
     (new-tool-does-not-own-semantics . 1))))