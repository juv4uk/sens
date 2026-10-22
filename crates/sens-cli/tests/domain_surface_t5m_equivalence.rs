//! Точковий свідок рівноправності поверхонь через фізичний Zig T5M.

const D5_ДЖЕРЕЛО: &str = include_str!("../../../lib/domains/d5.lisp");

fn поле_проєкції<'a>(рядок: &'a str, namespace: &str) -> &'a str {
    let початок = format!("({namespace} ");
    let решта = рядок
        .split_once(&початок)
        .unwrap_or_else(|| panic!("немає поля {namespace} у D5-рядку"))
        .1;
    решта.split_once(')').expect("закрите поле проєкції").0
}

#[test]
fn українська_й_англійська_проєкції_зберігаються_через_t5m_тріти() {
    let український_рядок = D5_ДЖЕРЕЛО
        .lines()
        .map(str::trim)
        .find(|рядок| рядок.contains("(ук додати)"))
        .expect("українська проєкція додавання має бути в чинному D5-джерелі");
    assert_eq!(поле_проєкції(український_рядок, "ук"), "додати");
    let біти = український_рядок
        .strip_prefix('(')
        .expect("відкритий запис доменного слова")
        .split_whitespace()
        .next()
        .expect("точне доменне слово перед українською поверхнею");

    let слова = sens::parse_binary_source_words(біти).expect("точне слово із D5-джерела");
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
    assert_eq!(відновлені_біти, біти);
    let англійський_рядок = D5_ДЖЕРЕЛО
        .lines()
        .map(str::trim)
        .find(|рядок| рядок.starts_with(&format!("({відновлені_біти} ")))
        .expect("відновлене слово має знайти ту саму доменну identity");
    assert_eq!(поле_проєкції(англійський_рядок, "en"), "plus");
}
