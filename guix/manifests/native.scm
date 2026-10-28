;; Нативний компіляційний і діагностичний шар поверх кореневого manifest.scm.
;; Містить інструменти збірки WSL-ядра; perf сам не створює апаратні RAPL-покази.
;; Використання: ./guix/run native -- <команда>
(specifications->manifest
 (quote ("gcc-toolchain"
         "binutils"
         "make"
         "flex"
         "bison"
         "bc"
         "perl"
         "openssl"
         "elfutils"
         "libelf"
         "dwarves"
         "cpio"
         "rsync"
         "qemu"
         "pkg-config"
         "llvm"
         "lld"
         "gdb"
         "strace"
         "nasm")))
