"""Zig 0.16.0 Cargo build-script environment change regression.

CI_GLUE_NO_SEMANTICS: verifies build provenance only, not SENS law.
Run: python3 -m unittest tests/test_zig_build_environment_watch.py -v
"""
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "crates/sens-cli/build.rs"
ZIG_ROOT = ROOT / "zig_transport_root.zig"

WATCHES = (
    'println!("cargo:rerun-if-env-changed=ZIG");',
    'println!("cargo:rerun-if-env-changed=PATH");',
)


def check_environment_watches(source: str) -> None:
    branch = 'if env::var_os("CARGO_FEATURE_ZIG_TRANSPORT").is_none() {'
    marker = source.find(branch)
    if marker < 0:
        raise ValueError("ZIG_CORRIDOR_BUILD_FAIL layer=build missing=feature_switch")
    for watch in WATCHES:
        if source.count(watch) != 1 or source.index(watch) >= marker:
            raise ValueError(
                f"ZIG_CORRIDOR_BUILD_FAIL layer=build missing_or_late={watch}"
            )
    # This is deliberately an external compiler, not a Rust T5 fallback.
    for required in (
        'env::var_os("ZIG")',
        'include_str!("../../.zig-version")',
        '.arg("zig_transport_root.zig")',
        'assert_eq!(actual, pinned,',
        'println!("cargo:rustc-link-lib=static=sens_zig_transport");',
    ):
        if required not in source:
            raise ValueError(
                f"ZIG_CORRIDOR_BUILD_FAIL layer=build missing={required}"
            )


def check_embedded_asset_watches(build_source: str, zig_root_source: str) -> None:
    """All Zig-root embedded bytes must invalidate the Cargo-linked archive."""
    branch = 'if env::var_os("CARGO_FEATURE_ZIG_TRANSPORT").is_none() {'
    marker = build_source.find(branch)
    if marker < 0:
        raise ValueError("ZIG_CORRIDOR_STALE_ASSET layer=build missing=feature_switch")
    # A literal source inventory, not a language registry or semantic resolver.
    assets = set(re.findall(r'@embedFile\\("([^"]+)"\\)', zig_root_source))
    if not assets:
        raise ValueError("ZIG_CORRIDOR_STALE_ASSET layer=build missing=zig_root_assets")
    setup_lines = build_source[:marker].splitlines()
    for asset in sorted(assets):
        watch = f'    println!("cargo:rerun-if-changed=../../{asset}");'
        if setup_lines.count(watch) != 1:
            raise ValueError(
                f"ZIG_CORRIDOR_STALE_ASSET layer=build file={asset} "
                "reason=missing_or_late_rebuild_watch"
            )


class ZigBuildEnvironmentWatchTest(unittest.TestCase):
    def test_pinned_zig_compiler_choice_invalidates_cargo_archive(self) -> None:
        source = BUILD.read_text(encoding="utf-8")
        check_environment_watches(source)

        # Negative controls: each lost watch must fail for the right reason.
        for lost in WATCHES:
            with self.subTest(mutation=lost):
                mutated = source.replace(lost, "", 1)
                with self.assertRaisesRegex(ValueError, "missing_or_late"):
                    check_environment_watches(mutated)

        # Moving a directive behind an early return is also forbidden.
        moved = source.replace(WATCHES[0], "", 1).replace(
            '    let root = PathBuf::from(',
            '    ' + WATCHES[0] + '\n    let root = PathBuf::from(',
            1,
        )
        with self.assertRaisesRegex(ValueError, "missing_or_late"):
            check_environment_watches(moved)

    def test_every_zig_embedded_asset_invalidates_cargo_archive(self) -> None:
        source = BUILD.read_text(encoding="utf-8")
        root = ZIG_ROOT.read_text(encoding="utf-8")
        check_embedded_asset_watches(source, root)

        # Negative control: deleting a release-manifest watch must fail closed.
        missing = source.replace(
            '    println!("cargo:rerun-if-changed=../../packaging/islands-manifest-v1.json");',
            '', 1,
        )
        with self.assertRaisesRegex(ValueError, "islands-manifest-v1.json"):
            check_embedded_asset_watches(missing, root)

        # An added Zig asset must require a new Cargo dependency; old watch
        # inventory cannot silently attest a newer Zig root module.
        newer_root = root + '\\nconst new_asset = @embedFile("packaging/new-release-asset.bin");\\n'
        with self.assertRaisesRegex(ValueError, "new-release-asset.bin"):
            check_embedded_asset_watches(source, newer_root)

        # Moving the declaration behind the feature return is not sufficient.
        watch = '    println!("cargo:rerun-if-changed=../../packaging/islands-manifest-v1.json");'
        late = source.replace(watch, '', 1).replace(
            '    let root = PathBuf::from(', watch + '\\n    let root = PathBuf::from(', 1,
        )
        with self.assertRaisesRegex(ValueError, "islands-manifest-v1.json"):
            check_embedded_asset_watches(late, root)


if __name__ == "__main__":
    unittest.main()
