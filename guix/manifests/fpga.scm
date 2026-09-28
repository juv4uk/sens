;; Відтворюваний відкритий FPGA toolchain для локальних witness-перевірок.
;; Використання: ./guix/run fpga -- <команда>
(specifications->manifest
 (quote ("yosys"
         "iverilog"
         "verilator")))
