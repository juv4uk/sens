# System One: модель-вчитель → компактна модель

Дата: 2026-10-22. Стан: дослідницький план; навчання моделі ще НЕ запускалося.

## Мета

Модель-вчитель надає спостереження — розподіл імовірностей над п'ятьма допустимими маршрутами звернення. SENS перевіряє тип запитання, домен значень, суму розподілу, впевненість і походження, а потім самостійно вирішує: прийняти, відкласти або відхилити. Вихід моделі не є фактом і не створює нових семантичних ідентичностей.

## Наявні артефакти в main

- **crates/sens-host/src/system_one_model.rs**: локальний loopback-адаптер OpenAI-сумісного сервера. Повертає лише розподіл і provenance; фінальна політика залишається в Lisp/SENS.
- **research/probabilistic-decision-auto-choice-20261021.lisp**: дослідницька політика вибору.
- **research/probabilistic-decision-system-one-20261022.lisp**: типізований пакет запитань і спостережень.
- **research/system-one-support-seed-20261022.jsonl**: 60 синтетичних українських прикладів;
- **research/system-one-support-challenge-20261022.jsonl**: незалежні 60 синтетичних adversarial-прикладів лише для фінальної challenge-перевірки; 5 класів по 12 прикладів; 40 train / 10 validation / 10 test; повторів тексту немає.
- **research/system-one-teacher-observe-20261022.py**: збирає обмежені оцінки вчителя, забороняє зовнішній endpoint і HTTP-перенаправлення.
- **research/system-one-compact-student-20261022.py**: навчає gold/soft-label CPU-базову лінію, генерує ймовірності та надає вузький loopback HTTP API.
- **research/system-one-calibrate-20261022.py**: підбирає температуру лише на validation і не допускає погіршення NLL порівняно з температурою 1.
- **research/system-one-evaluate-20261022.py**: рахує accuracy, macro-F1, Brier, ECE, coverage та selective risk, перевіряючи точну суму розподілу.
- **research/system-one-compare-20261022.py**: одним запуском порівнює вчителя, gold-учня та учня з м'якими цілями; за наявності готових перевірених validation/test прогнозів додає трансформер до того самого звіту. У навчання базових учнів потрапляють лише train-мітки й train-оцінки вчителя; test не використовується ні в навчанні, ні в калібруванні.
- **research/system-one-transformer-student-20261022.py**: необов'язковий тренер справжнього багатомовного класифікаційного трансформера з KL-наслідуванням м'якого розподілу, calibration на validation і loopback HTTP API. Для нього потрібні PyTorch/Transformers і базові ваги; CI ваги не завантажує.
- **tests/test_system_one_research_pipeline.py**: адресна перевірка teacher/student/метрик, HTTP-контракту, калібрування, порівняння та допоміжних законів трансформерного учня. Мережа й ваги моделі для цього тесту не потрібні.
- Точкові HTTP-свідки використовують фіктивні локальні сервери й не потребують завантаженої мовної моделі.

Seed-корпус — лише перевірка формату та початковий набір, не достатня вибірка для заяв про якість реального продукту. Для звітної оцінки слід розширити незалежний тестовий набір і додати реальні, знеособлені звернення лише за наявності законної підстави.

## Рекомендований порядок експерименту

### 1. Зафіксувати відтворюваний запуск учителя

Кандидати для пробного локального порівняння:

- [Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B) — більший учитель для першого досліду; картка моделі вказує Apache-2.0 та сумісність із локальними засобами запуску.
- [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B) — компактний кандидат учня; картка також вказує Apache-2.0 і сумісність із vLLM.

Це кандидати, а не остаточний вибір: перед навчанням треба виміряти доступну пам'ять, швидкість, реальну якість української класифікації та перевірити ліцензію саме завантажених ваг. Qwen повідомляє про підтримку понад 200 мов, зокрема української; це не замінює локального тесту якості українською ([огляд сімейства](https://qwen.ai/blog?id=qwen3.5)).

Для кожного запуску зберігати точний ідентифікатор/ревізію моделі, токенізатор, версії бібліотек, параметри генерації, апаратне забезпечення, випадковий seed і SHA навчальних даних. Обмежити виклики локальним 127.0.0.1; не передавати користувацькі звернення сторонньому сервісу без окремого дозволу.

### 2. Одержати та перевірити вчительські спостереження

