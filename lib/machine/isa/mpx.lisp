; Каталог машинних команд Intel MPX (розширення захисту пам'яті).
; Доступність залежить від платформи та ОС, навіть якщо процесор
; повідомляє про підтримку MPX.

(isa-catalogue-1
  (extension MPX)
  (source intel-sdm/intel-xed)
  (runtime-gate cpuid-mpx+os-support)
  (coverage seed)
  (instructions
    (instruction BNDCL
      (class bounds-check-lower)
      (feature MPX)
      (privilege user))
    (instruction BNDCU
      (class bounds-check-upper)
      (feature MPX)
      (privilege user))
    (instruction BNDMK
      (class bounds-create)
      (feature MPX)
      (privilege user))
    (instruction BNDMOV
      (class bounds-move)
      (feature MPX)
      (privilege user))))
