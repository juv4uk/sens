#[test]
#[ignore = "фінальний gate: увімкнути після завершення UK/EN/SA parity"]
fn повне_рівноправя_вимагає_наявності_для_всіх_людських_поверхонь() {
    let корінь = корінь_реєстру();
    for запис in записи_реєстру(&корінь) {
        let (ідентифікатор, _) = поверхні(запис);
        if ідентифікатор == "\"00000000\"" {
            continue;
        }
        let наявні = ["uk", "en", "sa"].map(|surface| рядок(запис, surface).1.is_some());
        assert!(
            наявні.iter().all(|наявне| *наявне),
            "{ідентифікатор}: UK/EN/SA ще не заповнені одночасно"
        );
    }
}#[test]
#[ignore = "фінальний gate: увімкнути після завершення UK/EN/SA parity"]
fn повне_рівноправя_вимагає_наявності_для_всіх_людських_поверхонь() {
    for id in registry_ids() {
        if id == 0 { continue; }
        let rows = registry_surfaces(id);
        let present = ["uk", "en", "sa"]
            .iter()
            .all(|namespace| rows.iter().any(|row| row.namespace == *namespace));
        assert!(present, "{}: UK/EN/SA ще не заповнені одночасно", registry_id_bits(id));
    }
}
