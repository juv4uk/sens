# Транзакційний захист T5 mirror

**Проблема:** legacy `migrate-to-sens-codes.py --sens-mirror` записує позитивні `.sens` по одному ще до того, як побачить BLOCK інших вхідних `.lisp`. Його exit 0 можливий після часткової конвертації. Це не є готовим корпусом.

**Виправлення:** `scripts/guarded_sens_mirror.py` запускає наявний мігратор у приватному тимчасовому каталозі, звіряє кожне вхідне `.lisp` з однойменним фізичним T5 `.sens`, перевіряє повний manifest, source SHA, typed-word SHA, фізичний SHA та канонічність T5. Лише якщо успішні **всі файли**, публікує весь каталог однією Linux `renameat2(RENAME_NOREPLACE)` без заміни попереднього результату. При будь-якому блокуванні каталог не публікується. Джерела ніколи не переписуються.

```bash
python3 scripts/guarded_sens_mirror.py --root /path/to/approved-lisp-corpus --out /tmp/new-unique-wave
python3 -m unittest discover -s tests -p 'test_guarded_sens_mirror.py' -v
```

Семантична двійкова SENS — лише 0/1; T5 використовує трит 2 між словами, п'ять тритів на фізичний байт, без службового EOS 22. Файл — `name.sens`, не extensionless. Результат містить `_physical-migration-report.json` з `semantics=NOT_VERIFIED`.

**Безпекова межа:** цей wrapper перевіряє **лише фізичний транспорт і транзакцію**. Він НЕ замінює незалежний D2 parser/oracle parity, перевірку епохи W8 чи схвалення конкретних історичних джерел. Для публікації до `main` потрібен канонічний admission gate. Не виконувати автоматичне видалення файлів, не чіпати `master`, не оголошувати semantic equivalence за byte roundtrip.

Координація: [#4449](https://github.com/juv4uk/sens/issues/4449).