; Журнал фактичного покриття нативного виконання SENS.
;
; Це лише цитовані діагностичні дані: вони не визначають семантики,
; не створюють нативного маршруту й не підтверджують допуск самі собою.
; Маршрут вибирає справжній класифікатор SENS; незалежний свідок
; перевіряє результат і точно зберігає відмову та її передумову.
;
; Єдині виконувані голови файла — ратифіковані D4 «визначити»
; і D3 «як-є». Історичну виконавчу голову 001 фізично вилучено.
; Представницькі форми також записані сучасною українською проєкцією,
; але залишаються даними всередині одного цитованого журналу.
;
; Поля native-coverage, class, representative, status, reason,
; evidence, expected, effect, error, prerequisite є атомами
; чинного протоколу споживача, а не викликами.
; Шість випадків: один native, два fallback, три blocked.

(визначити журнал-нативного-покриття
  (як-є
    ((native-coverage
       (class car-cons-u64-literals)
       (representative (перше (сполучити 2 3)))
       (status native-supported)
       (reason bounded-car-cons-u64-lowering-admitted)
       (evidence native-first-parity-witness)
       (expected 2)
       (effect pure)
       (error not-applicable))

     (native-coverage
       (class general-application)
       (representative (додати 2 3))
       (status fallback-required)
       (reason no-native-plan-for-general-application)
       (evidence native-first-dispatch-witness))

     (native-coverage
       (class car-cons-outside-native-literal-domain)
       (representative (перше (сполучити "native-limits" 3)))
       (status fallback-required)
       (reason current-native-island-holds-all-exact-integers)
       (evidence native-first-dispatch-witness))

     (native-coverage
       (class dynamic-pair-result)
       (representative (сполучити 2 3))
       (status blocked-runtime-prerequisite)
       (reason native-pair-result-needs-managed-lifetime)
       (evidence native-first-dispatch-witness)
       (prerequisite native-pair-allocation-and-managed-lifetime))

     (native-coverage
       (class lambda-application)
       (representative ((функція (аргумент) (додати аргумент 1)) 41))
       (status blocked-runtime-prerequisite)
       (reason user-callable-native-path-needs-closure-abi)
       (evidence native-first-dispatch-witness)
       (prerequisite native-closure-and-call-abi))

     (native-coverage
       (class general-control-flow)
       (representative
         (за-умовою
           ((тотожне? (як-є ні) (як-є так)) 0)
           ((атом? (як-є ())) 1)))
       (status blocked-runtime-prerequisite)
       (reason source-control-native-path-needs-label-graph)
       (evidence native-first-dispatch-witness)
       (prerequisite native-label-layout-and-general-control-lowering)))))
