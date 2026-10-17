//! Точковий свідок рівноправності поверхонь через фізичний Zig T5M.

const D5_ДЖЕРЕЛО: &str = include_str!("../../../lib/domains/d5.lisp");

fn поле_проєкції<'a>(рядок: &'a str, namespace: &str) -> &'a str {
    let початок = format!("({namespace} ");
    let решта = рядок
        .split_once(&початок)
        .unwrap_or_else(|| panic!("немає поля {namespace} у D5-рядку"))
        .1;
    решта
        .split_once(')')
        .expect("закрите поле проєкції")
        .0
}

#[test]
fn українська_й_англійська_проєкції_зберігаються_через_t5m_тріти() {
    let рядок = D5_ДЖЕРЕЛО
        .lines()
        .map(str::trim)
        .find(|рядок| рядок.starts_with("(01010 "))
        .expect("D5:01010 має бути в чинному доменному джерелі");
    let ук = поле_проєкції(рядок, "ук");
    let en = поле_проєкції(рядок, "en");
    assert_eq!(ук, "додати");
    assert_eq!(en, "plus");

    let слова = sens::parse_binary_source_words("01010")
        .expect("точне слово D5 із джерела домену");
    let [слово] = слова.as_slice() else {
        panic!("очікувалося одне слово D5");
    };
    let тотожність = sens::DomainIdentity::from_source_word(слово.word);
    assert!(matches!(тотожність, sens::DomainIdentity::D5(_)));
    assert_eq!(тотожність.width(), 5);

    let трити = sens_cli::zig_transport::encode_t5_direct(&[слово.word])
        .expect("Zig має запакувати точне слово D5 кодеком T5M");
    let відновлені = sens_cli::zig_transport::decode_t5_words(&трити)
        .expect("Zig має відновити точні слова з T5M");
    assert_eq!(відновлені, [слово.word]);

    let відновлені_біти = відновлені[0].to_string();
    assert_eq!(відновлені_біти, "01010");
    assert_eq!(поле_проєкції(рядок, "en"), en);
    assert_eq!(поле_проєкції(рядок, "ук"), ук);
}
