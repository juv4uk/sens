use sens::installed_capabilities;
use sens_host::install;

#[test]
fn portable_transport_substrate_exposes_raw_mechanisms_not_public_semantics() {
    install();
    let installed = installed_capabilities();

    for required in [
        "process-run-raw",
        "read-file-bytes",
        "write-file-bytes",
        "tcp-connect",
        "tcp-listen-raw",
        "tcp-accept",
        "tcp-read-raw",
        "tcp-write-raw",
        "tcp-close",
    ] {
        assert!(
            installed.iter().any(|name| name == required),
            "portable mechanism missing from host substrate: {required}"
        );
    }

    for language_owned in ["process-run", "tcp-listen", "tcp-read", "tcp-write"] {
        assert!(
            !installed.iter().any(|name| name == language_owned),
            "derived public semantics leaked back into host substrate: {language_owned}"
        );
    }
}
