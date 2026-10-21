; Каталог машинних команд x87 для обчислень із рухомою комою.
; Це фізичні факти набору команд, не закони математики SENS.

(isa-catalogue-1
  (extension X87)
  (source intel-sdm/intel-xed)
  (coverage seed)
  (instructions
    (instruction FLD
      (class floating-load)
      (feature X87)
      (privilege user))
    (instruction FSTP
      (class floating-store)
      (feature X87)
      (privilege user))
    (instruction FADD
      (class floating-arithmetic)
      (feature X87)
      (privilege user))))
