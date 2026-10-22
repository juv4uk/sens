use sens::{eval_program, Session};

// Чинний SENS виконує всі чотири людиночитні проєкції сам:
// Python/JSON та історичний SID8 тут не беруть участі.
// Це перевірка обчислення, не заміна тестів офлайнового перекладача.
#[test]
fn current_domain_projections_execute_without_python_or_sid8() {
    let programs = [
        ("англійська", "(car (cons 'cat 'dog))"),
        ("українська компактна", "(перше (сполучити 'cat 'dog))"),
        ("українська повна", "(перше (сполучити 'cat 'dog))"),
        ("санскритська", "(ādi (saṃyuj 'cat 'dog))"),
    ];

    for (surface, source) in programs {
        let mut session = Session::default();
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("{surface}: SENS runtime error: {error}"));
        assert_eq!(result.value.to_string(), "cat", "{surface}");
    }
}
