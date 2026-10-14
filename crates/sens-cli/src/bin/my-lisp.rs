// Compatibility binary with its own Cargo target path. Keep the historical
// "my-lisp" executable and the canonical "sens" CLI byte-for-byte identical
// without pointing two [[bin]] targets at the same source file.
// The actual CLI implementation and SENS law remain in src/main.rs.
include!("../main.rs");
