# Nyāya · Д11 НАС-форми: повний D3-хребет до збігу · 2026-10-25

## Поточний технічний борг
- Відправний HEAD: `6438fda02709fc7ab29e9e06868b0eccca781567`.
- D1–D10 мають ратифіковані доменні таблиці, але кожна ратифікована
  ідентичність ще не має доведеного фізичного виконання.
- D11 НАС-* — бібліотечна композиція над D3/D4/D5, не новий opcode.
- Виявлений дефект: `містить-канонічну-голову?` перевіряв лише
  зовнішню правильність D3 списку. Ранній збіг DEFINE міг дати
  D1:так до перевірки неправильної вкладеної пари (так . ні).

## Виправлення мовою SENS
- `lib/d11-form-presence.lisp`: нові взаємно рекурсивні SENS валідатори
  `підтвердити-правильне-дерево-форм` і
  `підтвердити-вкладені-списки-форм`.
- Цитовані дані QUOTE — інертні: неправильний хвіст там допускається
  як ДАНІ, але за межами цитати він дає справжню D3 CAR Type.
- Публічний `містить-канонічну-голову?` підтверджує весь
  нецитований D3-хребет рівно один раз, а `...-ядро?`
  обходить уже перевірені форми без повторного повного preflight.
- `tests/semantic/d11-form-presence-law.lisp` перевіряє дві ситуації з цитатою й вкладеним
  неправильним хвостом на реальному D1/SENS вердикті.
- `tests/fixtures/d11-form-presence-deep-improper-negative.lisp` демонструє, що ранній DEFINE збіг не приховує
  помилку структури.
- `scripts/prove-lisp-semantic-t5m.sh` і `scripts/execute_changed_lisp_t5m.sh` перевіряють direct,
  paired, standalone через реальний SENS → Zig/T5M → SENS,
  без заміни Type на UnknownSymbol.

## Доказова дисципліна
Статична збалансованість джерел перевірена. Нативний SENS/Zig
у цьому агентському середовищі недоступний, отже PASS на SHA
поки не підтверджено. Shell є лише тестовим механізмом.
Залишаються збої D6 MIN/MAX/LENGTH та фізична трійка D11.
Реліз l0.42.0 — NO-GO.

## Наступний swarm-агент
1. Запустити `cargo test --locked -p sens --test d11_legacy_form_presence`
   та нативний `scripts/prove-lisp-semantic-t5m.sh` на SHA коміту.
2. Зібрати точний stdout/stderr, sha256 і `physical_form_index`
   для позитиву, мутанта й негативу.
3. Перевірити, чи зміни D11 `.lisp` потребують нормативного
   перевидання `.sens` та бітового перегляду.
4. Довести, чому D6 MIN/MAX є у моноліті core4.lisp, але відсутні
   в усіх чинних `core4-parts`; звірити фактичний binding.
5. Продовжити D12+ та F6 physical producer/consumer.
   Жодного GO, поки owner не підтвердить реліз.

**Deutsch:** Vollständige D3-Struktur vor dem ersten HAS-Treffer
prüfen; QUOTE-Daten bleiben inert. Native Tests noch offen.
**English:** Validate all nonquoted nested D3 list structure before
an early HAS match, without rewalking validated trees.
