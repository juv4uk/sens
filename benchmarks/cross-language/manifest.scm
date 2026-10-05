;; Cross-language benchmark tools for Contract 11.5 external controls.
;; Extends the root manifest under the same channels.scm pin.
(specifications->manifest
 (quote ("python"
         "lua"
         "sbcl"
         "valgrind"
         "util-linux"
         "coreutils")))
