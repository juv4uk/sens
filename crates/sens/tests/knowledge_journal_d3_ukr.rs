//! Справжнє виконання українського журналу знань через D3.
use sens::{eval_program, Session};

#[test]
fn knowledge_journal_filters_events_and_preserves_order_in_sens() {
    let source = include_str!("../../../lib/knowledge.lisp");
    let start = source.find("(визначити внутрішній-зворот-журналу-знань")
        .expect("український D3-механізм");
    // Свідку потрібні обидві частини: фільтр подій і застосування tell.
    // Межа перед знання-символ? випадково виключала пізніше визначення
    // застосувати-одну-подію-журналу, яке перевіряється нижче.
    let end = source.find("(визначити модуль-клаузи-зараз")
        .expect("межа після виконуваних функцій журналу");
    assert!(start < end);
    let mut session = Session::default();
    // Справжній канонічний Core визначає однобітні так/ні та D3 закони.
    // Голий Session::default() не є завантаженою програмою SENS.
    sens::eval_core_library_source(
        include_str!("../../../lib/core.lisp"),
        &mut session,
    ).expect("виконуваний Core SENS має бути завантажений до бібліотеки знань");
    // Власний читач SENS задає exact D1 істину й чинні коди.
    // Звичайне текстове eval_program не є тим самим маршрутом для
    // українських доменних голів (зокрема безумовного «так»).
    let parsed = sens::parse_mixed_exact_domain_reasoning_source(
        "lib/knowledge.lisp",
        &source[start..end],
    ).expect("читач D1–D11 має розібрати програму");
    sens::eval_parsed_expressions(&parsed, &mut session)
        .expect("SENS повинен виконати точні D3 визначення");

    let journal = "(як-є ((tell alpha a) (tell beta b) (tell alpha c)))";
    let call = format!(
        "(додати-події-журналу-модуля (як-є alpha) {journal} (як-є ()))"
    );
    let actual = eval_program(&call, &mut session)
        .expect("SENS реально вибирає події")
        .value.to_string();
    let expected = eval_program("(як-є ((tell alpha a) (tell alpha c)))", &mut session)
        .expect("очікуваний список зі справжнього читача SENS")
        .value.to_string();
    assert_eq!(actual, expected, "порушено порядок або відбір");

    // Неповні записи пропускаємо; SENS сам доводить збереження порядку.
    let incomplete = "(як-є (самотня-подія (tell) () (tell alpha a) (tell beta b) (tell alpha c)))";
    let filtered = eval_program(
        &format!("(додати-події-журналу-модуля (як-є alpha) {incomplete} (як-є ()))"),
        &mut session,
    ).expect("неповні події не ламають справжній SENS-eval")
     .value.to_string();
    assert_eq!(filtered, expected, "неповні події не змінюють коректні alpha-записи");

    let absent = eval_program(
        &format!("(додати-події-журналу-модуля (як-є gamma) {journal} (як-є ()))"),
        &mut session,
    ).expect("відсутній модуль").value.to_string();
    let empty = eval_program("(як-є ())", &mut session)
        .expect("порожній список").value.to_string();
    assert_eq!(absent, empty);

    let reversed = eval_program(
        "(внутрішній-зворот-журналу-знань (як-є (a b c)) (як-є ()))",
        &mut session,
    ).expect("виконується D3-обернення").value.to_string();
    let expected_reversed = eval_program("(як-є (c b a))", &mut session)
        .expect("очікуваний D3-список").value.to_string();
    assert_eq!(reversed, expected_reversed);

    // Позитивний і негативний D1 свідки без невизначених голих так/ні.
    let yes = eval_program("(атом? (як-є ()))", &mut session)
        .expect("справжнє D1 YES").value.to_string();
    let no = eval_program("(атом? (як-є (запис)))", &mut session)
        .expect("справжнє D1 NO").value.to_string();
    let found = eval_program(
        "(журнал-містить-записи-модуля? (як-є alpha) (як-є ((tell alpha a) (tell beta b))))",
        &mut session,
    ).expect("SENS знаходить модуль").value.to_string();
    assert_eq!(found, yes, "дійсний модуль має повертати D1 YES");

    let missing = eval_program(
        "(журнал-містить-записи-модуля? (як-є alpha) (як-є ((tell) (tell beta b))))",
        &mut session,
    ).expect("неповна подія не повинна ламати SENS").value.to_string();
    assert_eq!(missing, no, "неповна подія не є свідком модуля");

    // Справжній SENS: лише подія з трьома полями може підтверджувати
    // існування модуля й потрапляти до журналу.
    let malformed_events =
        "(як-є ((tell alpha x зайве) (tell alpha y . хибний-хвіст) (tell beta b)))";
    let falsely_known = eval_program(
        &format!("(журнал-містить-записи-модуля? (як-є alpha) {malformed_events})"),
        &mut session,
    ).expect("пошкоджені записи не засвідчують модуль").value.to_string();
    assert_eq!(falsely_known, no, "неправильна арність не доводить існування модуля");

    let mixed_events =
        "(як-є ((tell alpha x зайве) (tell alpha y . хибний-хвіст) (tell alpha запис)))";
    let selected = eval_program(
        &format!("(додати-події-журналу-модуля (як-є alpha) {mixed_events} (як-є ()))"),
        &mut session,
    ).expect("справжній SENS пропускає зайві поля, зберігає правильну подію")
     .value.to_string();
    let valid_only = eval_program("(як-є ((tell alpha запис)))", &mut session)
        .expect("канонічна трійка").value.to_string();
    assert_eq!(selected, valid_only, "зіпсована подія не входить до журналу");

    // Пошкоджені події не можуть приховувати правильний запис,
    // який зустрічається далі. Перевірка проходить через справжній SENS.
    let recovered = eval_program(
        "(журнал-містить-записи-модуля? (як-є alpha) (як-є (самотня-подія (tell) (tell beta b) (tell alpha a))))",
        &mut session,
    ).expect("SENS знаходить модуль після пошкоджених подій")
     .value.to_string();
    assert_eq!(recovered, yes, "неповна подія не приховує наступне правильне свідчення");

    // Справжній SENS не повинен обчислювати Д4 «третє» на короткій події.
    // Залишаємо існуючі клаузи без зміни на кожному зіпсованому вході.
    let clauses = "(як-є (залишити))";
    let original = eval_program(clauses, &mut session)
        .expect("чинні клаузи")
        .value.to_string();
    for malformed in [
        "(як-є ())",
        "(як-є tell)",
        "(як-є (tell))",
        "(як-є (tell alpha))",
        "(як-є (retract alpha))",
        // Подія з трьома полями не може приховувати четверте або
        // неправильний крапковий хвіст: це не канонічний журнал.
        "(як-є (tell alpha запис зайве))",
        "(як-є (tell alpha запис . пошкоджений-хвіст))",
        "(як-є (retract alpha запис зайве))",
        "(як-є (retract alpha запис . пошкоджений-хвіст))",
        // Внутрішня пара не є атомною міткою дії і не доходить до D3 EQ.
        "(як-є ((tell) alpha запис))",
        "(як-є ((retract) alpha запис))",
    ] {
        let expression = format!("(застосувати-одну-подію-журналу {clauses} {malformed})");
        let actual = eval_program(&expression, &mut session)
            .expect("пошкоджена подія не читає відсутнє третє поле")
            .value.to_string();
        assert_eq!(actual, original, "подія {malformed} пошкодила чинні клаузи");
    }
    // Позитивний свідок: правильна трійка tell додає факт через Д3 сполучити.
    let added = eval_program(
        "(застосувати-одну-подію-журналу (як-є (залишити)) (як-є (tell alpha запис)))",
        &mut session,
    ).expect("правильна подія tell виконується у SENS")
     .value.to_string();
    let expected_added = eval_program("(як-є (запис залишити))", &mut session)
        .expect("очікувані клаузи")
        .value.to_string();
    assert_eq!(added, expected_added, "перевірка неповних подій не змінює закон tell");
}
