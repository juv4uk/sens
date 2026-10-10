//! #5406: фізичний T5 не може називати людський файл файлової влади
//! канонічним D2. Це доказ межі кодера, не реалізація компілятора.
use std::{
    fs::{self, OpenOptions},
    io::Write,
    path::PathBuf,
    process::{Command, Output},
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);

struct TemporaryPair {
    source: PathBuf,
    physical: PathBuf,
}

impl TemporaryPair {
    fn new(source: &str) -> Self {
        let nonce = NEXT.fetch_add(1, Ordering::Relaxed);
        let source_path = std::env::temp_dir().join(format!(
            "sens-file-authority-boundary-{}-{nonce}.lisp",
            std::process::id()
        ));
        let physical = source_path.with_extension("sens");
        let mut file = OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(&source_path)
            .expect("виключно нове тимчасове джерело");
        file.write_all(source.as_bytes())
            .expect("тимчасовий доказовий вхід");
        assert!(!physical.exists(), "фізичний свідок не може вже існувати");
        Self { source: source_path, physical }
    }

    fn trit(&self, command: &str) -> Output {
        Command::new(env!("CARGO_BIN_EXE_sens-trit"))
            .arg(command)
            .arg(if command == "encode" { &self.source } else { &self.physical })
            .output()
            .expect("запустити справжній sens-trit")
    }
}

impl Drop for TemporaryPair {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.source);
        let _ = fs::remove_file(&self.physical);
    }
}

fn rejected_without_physical_file(source: &str) {
    let pair = TemporaryPair::new(source);
    let rejected = pair.trit("encode");
    assert!(!rejected.status.success(), "неканонічний текст не є SENS T5");
    assert!(rejected.stdout.is_empty(), "відхилений файл не дає позитивного доказу");
    assert!(
        String::from_utf8_lossy(&rejected.stderr).contains("InvalidBinaryProjection"),
        "очікувана іменована відмова, stderr={:?}",
        rejected.stderr
    );
    assert!(
        !pair.physical.exists(),
        "після відмови кодера не можна залишати фізичний .sens"
    );
}

#[test]
fn exact_d2_projection_reaches_physical_t5_and_current_sens() {
    // D3 QUOTE(D3 EMPTY): один канонічний D2-вираз, без текстових імен.
    const WORDS: &str = "10 001 00 000 01";
    let pair = TemporaryPair::new(&format!("{WORDS}\n"));
    let encoded = pair.trit("encode");
    assert!(encoded.status.success(), "T5 encode: {:?}", encoded.stderr);
    let physical = fs::read(&pair.physical).expect("байти T5 реально створено");
    assert!(!physical.is_empty());
    assert!(physical.iter().all(|byte| *byte < 243));
    assert_eq!(sens::open_ternary_program(&physical).unwrap(), WORDS);
    assert_eq!(sens::encode_binary_projection_ternary(WORDS).unwrap(), physical);
    let opened = pair.trit("open");
    assert!(opened.status.success(), "physical open: {:?}", opened.stderr);
    assert_eq!(opened.stdout, format!("{WORDS}\n").as_bytes());
    let executed = Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg(&pair.physical)
        .output()
        .expect("фізичне виконання через SENS");
    assert!(executed.status.success(), "physical eval: {:?}", executed.stderr);
    assert_eq!(executed.stdout, b"()\n");
}

#[test]
fn ratified_uk_d1_cond_triplet_is_physical_without_text_fallback() {
    // Вузький уже перевірений український D1/D3 свідок, не довільний компілятор.
    const SOURCE: &str =
        include_str!("../../../tests/fixtures/migration-d1-cond-cohort/branch.lisp");
    const PHYSICAL: &[u8] =
        include_bytes!("../../../tests/fixtures/migration-d1-cond-cohort/branch.sens");
    const VIEW: &str =
        include_str!("../../../tests/fixtures/migration-d1-cond-cohort/branch");

    assert!(SOURCE.contains("за-умовою"));
    assert!(SOURCE.contains("перше"));
    let exact_words = VIEW.trim_end_matches('\n');
    assert_eq!(
        sens::open_ternary_program(PHYSICAL).expect("канонічний фізичний T5"),
        exact_words
    );
    assert_eq!(
        sens::encode_binary_projection_ternary(exact_words).unwrap(),
        PHYSICAL
    );

    let physical_file = TemporaryPair::new(SOURCE);
    fs::write(&physical_file.physical, PHYSICAL).expect("тимчасові фізичні байти");
    let bare = Command::new(env!("CARGO_BIN_EXE_sens"))
        .arg(&physical_file.physical)
        .output()
        .expect("фізичний SENS");
    let explicit = physical_file.trit("eval");
    assert!(bare.status.success(), "physical SENS stderr={:?}", bare.stderr);
    assert!(explicit.status.success(), "physical eval stderr={:?}", explicit.stderr);
    assert_eq!(bare.stdout, explicit.stdout, "незалежні публічні CLI бачать той самий T5");
    assert!(!bare.stdout.is_empty(), "фізичне виконання має видимий результат");

    // Людська українська проєкція авторизована ТІЛЬКИ через доказану трійку.
    // Низькорівневий encode не є компілятором і не може її мовчки прийняти.
    rejected_without_physical_file(SOURCE);
}

#[test]
fn human_named_file_authority_input_never_becomes_physical_t5() {
    rejected_without_physical_file(
        "(00001001 *file-authority-input*\n  (00000001 ((schema . file-authority-input/1))))\n",
    );
}

#[test]
fn canonical_prefix_cannot_hide_a_textual_file_authority_call() {
    rejected_without_physical_file(
        "10 001 00 000 01\n(00001001 *file-authority-input* (00000001 ()))\n",
    );
}
