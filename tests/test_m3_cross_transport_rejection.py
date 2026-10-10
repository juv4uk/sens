#!/usr/bin/env python3
"""М3 #5447: незалежна перевірка відмови T5 на чужих транспортних даних.

Це свідок МЕЖІ форматів, а не новий T5/F3/F4-кодек і не підміна
незалежного D2/Rust-оракула #5439. Фікстури походять з відкритого
коду CMLJ UART, GPU CSV та текстового GraalVM reader; вони НЕ програми SENS.
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "sens_t5_codec.py"


def load_t5():
    if not SOURCE.is_file():
        raise RuntimeError("BLOCKED: відсутній канонічний T5-кодек")
    spec = importlib.util.spec_from_file_location("sens_t5_codec_m3", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("BLOCKED: неможливо завантажити T5-кодек")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


T5 = load_t5()


class CrossTransportMustNotBeT5(unittest.TestCase):
    def test_frozen_t5_control_preserves_width_and_byte(self):
        # 00122 (base-3) = 17 (0x11). Розрізняємо D3:001 від D1:1.
        self.assertEqual(T5.decode_bytes(bytes.fromhex("11")), ["001"])
        self.assertEqual(T5.encode_words(["001"]), bytes.fromhex("11"))

    def test_fpga_cmlj_request_is_not_t5(self):
        # fpga-lisp/job_transport.py: заголовок UART завдання.
        with self.assertRaises(T5.SensT5Error):
            T5.decode_bytes(b"CMLJ")

    def test_gpu_csv_payload_is_not_t5(self):
        # sens-futhark/host/import_sens_fixture.py: зовнішній CSV контракт.
        with self.assertRaises(T5.SensT5Error):
            T5.decode_bytes(b"domain,width,bits,exact_text\n")

    def test_graalvm_textual_binary_declaration_is_not_t5(self):
        # wsm-graalvm/Reader.java: текстова, НЕ фізична декларація.
        with self.assertRaises(T5.SensT5Error):
            T5.decode_bytes(b"(binary 8)")

    def test_experimental_markers_are_not_t5_bytes(self):
        # F3/F4 належать лише явно вибраному дослідному .senc.
        for marker in (0xF3, 0xF4):
            with self.subTest(marker=marker):
                with self.assertRaises(T5.SensT5Error):
                    T5.decode_bytes(bytes([marker]))

    def test_noncanonical_all_twos_is_not_an_empty_program(self):
        # F2 = п'ять тритів 2, а не дозвіл на нульову/порожню програму.
        with self.assertRaises(T5.SensT5Error):
            T5.decode_bytes(bytes([0xF2]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
