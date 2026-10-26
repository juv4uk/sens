use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

#[test]
fn retired_ukrainian_staging_profile_is_not_an_active_source_authority() {
    let profile =
        fs::read_to_string(repo_root().join("lib/surface/український-профіль-джерела.lisp"))
            .expect("retired Ukrainian staging profile must remain readable as historical evidence");

    assert!(
        profile.contains("; ФАЙЛ ВИВЕДЕНО З УЖИТКУ."),
        "the obsolete staging profile must remain explicitly retired"
    );
    assert!(
        profile.contains("Не виконуваний SENS-програма. Не свідок. Не якір."),
        "a retired profile must not be treated as executable source or authority"
    );

    let release = fs::read_to_string(repo_root().join("RELEASE.md"))
        .expect("current release contract must be readable");
    assert!(
        release.contains("`name.lisp`")
            && release.contains("канонічна українська проєкція"),
        "the active release contract, not the retired staging profile, owns the canonical .lisp policy"
    );
}
