"""Targeted release witness: offline SENS HTML requires embedded wasm-bindgen JS."""

import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "make-portable-web.mjs"


class PortableWebFailClosedTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.public = self.root / "public"
        self.wasm = self.public / "wasm"
        self.wasm.mkdir(parents=True)
        self.wasm.joinpath("sens_wasm_bg.wasm").write_bytes(b"\0asm\x01\0\0\0")
        self.src = self.public / "demo.html"
        self.src.write_text(
            '<!doctype html><script src="./wasm-loader.js"></script>',
            encoding="utf-8",
        )
        self.out = self.root / "standalone.html"

    def bundle(self):
        return subprocess.run(
            ["node", str(SCRIPT), str(self.src), str(self.out)],
            capture_output=True, text=True, timeout=15, check=False,
        )

    def test_missing_js_blocks_without_partial_output(self):
        result = self.bundle()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sens_wasm.js", result.stderr)
        self.assertFalse(self.out.exists())

    def test_empty_js_blocks_without_partial_output(self):
        self.wasm.joinpath("sens_wasm.js").write_text("  ", encoding="utf-8")
        result = self.bundle()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RELEASE_BLOCKED", result.stderr)
        self.assertFalse(self.out.exists())

    def test_complete_local_wasm_js_produces_embedded_html(self):
        marker = "SENS_WASM_EMBED_WITNESS"
        self.wasm.joinpath("sens_wasm.js").write_text(
            'export default function init(){ return "' + marker + '"; }',
            encoding="utf-8",
        )
        result = self.bundle()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = self.out.read_text(encoding="utf-8")
        self.assertIn(marker, data)
        self.assertIn("embeddedWasmBytes", data)
        self.assertIn("embeddedWasmJs", data)
        self.assertNotIn("/wasm/my_lisp_wasm.js", data)
        self.assertNotIn("<script src=", data)

    def test_unresolved_local_script_blocks(self):
        self.wasm.joinpath("sens_wasm.js").write_text(
            "export default function init(){}", encoding="utf-8",
        )
        self.src.write_text('<script src="./missing.js"></script>', encoding="utf-8")
        result = self.bundle()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
