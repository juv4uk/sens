;; #1413 вісь A: інструменти самого бенчмарку (харнес), поверх
;; кореневого manifest.scm репозиторію. Закріплюється тим самим
;; channels.scm:
;;
;;   guix time-machine -C channels.scm -- shell -m manifest.scm \
;;       -m benchmarks/sens-surface/manifest.scm -- \
;;       python3 benchmarks/sens-surface/run.py --sens target-guix/release/sens
(specifications->manifest
 (quote ("python"
         "util-linux"     ; taskset
         "coreutils")))   ; sha256sum
