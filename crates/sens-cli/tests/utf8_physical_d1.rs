//! Фізичний SENS-свідок: Zig передає точні слова, SENS обчислює D1.
#![cfg(feature = "zig-transport")]

use sens::{load_core_library, load_utf8_library, PhysicalT5Program, Session};
use sens_cli::zig_transport::{decode_t5m_exact_words, encode_t5m_exact_words};

struct PairDirectory(std::path::PathBuf);

impl Drop for PairDirectory {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

fn verify_source_pair(source: &std::path::Path, physical: &[u8]) {
    let nonce = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let path = std::env::temp_dir().join(format!("sens-utf8-pair-{}-{nonce}", std::process::id()));
    std::fs::create_dir(&path).unwrap();
    let directory = PairDirectory(path);
    let minted = directory.0.join("law.sens");
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg("--t5m-mint-pair")
        .arg(source)
        .arg(&minted)
        .output()
        .expect("чинний frontend передає укр-джерело кодеку Zig T5M");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        std::fs::read(minted).unwrap(),
        physical,
        "закомічений .sens має точно відповідати чинній укр-проєкції"
    );
}

fn program(physical: &[u8]) -> PhysicalT5Program {
    let words = decode_t5m_exact_words(physical)
        .expect("фізичний свідок декодується тільки Zig")
        .into_iter()
        .map(|word| {
            sens::ExactDomainWord::from_physical_width_bits(word.width, &word.bits)
                .expect("точне слово SENS після Zig")
        })
        .collect();
    PhysicalT5Program::from_exact_domain_words_owned(words).expect("двійковий SENS-свідок")
}

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("фізичний Core4 bootstrap");
    load_utf8_library(&mut session).expect("фізичний UTF-8 bootstrap");
    session
}

#[test]
fn utf8_direct_d1_self_verdict_and_one_bit_mutant() {
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../tests/semantic/utf8-direct-d1-law.sens");
    let physical = std::fs::read(&path).expect("закомічений фізичний SENS-свідок");
    verify_source_pair(&path.with_extension("lisp"), &physical);
    let law = program(&physical);
    assert_eq!(law.form_count(), 2, "два мовні структурні закони");
    let mut positive = session();
    for form in law.forms() {
        let result = sens::eval_parsed_expressions(std::slice::from_ref(form), &mut positive)
            .expect("SENS виконує фізичний структурний закон");
        assert_eq!(result.value.as_predicate_bit(), Some(true));
    }

    // Єдиний D1:0 — очікувана відповідь першого закону. Міняємо тільки
    // його біт; цифри всередині D7 та числових доменів не зачіпаємо.
    let mut words = decode_t5m_exact_words(&physical).unwrap();
    let false_bits = words
        .iter()
        .enumerate()
        .filter(|(_, word)| word.width == 1 && word.bits == [0])
        .map(|(index, _)| index)
        .collect::<Vec<_>>();
    assert_eq!(
        false_bits.len(),
        1,
        "один точний D1-біт для негативного свідка"
    );
    words[false_bits[0]].bits[0] = 1;
    let mutant = encode_t5m_exact_words(&words).expect("Zig кодує однобітний мутант");
    let mutant_path = path.with_file_name("utf8-direct-d1-mutant.sens");
    let committed_mutant = std::fs::read(&mutant_path).expect("фізичний негативний SENS-свідок");
    verify_source_pair(&mutant_path.with_extension("lisp"), &committed_mutant);
    assert_eq!(
        mutant, committed_mutant,
        "негативний свідок змінює тільки один точний D1 біт"
    );
    let mutated = program(&committed_mutant);
    let mut negative = session();
    let error = sens::eval_parsed_expressions(&mutated.forms()[..1], &mut negative)
        .expect_err("SENS має відхилити хибний висновок самого закону");
    assert_eq!(error.kind, sens::ErrorKind::Type);
}
