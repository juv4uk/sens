# Від Lisp Маккарті до машини, що працює зі змістом: Стратегія розвитку · From McCarthy's Lisp to a Machine That Works with Meaning: Development Strategy · Von McCarthys Lisp zur bedeutungsverarbeitenden Maschine: Entwicklungsstrategie

## Українська

### 1. Поточний стан (Фундамент)
Ми успішно реалізували базове бачення Маккарті з "Advice Taker" (1958):
- **Символьний рушій (Unification & Backward Chaining)**: Мова `my-lisp` здатна робити логічні висновки (`reason`) з фактів та правил.
- **Модульність Знань (Knowledge Packages)**: Система підтримує завантаження модулів (`physics`, `astronomy`) через `defmodule` і здійснює ізольовані запити через `reason-in`.
- **Пояснення (Explainability)**: Завдяки `explain-proof` рушій пояснює *як* він дійшов висновку.

### 2. Найважливіший наступний крок: NLP Bridge
Головна мета "Advice Taker" — можливість сказати машині факт природною мовою, щоб вона його зрозуміла і використовувала.
Зараз знання записуються у Lisp-синтаксисі. Наступний крок — створення **NLP Bridge** (Містка Природної Мови).

Перша, експериментальна версія цього мосту (`crates/my-lisp-cli/src/llm.rs`, команди REPL `:tell`/`:ask`) була реалізована й далі видалена — вона додала мережеву залежність і зовнішній API-ключ без тестів і без trilingual-конвенції проєкту. Якщо цей крок повертається, він має заслуговувати того ж рівня строгості, що `reason.lisp`/`unify.lisp`, а не лишатись REPL-хаком.

#### Як це працюватиме:
1. **Інтерфейс**: Користувач вводить текст: "Всі планети мають масу. Земля - планета."
2. **LLM Translation**: Мовна модель (LLM) перекладає цей текст у Lisp-структури:
   ```lisp
   ((has-mass (var x)) (planet (var x)))
   ((planet earth))
   ```
3. **Symbolic Verification**: Lisp-рушій валідує ці знання на суперечності з існуючою базою знань.
4. **Integration**: Нові правила автоматично додаються в поточний модуль через `defmodule`.

### 3. Майбутні напрямки
- **Динамічне навчання (Dynamic Learning)**: Здатність системи самостійно створювати нові модулі знань, коли LLM стикається з невідомою сферою (наприклад, автоматичне створення `biology.lisp`).
- **Гібридний агент (Hybrid Agent)**: Поєднання гнучкості LLM (для розпізнавання намірів і тексту) зі строгою логікою Lisp (для гарантії відсутності галюцинацій).

### Висновок
Ми успішно завершили створення символьного ядра. Тепер ми переходимо до створення гібридної AI-системи, де LLM є "очима та вухами", а `my-lisp` — "раціональним мозком".

## English

### 1. Current state (foundation)
We have successfully implemented McCarthy's core "Advice Taker" vision (1958):
- **Symbolic engine (unification & backward chaining)**: `my-lisp` can draw logical inferences (`reason`) from facts and rules.
- **Knowledge modularity (knowledge packages)**: the system supports loading modules (`physics`, `astronomy`) via `defmodule`, and isolated per-module queries via `reason-in`.
- **Explainability**: `explain-proof` lets the engine explain *how* it reached a conclusion.

### 2. The most important next step: NLP bridge
The core goal of "Advice Taker" is being able to tell the machine a fact in natural language and have it understand and use it.
Right now knowledge is written in Lisp syntax. The next step is building an **NLP bridge**.

