# McCarthy's Lisp: from 1958 to a lifetime · Lisp Маккарті: від 1958-го до кінця життя · McCarthys Lisp: von 1958 bis zum Lebensende


## Доповнення 2026-09-20: COND, невизначеність і межа з my-lisp

Первинні джерела дають корисне, але вузьке історичне обґрунтування. У ["Recursive Functions of Symbolic Expressions" (1960)](https://www-formal.stanford.edu/jmc/recursive.pdf) Маккарті задає conditional expression як впорядкований перегляд предикатів зліва направо: значенням стає вираз при першому істинному предикаті, а якщо всі предикати хибні — значення **невизначене**. У математичному викладі предикати мають значення `T` або `F`; це не сучасна generic truthiness.

Практичний LISP I того ж періоду робить цю частковість спостережуваною як named failure: [*LISP I Programmer's Manual*, 1 March 1960](https://softwarepreservation.computerhistory.org/LISP/book/LISP%20I%20Programmers%20Manual.pdf) має помилку `A3 CONDITIONAL UNSATISFIED -EVCON-` для випадку, коли жодна умова не обчислилася як істинна. У ["History of Lisp" (1978)](https://www-formal.stanford.edu/jmc/history/lisp/lisp.html) Маккарті також пояснює походження conditional expressions роботою над шаховими процедурами у FORTRAN для IBM 704 у 1957–58 роках: на відміну від eager `XIF`, справжній conditional expression не обчислює непотрібну гілку.

**Межа аналогії:** канонічний my-lisp `COND` — не реконструкція синтаксису Маккарті. Власне розширення my-lisp має клаузу `(query expected-result expression)` і робить вибір через явне зіставлення observed result з expected datum. Історичний корінь тут лише у двох принципах: ordered/selective evaluation та легітимність відсутності значення при вичерпанні умов. Contract 8.0 робить другий принцип явним як `UnsatisfiedConditional`, а не як тихий `()`.

### English note

McCarthy's 1960 conditional expression is ordered and partial: predicates are examined left-to-right, only the selected branch is evaluated, and exhaustion is undefined. The March 1960 LISP I manual exposes the same boundary as `A3 CONDITIONAL UNSATISFIED -EVCON-`. my-lisp's three-part expected-result matching is its own extension, not a historical claim; Contract 8.0 preserves ordered selective evaluation and makes canonical exhaustion a named `UnsatisfiedConditional` failure.

## English

This document lays out how John McCarthy himself described Lisp's origin and evolution — mainly from his own 1978 retrospective ["History of Lisp"](https://www-formal.stanford.edu/jmc/history/lisp/lisp.html) (written for the ACM SIGPLAN History of Programming Languages conference) and his public writing over the following decades — and where this project deliberately follows or departs from that account. It's history, not a design spec; [`docs/language-core.md`](language-core.md) and [`PLAN.md`](../PLAN.md) are where this project's own decisions live.

### A notation, not a plan for an interpreter

McCarthy's actual starting point was 1958's "Programs with Common Sense" — the "Advice Taker" proposal — an argument that a program could take symbolic facts and derive new ones through formal reasoning, the way a person "takes advice." Lisp grew out of the search for the right notation to write that kind of program: a mathematical formalism for recursive functions on symbolic expressions, not, at first, a programming language meant to be run.

`eval`, the function that could interpret any Lisp expression given as data, started as a *proof* — a demonstration that the notation was expressive enough to describe its own semantics — written on paper, not intended as an implementation. McCarthy said plainly that he hadn't planned to turn it into an interpreter; Steve Russell, one of his students, read the paper's `eval` and hand-coded it into IBM 704 assembly, and Lisp became a running system somewhat by accident.

### Homoiconicity: the "temporary" choice that stuck

Representing programs as the same S-expressions Lisp already used for data was meant to be provisional — a working stand-in until "M-expressions," a more conventional-looking surface syntax, could be designed. M-expressions were never finished. The S-expression notation turned out to be sufficient on its own, and its side effect — code and data sharing one representation — became the property Lisp is best known for: `quote`/`eval` as a pair, macros, programs that write programs. McCarthy's own account frames this as something closer to a fortunate accident than a planned feature.

### The funarg problem: an early bug he lived with

The original LISP 1.5 implementation used dynamic scoping for free variables inside a function — a decision that produced the well-documented "funarg problem": a function passed as an argument and called far from where it was written could pick up bindings from the *caller's* environment instead of the one it was written in, producing surprising, hard-to-predict behavior. McCarthy acknowledged this as a real source of confusion in early Lisp systems. It was Scheme (Guy Steele and Gerald Sussman, from 1975) that fixed it with consistent lexical scoping — a correction to the original design, not something McCarthy changed in real time within LISP 1.5 itself.

### Garbage collection: the mechanism he was proudest of

Lisp was among the first languages with automatic memory management, freeing programmers from manually tracking the lifetime of symbolic data structures. McCarthy treated this as one of Lisp's most durable contributions — an idea that went on to become close to universal in later languages, well beyond Lisp's own lineage.

### Watching the dialects drift apart

By the late 1970s, Lisp had split into a family of mutually incompatible implementations — MacLisp, InterLisp, and eventually a dozen Scheme variants, each with its own idioms and extensions. McCarthy's own history-of-Lisp account treats this fragmentation candidly, neither hiding it nor pretending it was costless: a single language had become a scattered ecosystem. Common Lisp (standardized 1984, ANSI in 1994) was the community's attempt to reunify the split — a consolidation McCarthy regarded as necessary, even though his own instincts ran toward something smaller and closer to the original core than Common Lisp's large specification became.

### Symbolic AI, held to for a lifetime

Lisp was never, for McCarthy, a general-purpose programming language that happened to be good at AI — it was built *for* AI research, specifically the Advice-Taker vision of symbolic, logical reasoning over formally represented knowledge. He continued developing that thread for the rest of his career — circumscription, situation calculus, formalized common-sense reasoning — even as statistical and neural approaches to AI grew to dominate the field commercially and academically. He didn't reject those approaches outright, but his own research stayed with the symbolic, logic-based tradition Lisp was built to serve, up to his death in 2011.

### What he got to see land elsewhere

Late in his life, ideas that started in Lisp — recursion as a first-class tool, conditionals as expressions, garbage collection, higher-order functions, dynamic typing, the read-eval-print loop — had become ordinary features of mainstream languages that owed Lisp no direct lineage. McCarthy's own writing reflects satisfaction at that spread, even where Lisp itself never became the dominant commercial language.

### Where this project follows, and where it doesn't

Per [`PLAN.md`](../PLAN.md)'s Крок 9 and the Philosophy section of the root [`README.md`](../README.md): [`lib/meta-eval.lisp`](../lib/meta-eval.lisp) makes the eval/apply-describes-itself idea literal, not metaphorical; [`lib/unify.lisp`](../lib/unify.lisp) is in the spirit of the Advice Taker's symbolic reasoning; [`tests/fixtures/conformance.lisp`](../tests/fixtures/conformance.lisp) exists specifically so `fpga-lisp`, the project's second implementation, doesn't become "one more incompatible dialect" the way MacLisp/InterLisp/Scheme did (a previously planned third, C-based implementation was dropped 2026-08-09 — see `private/CLAUDE.md`); and the recurring refusal to grow the Rust primitive surface when the existing kernel already suffices is the same instinct that left M-expressions unfinished once S-expressions turned out to be enough. Where this project deliberately departs from LISP 1.5: lexical scoping from the start (the Scheme fix, not the funarg-problem original), and exact rational arithmetic as a stated core purpose — McCarthy's original LISP 1.5 had fixnums and flonums, no exact fractions; that ambition is this project's own, not inherited.

## Українська

Цей документ викладає, як сам Джон Маккарті описував походження й розвиток Lisp — головно з власного ретроспективного огляду 1978 року ["History of Lisp"](https://www-formal.stanford.edu/jmc/history/lisp/lisp.html) (написаного для конференції ACM SIGPLAN з історії мов програмування) та публічних текстів наступних десятиліть — і де цей проєкт свідомо йде за цим викладом, а де відходить від нього. Це історія, не специфікація дизайну; [`docs/language-core.md`](language-core.md) і [`PLAN.md`](../PLAN.md) — там, де живуть власні рішення цього проєкту.

### Нотація, не план інтерпретатора

Реальна відправна точка Маккарті — "Programs with Common Sense" 1958 року, пропозиція "Advice Taker": аргумент, що програма могла б брати символьні факти й виводити нові через формальне міркування, так само як людина "бере пораду". Lisp виріс із пошуку правильної нотації, щоб писати таку програму: математичного формалізму для рекурсивних функцій над символьними виразами, спершу не мови програмування, призначеної для виконання.

`eval` — функція, здатна інтерпретувати будь-який вираз Lisp, поданий як дані — почалась як *доказ*, демонстрація того, що нотація достатньо виразна, щоб описати власну семантику, написана на папері, не задумана як реалізація. Маккарті прямо казав, що не планував перетворювати її на інтерпретатор; Стів Расселл, один з його студентів, прочитав `eval` зі статті й вручну закодував її в асемблер IBM 704 — і Lisp став працюючою системою певною мірою випадково.

### Гомоіконічність: "тимчасовий" вибір, що прижився

Представлення програм тими самими S-виразами, якими Lisp уже користувався для даних, мало бути тимчасовим — робочою заміною, поки не буде спроєктовано "M-expressions", поверхневий синтаксис звичнішого вигляду. M-expressions так і не завершили. Нотація S-виразів виявилась достатньою сама собою, і її побічний ефект — код і дані діляться одним представленням — став властивістю, за якою Lisp найбільш відомий: пара `quote`/`eval`, макроси, програми, що пишуть програми. Власний виклад Маккарті подає це радше як щасливу випадковість, ніж заплановану фічу.

### Funarg problem: рання вада, з якою він жив

Оригінальна реалізація LISP 1.5 використовувала динамічний скоуп для вільних змінних усередині функції — рішення, що породило добре задокументовану "funarg problem": функція, передана як аргумент і викликана далеко від місця, де була написана, могла підхопити зв'язування з середовища *виклику*, а не того, де була написана, даючи несподівану, важкопередбачувану поведінку. Маккарті визнавав це реальним джерелом плутанини в ранніх системах Lisp. Саме Scheme (Гай Стіл і Джеральд Сассман, з 1975 року) виправила це послідовним лексичним скоупом — корекція оригінального дизайну, не те, що Маккарті змінив у реальному часі всередині самого LISP 1.5.

### Garbage collection: механізм, яким він пишався найбільше

Lisp був однією з перших мов з автоматичним керуванням пам'яттю, звільнивши програмістів від ручного відстеження часу життя символьних структур даних. Маккарті трактував це як один з найтриваліших внесків Lisp — ідею, що згодом стала майже універсальною в пізніших мовах, далеко за межами власної lisp-родини.

### Спостерігаючи, як діалекти розбігаються

До кінця 1970-х Lisp розколовся на родину взаємно несумісних реалізацій — MacLisp, InterLisp, і врешті десяток варіантів Scheme, кожен зі своїми ідіомами й розширеннями. Власний історичний виклад Маккарті трактує цю фрагментацію відверто, ані не приховуючи, ані не вдаючи, що вона безкоштовна: одна мова стала розкиданою екосистемою. Common Lisp (стандартизований 1984, ANSI 1994) був спробою спільноти возз'єднати розкол — консолідація, яку Маккарті вважав потрібною, хоча власні інстинкти тягнули його до чогось меншого й ближчого до оригінального ядра, ніж стала велика специфікація Common Lisp.

### Символьний AI, якому лишався вірним усе життя

Lisp ніколи не був для Маккарті мовою загального призначення, що просто добре підходила для AI — вона будувалась *для* AI-досліджень, конкретно для бачення Advice Taker: символьного, логічного міркування над формально представленим знанням. Він продовжував розвивати цю нитку до кінця кар'єри — циркумскрипція, situation calculus, формалізоване здоровоглузде міркування — навіть коли статистичні й нейромережеві підходи до AI стали домінувати комерційно й академічно. Він не відкидав ці підходи повністю, але власні дослідження лишались у символьній, логіко-орієнтованій традиції, для якої й будувався Lisp, аж до смерті 2011 року.

### Що він встиг побачити прижитим деінде

Наприкінці життя ідеї, що почались у Lisp — рекурсія як повноцінний інструмент, умовні вирази як вирази, garbage collection, функції вищого порядку, динамічна типізація, цикл read-eval-print — стали звичайними рисами мейнстрім-мов, які не завдячували Lisp прямою лінією походження. Власні тексти Маккарті відображають задоволення цим поширенням, навіть там, де сам Lisp так і не став домінантною комерційною мовою.

### Де цей проєкт іде за ним, а де ні

За Кроком 9 [`PLAN.md`](../PLAN.md) і розділом Philosophy кореневого [`README.md`](../README.md): [`lib/meta-eval.lisp`](../lib/meta-eval.lisp) робить ідею "eval/apply описує самих себе" буквальною, не метафоричною; [`lib/unify.lisp`](../lib/unify.lisp) — у дусі символьного міркування Advice Taker; [`tests/fixtures/conformance.lisp`](../tests/fixtures/conformance.lisp) існує саме тому, щоб `fpga-lisp`, друга реалізація проєкту, не стала "ще одним несумісним діалектом", як MacLisp/InterLisp/Scheme (раніше запланована третя, C-реалізація прибрана 2026-08-09 — див. `private/CLAUDE.md`); а повторювана відмова розширювати примітивну поверхню Rust, коли наявне ядро вже достатнє — той самий інстинкт, що лишив M-expressions незавершеними, коли S-виразів виявилось достатньо. Де цей проєкт свідомо відходить від LISP 1.5: лексичний скоуп з самого початку (виправлення Scheme, не оригінал з funarg problem), і точна раціональна арифметика як заявлена базова мета — оригінальний LISP 1.5 мав fixnum і flonum, жодних точних дробів; ця амбіція — власна для цього проєкту, не успадкована.

## Deutsch

Dieses Dokument legt dar, wie John McCarthy selbst Ursprung und Entwicklung von Lisp beschrieb — hauptsächlich aus seinem eigenen Rückblick von 1978, ["History of Lisp"](https://www-formal.stanford.edu/jmc/history/lisp/lisp.html) (geschrieben für die ACM-SIGPLAN-Konferenz zur Geschichte der Programmiersprachen), sowie seinen öffentlichen Texten der folgenden Jahrzehnte — und wo dieses Projekt dieser Darstellung bewusst folgt oder von ihr abweicht. Es ist Geschichte, keine Design-Spezifikation; [`docs/language-core.md`](language-core.md) und [`PLAN.md`](../PLAN.md) sind dort, wo die eigenen Entscheidungen dieses Projekts leben.

### Eine Notation, kein Plan für einen Interpreter

McCarthys eigentlicher Ausgangspunkt war "Programs with Common Sense" von 1958 — der "Advice Taker"-Vorschlag: das Argument, ein Programm könne symbolische Fakten aufnehmen und neue durch formales Schließen ableiten, so wie ein Mensch "einen Rat annimmt". Lisp entstand aus der Suche nach der richtigen Notation, um ein solches Programm zu schreiben: ein mathematischer Formalismus für rekursive Funktionen über symbolischen Ausdrücken, zunächst keine zur Ausführung gedachte Programmiersprache.

`eval`, die Funktion, die jeden als Daten gegebenen Lisp-Ausdruck interpretieren konnte, begann als *Beweis* — eine Demonstration, dass die Notation ausdrucksstark genug war, um ihre eigene Semantik zu beschreiben —, auf Papier geschrieben, nicht als Implementierung gedacht. McCarthy sagte unumwunden, er habe nicht geplant, sie in einen Interpreter zu verwandeln; Steve Russell, einer seiner Studenten, las das `eval` aus dem Paper und kodierte es von Hand in IBM-704-Assembler — und Lisp wurde gewissermaßen zufällig zu einem laufenden System.

### Homoikonizität: die "vorläufige" Wahl, die blieb

Programme mit denselben S-Ausdrücken darzustellen, die Lisp bereits für Daten verwendete, sollte vorläufig sein — ein Behelf, bis "M-Expressions", eine konventioneller aussehende Oberflächensyntax, entworfen werden konnte. M-Expressions wurden nie fertiggestellt. Die S-Ausdrucks-Notation erwies sich als für sich genommen ausreichend, und ihr Nebeneffekt — Code und Daten teilen sich eine Darstellung — wurde zu der Eigenschaft, für die Lisp am bekanntesten ist: das Paar `quote`/`eval`, Makros, Programme, die Programme schreiben. McCarthys eigene Darstellung rahmt dies eher als glücklichen Zufall denn als geplantes Feature.

### Das Funarg-Problem: ein früher Fehler, mit dem er lebte

Die ursprüngliche LISP-1.5-Implementierung verwendete dynamischen Scope für freie Variablen innerhalb einer Funktion — eine Entscheidung, die das gut dokumentierte "Funarg-Problem" erzeugte: eine als Argument übergebene und weit entfernt von ihrer Definition aufgerufene Funktion konnte Bindungen aus der Umgebung des *Aufrufers* statt aus der, in der sie geschrieben wurde, übernehmen, was zu überraschendem, schwer vorhersehbarem Verhalten führte. McCarthy erkannte dies als reale Quelle von Verwirrung in frühen Lisp-Systemen an. Es war Scheme (Guy Steele und Gerald Sussman, ab 1975), das dies mit konsistentem lexikalischem Scope behob — eine Korrektur des ursprünglichen Designs, nichts, was McCarthy in Echtzeit innerhalb von LISP 1.5 selbst änderte.

### Garbage Collection: der Mechanismus, auf den er am stolzesten war

Lisp war eine der ersten Sprachen mit automatischer Speicherverwaltung und befreite Programmierer davon, die Lebensdauer symbolischer Datenstrukturen manuell zu verfolgen. McCarthy behandelte dies als einen der dauerhaftesten Beiträge von Lisp — eine Idee, die in späteren Sprachen fast universell wurde, weit über Lisps eigene Abstammungslinie hinaus.

### Zusehen, wie die Dialekte auseinanderdrifteten

Bis Ende der 1970er hatte sich Lisp in eine Familie gegenseitig inkompatibler Implementierungen aufgespalten — MacLisp, InterLisp und schließlich ein Dutzend Scheme-Varianten, jede mit eigenen Idiomen und Erweiterungen. McCarthys eigene Lisp-Geschichte behandelt diese Fragmentierung offen, ohne sie zu verstecken oder vorzugeben, sie sei kostenlos gewesen: eine einzelne Sprache war zu einem verstreuten Ökosystem geworden. Common Lisp (standardisiert 1984, ANSI 1994) war der Versuch der Gemeinschaft, die Spaltung wiederzuvereinen — eine Konsolidierung, die McCarthy für nötig hielt, obwohl seine eigenen Instinkte zu etwas Kleinerem tendierten, näher am ursprünglichen Kern, als es die große Spezifikation von Common Lisp wurde.

### Symbolische KI, ein Leben lang festgehalten

Lisp war für McCarthy nie eine Allzweck-Programmiersprache, die zufällig gut für KI geeignet war — sie wurde *für* KI-Forschung gebaut, konkret für die Advice-Taker-Vision symbolischen, logischen Schließens über formal repräsentiertem Wissen. Er entwickelte diesen Strang für den Rest seiner Karriere weiter — Circumscription, Situation Calculus, formalisiertes Alltagsverstand-Schließen — selbst als statistische und neuronale Ansätze der KI kommerziell und akademisch zu dominieren begannen. Er lehnte diese Ansätze nicht rundweg ab, aber seine eigene Forschung blieb bei der symbolischen, logikbasierten Tradition, für die Lisp gebaut wurde, bis zu seinem Tod 2011.

### Was er noch erlebte, anderswo Fuß zu fassen

Spät in seinem Leben waren Ideen, die in Lisp begannen — Rekursion als erstklassiges Werkzeug, Bedingungen als Ausdrücke, Garbage Collection, Funktionen höherer Ordnung, dynamische Typisierung, die Read-Eval-Print-Schleife — zu gewöhnlichen Merkmalen von Mainstream-Sprachen geworden, die Lisp keine direkte Abstammung schuldeten. McCarthys eigene Schriften spiegeln Zufriedenheit über diese Verbreitung wider, selbst dort, wo Lisp selbst nie zur dominanten kommerziellen Sprache wurde.

### Wo dieses Projekt ihm folgt, und wo nicht

Gemäß Schritt 9 von [`PLAN.md`](../PLAN.md) und dem Philosophie-Abschnitt des Root-[`README.md`](../README.md): [`lib/meta-eval.lisp`](../lib/meta-eval.lisp) macht die Idee "eval/apply beschreibt sich selbst" wörtlich statt metaphorisch; [`lib/unify.lisp`](../lib/unify.lisp) steht im Geiste des symbolischen Schließens des Advice Taker; [`tests/fixtures/conformance.lisp`](../tests/fixtures/conformance.lisp) existiert genau deshalb, damit `fpga-lisp`, die zweite Implementierung des Projekts, nicht zu "noch einem inkompatiblen Dialekt" wird, wie es MacLisp/InterLisp/Scheme wurden (eine zuvor geplante dritte, C-basierte Implementierung wurde am 2026-08-09 gestrichen — siehe `private/CLAUDE.md`); und die wiederkehrende Weigerung, die primitive Rust-Oberfläche wachsen zu lassen, wenn der vorhandene Kern bereits ausreicht, ist derselbe Instinkt, der M-Expressions unfertig ließ, sobald sich S-Ausdrücke als ausreichend erwiesen. Wo dieses Projekt bewusst von LISP 1.5 abweicht: lexikalischer Scope von Anfang an (die Scheme-Korrektur, nicht das Funarg-Problem-Original), und exakte rationale Arithmetik als erklärter Kernzweck — McCarthys ursprüngliches LISP 1.5 hatte Fixnums und Flonums, keine exakten Brüche; dieser Anspruch ist der eigene dieses Projekts, kein ererbter.
