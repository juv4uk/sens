"""Ізольовані перевірки shell-інсталятора; не замінюють перевірку реальних ОС."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest


INSTALLER = Path(__file__).resolve().parents[1] / "install.sh"
VERSION = tomllib.loads((INSTALLER.parents[1] / "crates/sens-cli/Cargo.toml").read_text())["package"]["version"]


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="installer-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home with spaces"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.local_bin = self.home / ".local/bin"
        self.local_bin.mkdir(parents=True)
        local_lib = self.home / ".local/lib"
        local_lib.mkdir()
        # Готові CLIPS-файли ізолюють оновлення CLI від збирання острова.
        for name in ("libclips.so", "libclips.dylib"):
            (local_lib / name).touch()
        (self.local_bin / "clips").touch()
        self.log = self.root / "calls"
        self.log.touch()
        self.env = dict(os.environ, HOME=str(self.home), PATH=str(self.bin),
                        TEST_LOG=str(self.log), TEST_OS="Linux", TEST_ARCH="x86_64")
        # PATH не містить справжніх мережевих або пакетних менеджерів.
        for name in ("bash", "mkdir", "mktemp", "chmod", "mv", "rm", "cp", "ln", "env"):
            (self.bin / name).symlink_to(shutil.which(name))
        self.stub("uname", 'if [ "$1" = -s ]; then echo "$TEST_OS"; else echo "$TEST_ARCH"; fi')
        self.stub("id", "echo 0")
        for name in ("apt-get", "brew"):
            self.stub(name, f'echo "{name} $*" >> "$TEST_LOG"')
        self.payload = self.root / "payload"
        self.payload.write_text('#!/bin/bash\necho "new $*" >> "$TEST_LOG"\n'
                                f'if [ "$1" = --version ]; then echo "sens {VERSION}"; fi\n')
        self.env["TEST_PAYLOAD"] = str(self.payload)
        self.stub("curl", '''echo "curl $*" >> "$TEST_LOG"
while [ "$#" -gt 0 ]; do
    if [ "$1" = -o ]; then destination="$2"; shift; fi
    shift
done
if [ "${TEST_DOWNLOAD_FAIL:-0}" = 1 ]; then
    echo partial > "$destination"
    exit 22
fi
cp "$TEST_PAYLOAD" "$destination"
''')

    def stub(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/bash\nset -eu\n" + body + "\n")
        path.chmod(0o755)

    def run_installer(self):
        return subprocess.run([str(self.bin / "bash"), str(INSTALLER)],
                              env=self.env, text=True, capture_output=True, timeout=10)

    def test_platform_assets_and_exact_installed_cli(self):
        for system, arch, suffix in (("Linux", "x86_64", "linux_amd64"),
                                     ("Darwin", "arm64", "macos_arm64"),
                                     ("Darwin", "x86_64", "macos_x64")):
            with self.subTest(system=system, arch=arch):
                self.env.update(TEST_OS=system, TEST_ARCH=arch)
                self.log.write_text("")
                self.stub("sens", 'echo "old $*" >> "$TEST_LOG"')
                result = self.run_installer()
                self.assertEqual(result.returncode, 0, result.stderr)
                calls = self.log.read_text()
                self.assertIn(f"_{VERSION}_{suffix}", calls)
                self.assertIn(f"/releases/download/l{VERSION}/", calls)
                self.assertIn("new install --profile four-kernel", calls)
                self.assertNotIn("old ", calls)
                self.assertEqual((self.local_bin / "sens").read_bytes(), self.payload.read_bytes())

    def test_failed_download_preserves_old_binary(self):
        target = self.local_bin / "sens"
        target.write_text("previous binary")
        self.env["TEST_DOWNLOAD_FAIL"] = "1"
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.read_text(), "previous binary")
        self.assertEqual(list(self.local_bin.glob(".sens.*")), [])
        self.assertNotIn("new install", self.log.read_text())

    def test_unsupported_architecture_has_no_install_side_effects(self):
        for system, arch in (("Linux", "aarch64"), ("Darwin", "ppc64"),
                             ("FreeBSD", "x86_64")):
            with self.subTest(system=system, arch=arch):
                self.env.update(TEST_OS=system, TEST_ARCH=arch)
                self.log.write_text("")
                result = self.run_installer()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.log.read_text(), "")

    def test_unusable_download_preserves_old_binary(self):
        for payload in ("", "#!/bin/bash\nexit 1\n",
                        "#!/nonexistent/installer-test-interpreter\n"):
            with self.subTest(payload=payload):
                target = self.local_bin / "sens"
                target.write_text("previous binary")
                self.payload.write_text(payload)
                result = self.run_installer()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(target.read_text(), "previous binary")
                self.assertEqual(list(self.local_bin.glob(".sens.*")), [])


if __name__ == "__main__":
    unittest.main()
