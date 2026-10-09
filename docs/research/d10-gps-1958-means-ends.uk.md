# D10 — ранній символьний ШІ: GPS (1958–1959)

Статус: RESEARCH HOLD, 0 SELECT, 0 координат, 0 ратифікацій. Координація #4977 #4988 #4013 #4463.

## Історичний скарб

Allen Newell, J. C. Shaw, Herbert A. Simon, RAND P-1584, Report on a General Problem-Solving Program (1958, revised 1959). Оригінальні сторінки 10–11 (рис. 2): three goal types (transform a→b; apply operator q to a; reduce difference d between a and b). The method looks for an operator relevant to a difference, then makes satisfying its operator precondition into a subgoal. Primary: https://home.mis.u-picardie.fr/~furst/docs/Newell_Simon_General_Problem_Solving_1959.pdf.

Не слід плутати з MacCarthy's Advice Taker (1958/1959), Robinson resolution 1965 чи STRIPS 1971 goal regression. GPS був раннім проривом в організації планування за різницею поточного і бажаного стану, а не повним сучасним планувальником.

## Три дослідницькі закони

1. `GPS-FINITE-STATE-DIFFERENCES` — за явного скінченного універсуму фактів U, стану S й цілі G: відсутні G\S, зайві S\G. Це повна двійкова модель стану; для часткових цілей потрібна інша семантика.
2. `GPS-OPERATOR-DIFFERENCE-WITNESS` — для оператора з множинами add/delete показати, які саме відсутні факти може додати і які зайві вилучити. Це свідок **релевантності**, а НЕ гарантія виконуваності, прогресу або плану.
3. `GPS-OPERATOR-PRECONDITION-SUBGOALS` — знайти невиконані передумови оператора. Коли є хоча б одна, застосування заблоковане, але ці умови придатні для постановки наступної підцілі.

Контрприклад: S={battery}, G={battery,signal}; оператор одночасно додає signal та вилучає battery. Він релевантний для однієї різниці, але не є прогресом до повної цілі. GPS-style heuristic must not silently pretend to prove reachability.

## Межа SENS

D9 уже містить `UNIFY`, `PROVE-GOAL`, `FIRE-RULE`, JTMS, підтримку/відкликання фактів. D10 вже має `SEARCH`, `PROVE-RULE`, `PROVE-GOAL-STATE`. Паралельні дослідження: STRIPS #4986, IPL Logic Theorist #4988, абдукція #4965, ATMS #4958, уніфікація й резолюція. Не переводимо жодну назву в D10 selected, доки не доведено **семантичну відмінність від цих наявних законів** і потребу саме у Core, а не бібліотеці. Керування і синтаксис незмінно за D2.

## Докази

`knowledge/d10-gps-means-ends-historical-research-20261009.json`: точні назви, три поведінкові контракти, спостереження, фальсифікатори, п'ять HOLD.
`tests/oracles/d10_gps_means_ends_swi.pl`: 17 перевірюваних свідків у реальному SWI-Prolog. Це власна **сучасна реконструкція** мінімальної Boolean-частини GPS, НЕ історичний оригінальний IPL-V runtime і НЕ виконання SENS.
`scripts/check_d10_gps_means_ends_history.py`: 10 негативних мутацій джерела, невигаданих координат, ратифікації, семантик і тестів.

## Зв'язок з авторськими захопленнями

Advice Taker / програмні агенти: вибрати операцію, яка усуває конкретну різницю. Паніні: окремо довести, чи граматичне правило змінює відповідну ознаку. SDR/FPGA: діагностувати передумови переналаштування. Астрономія: плани калібрування/спостереження. У цих прикладах немає нових авторитетних бітових інструкцій.

Після історичного перепису: незалежне поведінкове доведення проти D1–D10 → вихідна версія від іншого runtime → owner review → canonical ledger PROPOSE → можливий SELECT → окрема ратифікація; саме дослідження не збільшує 635/1024.
