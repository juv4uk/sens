;; Зовнішні execution islands. Вони є механізмами виконання, не семантичною владою.
;; CLIPS додається runner-ом через локальний packaging/guix/clips.scm.
;; Використання: ./guix/run islands -- <команда>
(specifications->manifest
 (quote ("swi-prolog"
         "sbcl")))