A first, experimental version of this bridge (`crates/my-lisp-cli/src/llm.rs`, the REPL's `:tell`/`:ask` commands) was built and then removed — it added a network dependency and an external API key with no tests and no trilingual convention. If this step returns, it should earn the same rigor as `reason.lisp`/`unify.lisp`, not stay a REPL hack.

#### How it will work:
1. **Interface**: the user types text: "All planets have mass. Earth is a planet."
2. **LLM translation**: a language model (LLM) translates this text into Lisp structures:
   ```lisp
   ((has-mass (var x)) (planet (var x)))
   ((planet earth))
   ```
3. **Symbolic verification**: the Lisp engine validates this knowledge for contradictions against the existing knowledge base.
4. **Integration**: new rules are automatically added to the current module via `defmodule`.

### 3. Future directions
- **Dynamic learning**: the system's ability to create new knowledge modules on its own when the LLM encounters an unfamiliar domain (e.g. automatically creating `biology.lisp`).
- **Hybrid agent**: combining the LLM's flexibility (for recognizing intent and parsing text) with Lisp's strict logic (to guarantee no hallucinations).

### Conclusion
We have successfully completed the symbolic core. We are now moving toward a hybrid AI system, where the LLM is the "eyes and ears," and `my-lisp` is the "rational brain."

## Deutsch

### 1. Aktueller Stand (Fundament)
Wir haben McCarthys Kernvision des "Advice Taker" (1958) erfolgreich umgesetzt:
- **Symbolische Engine (Unifikation & Backward Chaining)**: `my-lisp` kann logische Schlussfolgerungen (`reason`) aus Fakten und Regeln ziehen.
- **Wissensmodularität (Knowledge Packages)**: das System unterstützt das Laden von Modulen (`physics`, `astronomy`) über `defmodule` und isolierte Anfragen pro Modul über `reason-in`.
- **Erklärbarkeit**: Dank `explain-proof` erklärt die Engine, *wie* sie zu einer Schlussfolgerung gelangt ist.

### 2. Der wichtigste nächste Schritt: NLP-Brücke
Das Kernziel des "Advice Taker" ist es, der Maschine eine Tatsache in natürlicher Sprache mitteilen zu können, sodass sie diese versteht und nutzt.
Derzeit wird Wissen in Lisp-Syntax geschrieben. Der nächste Schritt ist der Bau einer **NLP-Brücke**.

Eine erste, experimentelle Version dieser Brücke (`crates/my-lisp-cli/src/llm.rs`, die REPL-Befehle `:tell`/`:ask`) wurde gebaut und dann wieder entfernt — sie brachte eine Netzwerkabhängigkeit und einen externen API-Schlüssel ohne Tests und ohne trilinguale Konvention mit sich. Kehrt dieser Schritt zurück, sollte er sich dieselbe Sorgfalt wie `reason.lisp`/`unify.lisp` verdienen, statt ein REPL-Hack zu bleiben.

#### Wie es funktionieren wird:
1. **Schnittstelle**: der Nutzer gibt Text ein: "Alle Planeten haben Masse. Die Erde ist ein Planet."
2. **LLM-Übersetzung**: ein Sprachmodell (LLM) übersetzt diesen Text in Lisp-Strukturen:
   ```lisp
   ((has-mass (var x)) (planet (var x)))
   ((planet earth))
   ```
3. **Symbolische Verifikation**: die Lisp-Engine prüft dieses Wissen auf Widersprüche zur bestehenden Wissensbasis.
4. **Integration**: neue Regeln werden automatisch über `defmodule` zum aktuellen Modul hinzugefügt.

### 3. Zukünftige Richtungen
- **Dynamisches Lernen**: die Fähigkeit des Systems, selbstständig neue Wissensmodule zu erstellen, wenn das LLM auf ein unbekanntes Gebiet stößt (z. B. automatisches Erstellen von `biology.lisp`).
- **Hybrider Agent**: Kombination der Flexibilität des LLM (zur Erkennung von Absicht und Text) mit der strikten Logik von Lisp (zur Garantie, dass keine Halluzinationen auftreten).

### Fazit
Wir haben den symbolischen Kern erfolgreich fertiggestellt. Wir bewegen uns nun auf ein hybrides KI-System zu, in dem das LLM die "Augen und Ohren" ist und `my-lisp` das "rationale Gehirn".
