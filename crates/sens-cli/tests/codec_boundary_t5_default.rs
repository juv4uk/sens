//! М1 #5445 — механічна межа CLI/читача: канонічний фізичний носій — T5 (`.sens`).
//! Дослідний `.senc` (F3/F4) НЕ автовиявляється, не відкривається як програма
//! і не підміняє дефолт. Це **негативний, fail-closed свідок** межі, а не новий
//! кодек і не зміна canonical loader.
//!
//! Межа фізично лежить у `sens-trit.rs`: `read_sens` вимагає розширення
//! `.sens`, а однопараметрична форма запускається лише для шляху, що
//! закінчується `.sens` (див. `crates/sens-cli/src/bin/sens-trit.rs`).
use std::{
    fs::{self, OpenOptions},
    io::Write,
    path::PathBuf,
    process::{Command, Output},
    sync::atomic::{AtomicU64, Ordering},
};

const PHYSICAL: &[u8] = include_bytes!("../../../tests/fixtures/migration-d1-cond-cohort/branch.sens");
const VIEW: &str = include_str!("../../../tests/fixtures/migration-d1-cond-cohort/branch");

static NEXT: AtomicU64 = AtomicU64::new(0);

fn write_temp(ext: &str, bytes: &[u8]) -> PathBuf {
    let nonce = NEXT.fetch_add(1, Ordering::Relaxed);
    let path = std::env::temp_dir().join(format!(
        "sens-codec-boundary-{}-{nonce}.{ext}",
        std::process::id()
    ));
    let mut file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(&path)
        .expect("створити тимчасовий файл-свідок");
    file.write_all(bytes).expect("записати байти свідка");
    drop(file);
    path
}

fn trit(args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_sens-trit"))
        .args(args)
        .output()
        .expect("запустити справжній sens-trit")
}

struct Temp(PathBuf);
impl Drop for Temp {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.0);
    }
}

#[test]
fn canonical_t5_is_the_default_and_roundtrips_byte_for_byte() {
    // Типовий маршрут: фізичний T5 відкривається як точні binary words.
    let exact = VIEW.trim_end_matches('\n');
    assert_eq!(
        sens::open_ternary_program(PHYSICAL).expect("канонічний T5 відкривається"),
        exact
    );
    assert_eq!(
        sens::encode_binary_projection_ternary(exact).expect("канонічний T5 кодується"),
        PHYSICAL,
        "encode(open(bytes)) мусить давати ті самі байти"
    );

    let path = write_temp("sens", PHYSICAL);
    let _tmp = Temp(path.clone());
    let opened = trit(&["open", path.to_str().unwrap()]);
    assert!(opened.status.success(), "open .sens: {:?}", opened.stderr);
    assert_eq!(opened.stdout, format!("{exact}\n").as_bytes());
}

#[test]
fn senc_extension_is_never_autodetected_even_with_valid_t5_bytes() {
    // Навіть канонічні T5-байти під розширенням .senc НЕ відкриваються:
    // межа — це розширення й явний режим, а не «вгадування» за вмістом.
    let path = write_temp("senc", PHYSICAL);
    let _tmp = Temp(path.clone());
    let arg = path.to_str().unwrap();

    // Однопараметрична форма: .senc не потрапляє у гілку `ends_with(".sens")`
    // → це не open, а невідомий виклик → відмова, жодного виводу.
    let implicit = trit(&[arg]);
    assert!(!implicit.status.success(), "single-arg .senc не сміє відкриватись");
    assert!(implicit.stdout.is_empty(), "жодного позитивного доказу з .senc");
    assert!(
        String::from_utf8_lossy(&implicit.stderr).contains("usage:"),
        "очікувана відмова-підказка: {:?}",
        implicit.stderr
    );

    // Явний open .senc → відмова на межі розширення, без декодування.
    let explicit = trit(&["open", arg]);
    assert!(!explicit.status.success(), "open .senc не сміє декодувати");
    assert!(explicit.stdout.is_empty());
    assert!(
        String::from_utf8_lossy(&explicit.stderr).contains("expected a physical .sens file"),
        "очікувана іменована межа: {:?}",
        explicit.stderr
    );
}

#[test]
fn non_sens_extension_is_refused_on_open() {
    let path = write_temp("lisp", PHYSICAL);
    let _tmp = Temp(path.clone());
    let opened = trit(&["open", path.to_str().unwrap()]);
    assert!(!opened.status.success(), "open .lisp не сміє декодувати");
    assert!(opened.stdout.is_empty());
    assert!(
        String::from_utf8_lossy(&opened.stderr).contains("expected a physical .sens file"),
        "{:?}",
        opened.stderr
    );
}

#[test]
fn out_of_domain_bytes_are_refused_without_fallback() {
    // Байти >= 243 — поза фізичною областю T5. Відмова, а не мовчазний
    // T5 fallback на довільному декодуванні.
    let path = write_temp("sens", &[0xF6, 0xF6, 0xF6, 0xF6]);
    let _tmp = Temp(path.clone());
    let opened = trit(&["open", path.to_str().unwrap()]);
    assert!(!opened.status.success(), "out-of-domain мусить бути відхилено");
    assert!(opened.stdout.is_empty(), "жодного позитивного доказу поза доменом");
}

#[test]
fn unknown_subcommand_is_refused() {
    let path = write_temp("sens", PHYSICAL);
    let _tmp = Temp(path.clone());
    let bogus = trit(&["frobnicate", path.to_str().unwrap()]);
    assert!(!bogus.status.success(), "невідома команда не сміє пройти");
    assert!(bogus.stdout.is_empty());
    assert!(
        String::from_utf8_lossy(&bogus.stderr).contains("usage:"),
        "{:?}",
        bogus.stderr
    );
}
