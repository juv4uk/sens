;; #1546: інструменти міжмовного benchmark harness.
;; Накладається поверх кореневого manifest.scm під тим самим channels.scm.
(specifications->manifest
 (quote ("python"
         "valgrind"
         "util-linux"
         "coreutils")))