На **train**-прикладах учитель повертає розподіл п'яти маршрутів та походження. Зберігати окремо:
- еталонну мітку;
- первісний вихід учителя й необроблені оцінки, якщо сервер їх надає;
- розподіл після нормалізації;
- назву/ревізію моделі, спосіб отримання оцінок і точність квантування;
- результат перевірки SENS та подальше рішення політики.

Не записувати оцінки учителя як еталонну істину. Якщо потрібна мітка не представлена у відповіді або розподіл недопустимий, приклад отримує явну помилку/невідомий стан, а не вигадану ймовірність. Validation можна використовувати для вибору моделі й порога; test лишається недоторканим до остаточного звіту.

У поточному адаптері вихід — розподіл **класів** із першого токена, квантований у точні дроби D48. Це не повний розподіл токенів усієї мовної моделі.

### 3. Порівняти три окремі базові варіанти

1. **Еталонне донавчання:** компактна модель навчається лише на еталонних мітках train.
2. **М'які цільові розподіли:** учитель формує розподіли п'яти класів; компактна класифікаційна голова навчається зі зваженою крос-ентропією або дивергенцією Кульбака—Лейблера до цих розподілів, з еталонними мітками як незалежним контрольним сигналом. Необхідно окремо зберігати вагу внеску учителя й еталонних міток.
3. **Повне токен-рівневе наслідування:** окремий експеримент із **TRL DistillationTrainer**, який навчає учня узгоджувати розподіли наступного токена на власних згенерованих послідовностях. Цей засіб працює з повнішим токен-рівневим сигналом учителя; його не можна вважати автоматично під'єднаним до наявного п'ятикласового адаптера. За потреби відокремленого HTTP-учителя в документації TRL є **AsyncDistillationTrainer**.

