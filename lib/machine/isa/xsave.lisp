; Каталог машинних команд збереження та відновлення стану процесора.
; Тут описані лише фізичні властивості ISA.
; Доступність складових стану перевіряють операційна система
; та виконавець; каталог не встановлює мовних законів СЕНС.

(isa-catalogue/1
  (extension XSAVE)
  (source intel-sdm/intel-xed)
  (runtime-gate cpuid-xsave)
  (coverage seed)
  (instructions
    (instruction XSAVE
      (class processor-state-save)
      (feature XSAVE)
      (privilege user))
    (instruction XRSTOR
      (class processor-state-restore)
      (feature XSAVE)
      (privilege user))))
