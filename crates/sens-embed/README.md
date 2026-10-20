# Вбудовування SENS через C ABI

`sens-embed` — вузька межа C ABI для host-програм, яким потрібна станова
сесія SENS. Розбір, початкове завантаження, обчислення, друк, помилки,
визначення, макроси та замикання делегуються crate `sens`; другого
обчислювача чи альтернативної семантики тут немає.

Поточна версія ABI — `6`. Це несумісне перейменування публічного інтерфейсу:
старі символи `my_lisp_embed_*`, типи `MyLispEmbed*` та заголовок
`my_lisp_embed.h` вилучено. Host має перевірити версію перед використанням
експортів.

```c
uint32_t sens_embed_abi_version(void);
SensEmbedSession *sens_embed_session_new(void);
char *sens_embed_eval(SensEmbedSession *, const char *utf8_source);
void sens_embed_free_string(char *);
void sens_embed_session_free(SensEmbedSession *);
```

`sens_embed_eval` обчислює повний UTF-8 фрагмент у тій самій сесії під час
кожного виклику. Викликач володіє ненульовим повернутим рядком і звільняє його
через `sens_embed_free_string`. Нульова сесія дає нульовий вказівник. Помилки
розбору й мови повертаються як читабельний рядок `error:`, а не перетинають ABI
як panic.

## Механізми host-середовища

ABI v2 додав вузький місток для host-факту або дії без аргументів. Host
прив'язує українську поверхню до C callback; callback може повернути лише
теги `SENS_EMBED_NIL` або `SENS_EMBED_TRUE`:

```c
int32_t sens_embed_register_nullary(
    SensEmbedSession *session,
    const char *utf8_surface,
    SensEmbedNullaryFn callback,
    void *context);
```

Callback запускається лише тоді, коли програма SENS викликала прив'язану
функцію. Він не розбирає джерело, не вибирає сценарій і не запускає окремий
обчислювач.

ABI v3 додав `sens_embed_bind_host_handle`: host може прив'язати непрозоре
значення на кшталт `гравець`, не відкриваючи числовий токен у джерелі чи REPL.

ABI v4 додав вузький місток для дії з одним непрозорим аргументом фіксованого
`kind`:

```c
int32_t sens_embed_register_unary(
    SensEmbedSession *session,
    const char *utf8_surface,
    const char *utf8_kind,
    SensEmbedUnaryFn callback,
    void *context);
```

Прив'язана функція приймає рівно один аргумент — handle, створений через
`sens_embed_bind_host_handle`, чий `kind` точно збігається з `utf8_kind`.
Інший тип handle, звичайне значення чи неправильна кількість аргументів
повертає звичайну перехоплювану помилку `error:`. Callback отримує токен
`u64` напряму. Результат обмежений тегами `SENS_EMBED_NIL` або
`SENS_EMBED_TRUE` через `out_result`.

ABI v5 додав канал бінарного результату: `sens_embed_eval_binary` повертає
щільно упакований потік бітів і його точну довжину. Версія ABI v6 перейменувала
публічний інтерфейс; представлення даних, сигнатури за типами аргументів,
володіння пам'яттю та поведінка залишилися незмінними.
