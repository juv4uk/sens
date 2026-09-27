;; Нативний компіляційний і діагностичний шар поверх кореневого manifest.scm.
;; Використання: ./guix/run native -- <команда>
(specifications->manifest
 (quote ("gcc-toolchain"
         "binutils"
         "llvm"
         "lld"
         "gdb"
         "strace"
         "nasm")))
