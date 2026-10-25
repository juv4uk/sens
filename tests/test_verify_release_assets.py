"""Negative gates for asset completeness, integrity and provenance."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_release_assets import _expected, prepare, verify_replay

TAG = "l0.42.0"
SHA = "a" * 40


class ReleaseAssetsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dist = self.root / "dist"
        self.dist.mkdir()
        for name in _expected(TAG):
            (self.dist / name).write_bytes(b"fake test fixture for " + name.encode())
        (self.dist / "my-lisp-cli-web.html").write_bytes(
            (self.dist / "sens-cli-web.html").read_bytes()
        )

    def replay(self):
        target = self.root / "downloaded"
        shutil.copytree(self.dist, target)
        return target

    def test_complete_success(self):
        prepare(self.dist, TAG, SHA)
        self.assertEqual(verify_replay(self.dist, self.replay(), TAG, SHA), 9)

    def test_hardlinked_download_does_not_prove_independent_replay(self):
        # A second pathname to the same inode is not a downloaded artifact.
        # One shared binary or even the checksum receipt invalidates replay.
        prepare(self.dist, TAG, SHA)
        for name in ("sens-cli_0.42.0_linux_amd64", "SHA256SUMS"):
            with self.subTest(asset=name):
                downloaded = self.root / ("downloaded-hardlinked-" + name)
                shutil.copytree(self.dist, downloaded)
                (downloaded / name).unlink()
                os.link(self.dist / name, downloaded / name)
                self.assertNotEqual(self.dist.resolve(), downloaded.resolve())
                self.assertTrue((self.dist / name).samefile(downloaded / name))
                with self.assertRaisesRegex(ValueError, "not independently downloaded"):
                    verify_replay(self.dist, downloaded, TAG, SHA)

    def test_missing_msi_rejected(self):
        (self.dist / "sens-cli_0.42.0_windows_x64.msi").unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            prepare(self.dist, TAG, SHA)

    def test_extra_artifact_rejected(self):
        (self.dist / "unknown.exe").write_bytes(b"bad")
        with self.assertRaisesRegex(ValueError, "extra"):
            prepare(self.dist, TAG, SHA)

    def test_empty_artifact_rejected(self):
        (self.dist / "sens-cli-web.html").write_bytes(b"")
        with self.assertRaisesRegex(ValueError, "empty"):
            prepare(self.dist, TAG, SHA)

    def test_web_alias_missing_rejected(self):
        (self.dist / "my-lisp-cli-web.html").unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            prepare(self.dist, TAG, SHA)

    def test_web_alias_must_match_canonical_bytes(self):
        (self.dist / "my-lisp-cli-web.html").write_bytes(b"different HTML")
        with self.assertRaisesRegex(ValueError, "web compatibility alias differs"):
            prepare(self.dist, TAG, SHA)

    def test_tampered_web_alias_in_download_rejected(self):
        prepare(self.dist, TAG, SHA)
        replay = self.replay()
        (replay / "my-lisp-cli-web.html").write_bytes(b"changed after staging")
        with self.assertRaisesRegex(ValueError, "web compatibility alias differs"):
            verify_replay(self.dist, replay, TAG, SHA)

    def test_bad_downloaded_checksum_rejected(self):
        prepare(self.dist, TAG, SHA)
        replay = self.replay()
        (replay / "sens-cli_0.42.0_macos_arm64").write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "digest/size mismatch"):
            verify_replay(self.dist, replay, TAG, SHA)

    def test_tampered_both_checksums_rejected(self):
        prepare(self.dist, TAG, SHA)
        replay = self.replay()
        for root in (self.dist, replay):
            (root / "SHA256SUMS").write_text("bad\n", encoding="ascii")
        with self.assertRaisesRegex(ValueError, "SHA256SUMS mismatch"):
            verify_replay(self.dist, replay, TAG, SHA)

    def test_duplicate_provenance_key_rejected(self):
        # Root commit and nested asset digest must never select 'last key wins'.
        prepare(self.dist, TAG, SHA)
        for key, fake_value in (("commit", "b" * 40), ("sha256", "0" * 64)):
            with self.subTest(key=key):
                replay = self.root / f"downloaded-{key}"
                shutil.copytree(self.dist, replay)
                provenance = replay / "release-provenance.json"
                data = provenance.read_text(encoding="utf-8")
                needle = f'"{key}":'
                self.assertIn(needle, data)
                data = data.replace(
                    needle,
                    f'"{key}": "{fake_value}",\n    "{key}":',
                    1,
                )
                provenance.write_text(data, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "duplicate provenance JSON key"):
                    verify_replay(self.dist, replay, TAG, SHA)

    def test_wrong_candidate_sha_rejected(self):
        prepare(self.dist, TAG, SHA)
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            verify_replay(self.dist, self.replay(), TAG, "b" * 40)

    def test_wrong_tag_rejected(self):
        # Asset staging must use the same canonical tag grammar as tag admission.
        for tag in ("main", "l00.42.0", "l0.042.0", "l0.42.00", "l0.42", "l0.42.0-rc1"):
            with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, "malformed release tag"):
                prepare(self.dist, tag, SHA)

    def test_symlink_rejected(self):
        target = self.dist / "sens-cli-web.html"
        target.unlink()
        target.symlink_to(self.dist / "install.sh")
        with self.assertRaisesRegex(ValueError, "invalid"):
            prepare(self.dist, TAG, SHA)


class ReleaseWorkflowOrderingTest(unittest.TestCase):
    """Keep current release entry points and published artifact flow covered."""

    def test_web_bundle_source_and_generated_wasm_names(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        bundler = (root / "scripts" / "make-portable-web.mjs").read_text(encoding="utf-8")
        self.assertTrue((root / "public" / "my-lisp-cli-web.html").is_file())
        self.assertIn(
            "--out-dir ../../public/wasm --release",
            workflow,
            "WASM bindings must be written where the standalone bundler reads them",
        )
        self.assertIn(
            "node scripts/make-portable-web.mjs public/my-lisp-cli-web.html sens-cli-web.html",
            workflow,
            "release must use the checked-in standalone HTML bundler",
        )
        self.assertIn("cp sens-cli-web.html my-lisp-cli-web.html", workflow)
        self.assertIn("cmp -s sens-cli-web.html my-lisp-cli-web.html", workflow)
        self.assertIn("            sens-cli-web.html\n            my-lisp-cli-web.html", workflow)
        self.assertIn("wasm/sens_wasm_bg.wasm", bundler)
        self.assertIn("wasm/sens_wasm.js", bundler)
        self.assertNotIn("wasm/my_lisp_wasm_bg.wasm", bundler)
        self.assertNotIn("wasm/my_lisp_wasm.js", bundler)

    def test_main_sha_and_owner_go_are_rechecked_after_replay_before_publish(self):
        root = Path(__file__).resolve().parents[1]
        entry = (root / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        publisher = (root / ".github" / "workflows" / "release-publish.yml").read_text(
            encoding="utf-8"
        )
        delegated = entry[entry.index("  release-publish:"):]
        self.assertIn(
            "needs: [test, publish-island-manifest, build-cli, build-msi, build-web]",
            delegated,
        )
        self.assertIn("uses: ./.github/workflows/release-publish.yml", delegated)

        replay = publisher.rfind("python3 scripts/verify_release_assets.py replay")
        publish = publisher.rfind('gh release edit "$GITHUB_REF_NAME" --draft=false')
        last_fetch = publisher.rfind("git fetch --no-tags --depth=1 origin main")
        last_compare = publisher.rfind('test "$(git rev-parse FETCH_HEAD)" = "$GITHUB_SHA"')

        self.assertGreaterEqual(replay, 0, "draft replay verifier is required")
        self.assertGreater(last_fetch, replay, "main must be refetched after byte replay")
        self.assertGreater(last_compare, last_fetch, "fresh main ref must be compared to tagged SHA")
        self.assertGreater(publish, last_compare, "nothing may publish before the final SHA guard")
        final_guard = publisher[last_fetch:publish]
        self.assertIn("RELEASE_GO_SHA", final_guard)
        self.assertIn("RELEASE_GO_TAG", final_guard)
        self.assertIn("RELEASE_BLOCKED", final_guard)

class TaggedReleaseWorkflowWiringTests(unittest.TestCase):
    """Guard the actual tag workflow's connection to the canonical release verifier."""

    def test_tagged_workflow_invokes_optimization_safe_verifier_before_installer(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        label = "      - name: Перевірити версію тегу та інсталятор"
        self.assertIn(label, workflow, "RELEASE_BLOCKED: tag/version step missing")
        block = workflow.split(label, 1)[1].split("\n      - name:", 1)[0]
        guard = 'python3 scripts/verify_release_tag.py "$RELEASE_TAG"'
        self.assertIn('RELEASE_TAG: ${{ github.ref_name }}', block)
        self.assertIn("set -euo pipefail", block)
        self.assertIn(guard, block, "RELEASE_BLOCKED: canonical tag verifier absent")
        installer = "python3 -m unittest discover -s packaging/tests -v"
        self.assertIn(installer, block)
        self.assertLess(block.index(guard), block.index(installer),
                        "RELEASE_BLOCKED: tag verification must precede installer checks")

class ReleaseVersionParityTest(unittest.TestCase):
    """One exact release version across crates, Cargo.lock, Guix and installer tooling."""

    def test_all_active_release_surfaces_match_cli_package(self):
        import re
        import tomllib

        root = Path(__file__).resolve().parents[1]
        manifest_paths = [
            "crates/sens/Cargo.toml",
            "crates/sens-cli/Cargo.toml",
            "crates/sens-host/Cargo.toml",
            "crates/sens-lsp/Cargo.toml",
            "crates/sens-wasm/Cargo.toml",
            "crates/sens-literate/Cargo.toml",
            "crates/sens-semantic/Cargo.toml",
        ]
        cli_package = tomllib.loads(
            (root / "crates/sens-cli/Cargo.toml").read_text(encoding="utf-8")
        )["package"]
        version = cli_package["version"]
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")

        for relative in manifest_paths:
            with self.subTest(manifest=relative):
                package = tomllib.loads(
                    (root / relative).read_text(encoding="utf-8")
                )["package"]
                self.assertEqual(package["version"], version, relative)

        locked = tomllib.loads((root / "Cargo.lock").read_text(encoding="utf-8"))
        canonical_names = {
            "sens", "sens-cli", "sens-host", "sens-lsp",
            "sens-wasm", "sens-literate", "sens-semantic",
        }
        locked_versions = {
            package["name"]: package["version"]
            for package in locked["package"]
            if package["name"] in canonical_names
        }
        self.assertEqual(set(locked_versions), canonical_names)
        self.assertEqual(
            locked_versions,
            {name: version for name in canonical_names},
            "root Cargo.lock canonical release package versions differ",
        )

        guix = (root / "guix.scm").read_text(encoding="utf-8")
        guix_version = re.search(r'\(version\s+"([^"]+)"\)', guix)
        self.assertIsNotNone(guix_version, "Guix package version is missing")
        self.assertEqual(guix_version.group(1), version)

        installer = (root / "packaging" / "install.sh").read_text(encoding="utf-8")
        for suffix in ("linux_amd64", "macos_arm64", "macos_x64"):
            with self.subTest(asset=suffix):
                self.assertIn(f"sens-cli_{version}_{suffix}", installer)
        self.assertIn(f"releases/download/l{version}/", installer)

        release_script = (root / "scripts" / "release.lisp").read_text(encoding="utf-8")
        self.assertIn("ФАЙЛ ВИВЕДЕНО З УЖИТКУ", release_script)
        self.assertIn(f"Потрібна версія релізу: {version}.", release_script)
        self.assertNotIn("gh release", release_script)

class ReleaseWebDemoLinkTests(unittest.TestCase):
    """CI_GLUE_NO_SEMANTICS: stable README link across asset renames."""

    def test_readme_latest_page_survives_web_asset_rename(self):
        import re

        root = Path(__file__).resolve().parents[1]
        readme = (root / "README.md").read_text(encoding="utf-8")
        stable = "https://github.com/juv4uk/sens/releases/latest"
        stale = stable + "/download/my-lisp-cli-web.html"

        def verify_link(content):
            match = re.search(
                r'<a href="([^"]+)"><strong>▶ Завантажити вебдемо SENS</strong></a>',
                content,
            )
            self.assertIsNotNone(match, "RELEASE_BLOCKED: web-demo CTA missing")
            self.assertEqual(
                match.group(1), stable,
                "RELEASE_BLOCKED: demo must link to the stable release page",
            )

        verify_link(readme)
        mutated = readme.replace(f'href="{stable}"', f'href="{stale}"', 1)
        self.assertNotEqual(mutated, readme)
        with self.assertRaises(AssertionError):
            verify_link(mutated)


if __name__ == "__main__":
    unittest.main()
