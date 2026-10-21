; Каталог машинних команд Intel SGX; лише факти фізичної архітектури.
; Доступність залежить від CPUID, прошивки й керівного середовища ME,
; а також від підтримки операційною системою.

(isa-catalogue-1
  (extension SGX)
  (source intel-sdm/intel-xed)
  (runtime-gate cpuid-sgx+firmware+os-support)
  (coverage seed)
  (instructions
    (instruction ENCLU
      (class enclave-user-leaf)
      (feature SGX)
      (privilege user))
    (instruction ENCLS
      (class enclave-supervisor-leaf)
      (feature SGX)
      (privilege supervisor))))
