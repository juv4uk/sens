# Архів історичного PR #623 — генератор post-core peer cache

**Статус: ARCHIVE-ONLY / НЕ АКТИВУВАТИ БЕЗ ПЕРЕПЕРЕВІРКИ НА ПОТОЧНОМУ SENS.**

Цей архів зберігає оригінальний diff та точний binary blob FASL із гілки work/chatgpt-606-generated-postcore-cache, head 1894dcf0c599e35f14aa594453aacc64cfbaa949. Гілку не зливали wholesale: її lib/core.lisp — 40,812 байтів і має старішу структуру, тоді як поточний main lib/core.lisp — 51,354 байти. Це не сумісний кандидат на заміну файла або FASL.

Перевірена межа в поточному main:
- lib/time.lisp прямо каже, що повторні my-postcore виклики застаріли й їхній шлях зупиняв завантаження; loader використовує механічну проєкцію стабільних peer-ів.
- lib/process.lisp зазначає, що per-file my-postcore materializer не викликається, бо залежить від старих pre-Contract 11.8 call-heads.
- Вихідні generator і workflow у PR #623 відсутні в main, отже їх унікальна гіпотеза збережена в патчі, але не включена до виконуваного шляху.
- PR #623 залишається джерелом для окремого розгляду, але його старі generated rows (у т.ч. time IDs 1079–1092) не слід механічно відновлювати всупереч теперішньому реєстру.

Артефакти:
- postcore-cache-review.patch — повний text diff усіх семи PR paths (GitHub опускає raw payload binary FASL).
- lib/core.lisp.fasl.base64.txt — точне Base64-представлення branch FASL; blob SHA в manifest.
- manifest.json — original branch head + кожен blob SHA та поточна звірка.

Для переведення ідеї назад в активний код потрібне окреме власницьке рішення в уже наявному #606/#5041 і реалізація проти поточного main; нові гілки не створюються.

