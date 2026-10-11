# Архів PR #2412 — generation accounting

**Статус: HISTORICAL-RESEARCH-ONLY.**

Повний diff workflow + benchmark runner збережений у `generation-accounting-review.patch` разом із manifest. PR head `17ddba20c91249ec3d56aa8c539159729ec37e49` базувався на main snapshot `42e3945c5e8f27902ade6fedf52f54786c56f914`, який значно старіший за поточний main.

Історичні числа з PR body: 30 активних D3+ рядків, 12 похідних selector-кандидатів, 18 UNKNOWN; інтервал плоского selector [0,15], root+law [0,5], верхня межа звужується на 10, але нижня не змінюється. Власний self-framed сертифікат займає більше, ніж плоскі координати, тому збереження даних саме по собі не доводить виграшу. Приховане per-row map “compression” було відхилено.

Це обліковий benchmark-доказ, а не швидкісний результат і не поточна оцінка покриття. Перед активацією runner має бути переприв'язаний до поточних inventory/blob SHA й відтворений на тому самому workload. Нової гілки не створено.
