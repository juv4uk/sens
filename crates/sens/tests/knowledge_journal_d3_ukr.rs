//! Справжнє виконання українського журналу знань через D3.
use sens::{eval_program, Session};

#[test]
fn knowledge_journal_filters_events_and_preserves_order_in_sens() {
    let source = include_str!("../../../lib/knowledge.lisp");
    let start = source.find("(визначити внутрішній-зворот-журналу-знань")
        .expect("український D3-механізм");
    let end = source.find("(визначити отримати-події-журналу-окремого-модуля")
        .expect("межа визначення фільтра");
    assert!(start < end);
    let mut session = Session::default();
    // Справжній канонічний Core визначає однобітні так/ні та D3 закони.
    // Голий Session::default() не є завантаженою програмою SENS.
    sens::eval_core_library_source(
        include_str!("../../../lib/core.lisp"),
        &mut session,
    ).expect("виконуваний Core SENS має бути завантажений до бібліотеки знань");
    eval_program(&source[start..end], &mut session)
        .expect("SENS повинен завантажити український D3-код");

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
}