Дослідницькі джерела: [TRL DistillationTrainer](https://huggingface.co/docs/trl/en/distillation_trainer), [TRL SDFT](https://huggingface.co/docs/trl/main/sdft_trainer). SDFT — окремий напрям самонаслідування для поступового набуття навичок; не слід змішувати його з першою перевіркою класифікаційного адаптера.

### 4. Міряти не лише точність

У звіті показати:
- точність та macro-F1 загалом і за кожним класом;
- матрицю помилок, зокрема помилки маршруту «невизначено»;
- Brier score та Expected Calibration Error (ECE) для ймовірностей; калібрування температурою на окремому validation;
- coverage (частку запитів, які політика прийняла) і selective risk (помилки серед прийнятих);
- затримку p50/p95, пропускну здатність, пам'ять і розмір моделі;
- порівняння вчителя, учня без донавчання та кожного способу донавчання.

Поріг обирається тільки на validation. Зниження ECE не компенсує падіння точності або небезпечне зростання помилок серед автоматично прийнятих рішень. Публікації 2026 року описують проблеми шуму хвоста, розриву між учителем і учнем та надмірної впевненості в дистиляції ([ACL 2026: Distillation Traps and Guards](https://aclanthology.org/2026.acl-long.908/)); це ще одна причина зберігати незалежний тест і походження даних.

### 5. Поступовий навчальний план

Після першого baseline:
1. виправляти приклади, де учитель суперечить еталонній мітці;
2. додавати нові синтетичні приклади малими тематичними партіями;
3. перевіряти якість кожної партії на validation до наступного кроку;
4. не переносити test-приклади в train і фіксувати кожну версію корпусу;
5. лише після стабільних результатів перевірити curriculum/поступове ускладнення, не вважаючи синтетичний приріст автоматичним доказом якості на реальних даних.

Для curriculum і синтетичного наслідування є свіже дослідження [ICLR 2026: Pedagogically-Inspired Data Synthesis](https://proceedings.iclr.cc/paper_files/paper/2026/hash/b693a240cf1009bff9fa4422141c9392-Abstract-Conference.html). Це напрям для наступного експерименту, не підстава наперед заявляти очікуваний приріст.

## Відтворюваний перший запуск

Після встановлення локального vLLM і перевірки наявної пам'яті виконується так:

```bash
export SENS_SYSTEM_ONE_API_KEY='локальний-тимчасовий-ключ'
vllm serve Qwen/Qwen3.5-2B --host 127.0.0.1 --port 8000 --api-key "$SENS_SYSTEM_ONE_API_KEY"
```

Інший термінал, з кореня репозиторію — зібрати три незалежні порції оцінок і порівняти всі підходи:

```bash
# 1) Учитель оцінює train — тільки ця порція може йти в навчання учня.
python3 research/system-one-teacher-observe-20261022.py \
  --model Qwen/Qwen3.5-2B --split train \
  --input research/system-one-support-seed-20261022.jsonl \
  --output /tmp/system-one-teacher-train.jsonl

# 2) Окрема оцінка validation для виміру та калібрування.
python3 research/system-one-teacher-observe-20261022.py \
  --model Qwen/Qwen3.5-2B --split validation --allow-holdout \
  --input research/system-one-support-seed-20261022.jsonl \
  --output /tmp/system-one-teacher-validation.jsonl

# 3) Окрема оцінка test — лише для остаточного порівняння.
python3 research/system-one-teacher-observe-20261022.py \
  --model Qwen/Qwen3.5-2B --split test --allow-holdout \
  --input research/system-one-support-seed-20261022.jsonl \
  --output /tmp/system-one-teacher-test.jsonl

# 4) Один відтворюваний запуск: учитель проти gold-учня і учня з м'якими оцінками.
# Калібрування обох учнів використовує validation; test не входить у навчання.
python3 research/system-one-compare-20261022.py \
  --input research/system-one-support-seed-20261022.jsonl \
  --teacher-train /tmp/system-one-teacher-train.jsonl \
  --teacher-validation /tmp/system-one-teacher-validation.jsonl \
  --teacher-test /tmp/system-one-teacher-test.jsonl \
  --output-dir /tmp/system-one-comparison \
  --threshold 0.80 --bins 10

# Звіт: /tmp/system-one-comparison/comparison.json
# Містить accuracy, macro-F1, Brier, ECE, coverage та selective risk
# для вчителя, gold-учня й учня з м'якими цілями на validation і test.
# Окреме поле teacher_decoding_agreement показує збіг фактично згенерованої
# літери вчителя з argmax нормованого розподілу; розбіжності явно звітуються.

# 5) Запустити каліброваного компактного учня як локальний HTTP-вузол.
export SENS_SYSTEM_ONE_STUDENT_API_KEY="$SENS_SYSTEM_ONE_API_KEY"
python3 research/system-one-compact-student-20261022.py serve \
  --model-path /tmp/system-one-comparison/student-soft-calibrated.json \
  --port 8100

# SENS host adapter використовує той самий ключ і endpoint:
# (модельний-розподіл-вибору-сире
#   "http://127.0.0.1:8100/v1/chat/completions"
#   "sens.system-one.naive-bayes/1" "текст звернення"
#   "інструкція запитання" ((оплата "платіж") (доставка "посилка")
#                            (технічне "помилка") (обліковий-запис "вхід")
#                            (невизначено "замало даних")))
```

Обробник учителя відхиляє будь-яку адресу, крім `127.0.0.1`, не підставляє відсутні оцінки і записує точний розподіл із сумою `1_000_000_000 / 1_000_000_000`. Для `validation` або `test` збір вчительських оцінок вимагає явного `--allow-holdout`; для навчання учня такі приклади відхиляються. Вихідні дані моделей зберігаються окремо в `/tmp`, не додаються до seed-корпусу.

Перший учень — малий багатокласовий наївний баєсів класифікатор зі словником і логарифмами ймовірностей; він навмисно написаний без сторонніх залежностей, щоб перевірити користь м'яких міток без GPU. Він тепер має вузький HTTP-вузол, який слухає лише 127.0.0.1, перевіряє послідовність п'яти класів і повертає розподіл у форматі, який розуміє SENS host adapter. Це лише базова лінія, не трансформер і не заміна справжньої компактної мовної моделі. Лише якщо вона показує відтворюваний приріст на validation, є сенс переходити до донавчання трансформера Qwen3.5-0.8B або іншого компактного учня.

Документація vLLM підтверджує сумісність Chat Completions, `logprobs` та обмеженого набору `structured_outputs.choice` ([інтерфейс сервера](https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/), [структуровані відповіді](https://docs.vllm.cc/en/latest/features/structured_outputs/)). Вона також попереджає, що ключ сервера не захищає всі його шляхи, тому прив'язка до loopback тут принципова, а не декоративна. Модель Qwen3.5-2B має картку з Apache-2.0 та вказаною сумісністю з vLLM ([картка моделі](https://huggingface.co/Qwen/Qwen3.5-2B)). Фактичну точність українською ці посилання не гарантують — її потрібно виміряти локально.

## Трансформерний експеримент: окрема перевірка наслідування

CPU-наївний Баєс вище — корисний і дешевий контрольний рівень, але він не є малою мовною моделлю. Для наступного рівня додано **research/system-one-transformer-student-20261022.py**. За замовчуванням він використовує **jhu-clsp/mmBERT-small** — багатомовний енкодер приблизно зі 140 млн параметрів; його модельна картка заявляє понад 1800 мов і ліцензію MIT. У картці також є приклад багатомовної класифікації через `AutoModelForSequenceClassification` ([офіційна модельна картка](https://huggingface.co/jhu-clsp/mmBERT-small), [репозиторій авторів](https://github.com/jhu-clsp/mmBERT)). Ці характеристики роблять його слушним кандидатом, але не гарантують точності українською.

Тренер розділяє два сигнали: **еталонна мітка** дає перехресну ентропію, а **м'який розподіл учителя** — дивергенцію Кульбака—Лейблера. Їхня вага задається `--gold-weight`; навчальний приклад із учительським розподілом повинен мати точний відповідний ID, ту саму еталонну мітку й текст, а також той самий SHA корпусу. Тренер не приймає teacher-рядки з `validation` або `test`. Після навчання він обирає скалярну температуру на validation за негативним логарифмом правдоподібності й зберігає provenance. Команда `predict --split test` тільки вимірює відкладений тест. Це класифікаційне наслідування п'яти класів, не повне токен-рівневе наслідування всієї мовної моделі.

Окремий локальний запуск (вимагає PyTorch, Transformers та Accelerate; не запускається в базовому CI):

```bash
python3 -m pip install 'torch>=2.2' 'transformers>=4.48' accelerate

# Teacher train JSONL уже має бути зібраний окремою командою collector.
# Фіксуємо ревізію базових ваг, щоб можна було повторити дослід.
python3 research/system-one-transformer-student-20261022.py train \
  --input research/system-one-support-seed-20261022.jsonl \
  --teacher /tmp/system-one-teacher-train.jsonl \
  --model-name jhu-clsp/mmBERT-small \
  --revision 0eb3d056ec1d6333cf4e19b0966dfde342a41a3a \
  --output-dir /tmp/system-one-mmbert-soft \
  --epochs 3 --batch-size 4 --gold-weight 0.25

# Незалежні прогнози для validation та test; жоден із цих наборів не навчав ваги.
python3 research/system-one-transformer-student-20261022.py predict \
  --model-dir /tmp/system-one-mmbert-soft \
  --input research/system-one-support-seed-20261022.jsonl \
  --split validation --output /tmp/system-one-mmbert-validation.jsonl
python3 research/system-one-evaluate-20261022.py \
  --input /tmp/system-one-mmbert-validation.jsonl \
  --expected-split validation --threshold 0.80

python3 research/system-one-transformer-student-20261022.py predict \
  --model-dir /tmp/system-one-mmbert-soft \
  --input research/system-one-support-seed-20261022.jsonl \
  --split test --output /tmp/system-one-mmbert-test.jsonl
python3 research/system-one-evaluate-20261022.py \
  --input /tmp/system-one-mmbert-test.jsonl \
  --expected-split test --threshold 0.80

# Тепер порівняти teacher, два CPU-базові варіанти та трансформер в одному звіті.
python3 research/system-one-compare-20261022.py \
  --input research/system-one-support-seed-20261022.jsonl \
  --teacher-train /tmp/system-one-teacher-train.jsonl \
  --teacher-validation /tmp/system-one-teacher-validation.jsonl \
  --teacher-test /tmp/system-one-teacher-test.jsonl \
  --transformer-validation-predictions /tmp/system-one-mmbert-validation.jsonl \
  --transformer-test-predictions /tmp/system-one-mmbert-test.jsonl \
  --output-dir /tmp/system-one-comparison-with-transformer \
  --threshold 0.80 --bins 10

# comparison.json тепер містить teacher, student_gold, student_soft та student_transformer.

# Для під'єднання до host адаптера SENS; інструкція/порядок критеріїв мають збігатися.
export SENS_SYSTEM_ONE_STUDENT_API_KEY='локальний-тимчасовий-ключ'
python3 research/system-one-transformer-student-20261022.py serve \
  --model-dir /tmp/system-one-mmbert-soft --port 8101
```

Ваги mmBERT-small можуть завантажуватися під час `train`, якщо їх ще немає в кеші; для відтворення слід зберігати ревізію базової моделі, SHA seed/teacher-даних, версії бібліотек, параметри запуску та виміри пам'яті/швидкості. За потреби відокремлений teacher-token-level experiment можна пізніше порівняти з офіційним [TRL DistillationTrainer](https://huggingface.co/docs/trl/en/distillation_trainer), який працює з повнішими розподілами наступного токена; його не можна вважати тотожним п'ятикласовому loss цього скрипта.

## Незалежний challenge-test: не для навчання і не для добору порога

Файл `research/system-one-support-challenge-20261022.jsonl` містить 60 окремих, синтетично створених складних звернень — по 12 на кожен із п'яти класів. Набір позначено `evaluation_only=true`, він повністю має `split=test`, і в ньому немає нормалізованих текстових збігів із 60 записами seed. Це **challenge-набір для перевірки стійкості після фіксації моделі й порога**, а не заміна реальних звернень і не доказ виробничої якості.

Після завершення основного порівняння запустити окрему оцінку на challenge-наборі. Ці виклики нічого не донавчають і не калібрують:

```bash
# Окремий прогноз вчителя. --allow-holdout тут лише дозволяє оцінку test;
# збережений файл не передавати до жодної команди train.
python3 research/system-one-teacher-observe-20261022.py \
  --model Qwen/Qwen3.5-2B --split test --allow-holdout \
  --input research/system-one-support-challenge-20261022.jsonl \
  --output /tmp/system-one-challenge-teacher.jsonl

# Якщо трансформерний експеримент був виконаний:
python3 research/system-one-transformer-student-20261022.py predict \
  --model-dir /tmp/system-one-mmbert-soft \
  --input research/system-one-support-challenge-20261022.jsonl \
  --split test --output /tmp/system-one-challenge-transformer.jsonl

# Звести звичайний seed і challenge-test в один comparison.json.
# Поріг має бути зафіксований на validation ДО цього виклику.
python3 research/system-one-compare-20261022.py \
  --input research/system-one-support-seed-20261022.jsonl \
  --teacher-train /tmp/system-one-teacher-train.jsonl \
  --teacher-validation /tmp/system-one-teacher-validation.jsonl \
  --teacher-test /tmp/system-one-teacher-test.jsonl \
  --challenge-input research/system-one-support-challenge-20261022.jsonl \
  --challenge-teacher /tmp/system-one-challenge-teacher.jsonl \
  --output-dir /tmp/system-one-comparison-with-challenge \
  --threshold 0.80 --bins 10

# Якщо трансформерний експеримент виконано, додати ці три аргументи до команди вище:
# --transformer-validation-predictions /tmp/system-one-mmbert-validation.jsonl
# --transformer-test-predictions /tmp/system-one-mmbert-test.jsonl
# --challenge-transformer-predictions /tmp/system-one-challenge-transformer.jsonl
# comparison.json матиме секцію challenge.comparison із метриками для всіх доступних моделей.
```

У командах нижче `0.80` — лише приклад уже зафіксованого порога; замінити його на значення, яке було вибране **до challenge-тесту** на validation, і зафіксувати це значення у звіті. Не підбирати поріг за результатом challenge-набору. Якщо його результат спричинив зміну моделі, порога або правил, challenge-набір стає частиною процесу розробки; для чесної наступної оцінки потрібен новий незалежний challenge-набір. Кількість 60 і синтетичне походження треба показувати поруч із метриками.

## Межа виконаного

На момент останнього перегляду в main є локальний адаптер, типізована політика, CPU-наївно-баєсова базова лінія, збирач оцінок, калібрування, порівняльний запуск і необов'язковий тренер багатомовного трансформера; додано синтетичний seed із 60 прикладів та адресується один спільний Python-тестовий набір. Попередня ревізія базового конвеєра проходила CI, але останні зміни для заборони перенаправлень, калібрування, порівняння й трансформерних помічників ще очікують актуального CI. **Реальні ваги не завантажувалися, teacher-прогнози не збиралися, трансформер не навчався, а метрики реального продукту не вимірювалися.** Спершу слід дочекатися адресного тесту поточної ревізії, потім запустити локального вчителя та окремо виміряти CPU-учня і трансформер на train/validation/test.
