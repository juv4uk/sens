; Каталог машинних команд ADX для багаторозрядного додавання з переносом.
; Це фізичні відомості ISA, а не математичні закони доменів SENS.

(isa-catalogue-1
  (extension ADX)
  (source intel-sdm/intel-xed)
  (runtime-gate cpuid-adx)
  (coverage seed)
  (instructions
    (instruction ADCX
      (class add-carry)
      (feature ADX)
      (privilege user))
    (instruction ADOX
      (class add-overflow)
      (feature ADX)
      (privilege user))))
