"""Research-only framing tests; no semantic authority."""
import importlib.util
import random
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("framed", Path(__file__).with_name("research_codec.py"))
framed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(framed)


class CodecTests(unittest.TestCase):
    def test_known_t5_and_framed_examples(self):
        for words, t5, compressed in [
            ("10 01", "64", "00"),
            ("10 001 00 000 01", "638906a1", "23d0"),
            ("10 100 00 10 111 00 1 00 0 01 01", "66386789893b35", "2109895eb5"),
        ]:
            with self.subTest(words=words):
                words = tuple(words.split())
                self.assertEqual(framed.reference_t5(words).hex(), t5)
                self.assertEqual(framed.encode(words).hex(), compressed)
                self.assertEqual(framed.decode(bytes.fromhex(compressed)), words)

    def test_capacity_and_invalid_codepoints(self):
        self.assertEqual(framed._buckets()[:3], ((1, 5, 11), (2, 12, 17), (3, 18, 22)))
        for width, lo, hi in framed._buckets():
            used = sum(framed.capacity(n) for n in range(lo, hi + 1))
            self.assertLessEqual(used, 256 ** width)
            if hi < framed.MAX_TRITS:
                self.assertGreater(used + framed.capacity(hi+1), 256 ** width)
            if used < 256 ** width:
                with self.assertRaises(framed.FrameError):
                    framed.decode(used.to_bytes(width, 'big'))

    def test_rank_roundtrips(self):
        randomizer = random.Random(20261010)
        for n in range(5, framed.MAX_TRITS + 1):
            cap = framed.capacity(n)
            if cap == 0:
                continue
            indexes = range(cap) if n <= 14 else [0, cap-1, cap//2] + [randomizer.randrange(cap) for _ in range(12)]
            for i in indexes:
                self.assertEqual(framed._rank(framed._unrank(n, i)), i)

    def test_random_balanced_nested_programs(self):
        rng = random.Random(26)
        def expr(depth):
            if depth == 0 or rng.random() < .4:
                return [''.join(str(rng.randrange(2)) for _ in range(rng.choice((1,3,4,7,9))))]
            children = [expr(depth-1) for _ in range(rng.randrange(1,4))]
            return ['10'] + [word for i, child in enumerate(children) for word in ((['00'] if i else []) + child)] + ['01']
        checked = 0
        for _ in range(2000):
            words = tuple(['10'] + expr(3) + ['01'])
            try:
                data = framed.encode(words)
            except framed.FrameError as err:
                if 'long frame' in str(err):
                    continue
                raise
            self.assertEqual(framed.decode(data), words)
            self.assertLessEqual(len(data), len(framed.reference_t5(words)))
            checked += 1
        self.assertGreater(checked, 200)

    def test_fail_closed(self):
        for words in [(), ('01',), ('10',), ('10','01','10','01'), ('10','01','00'), ('10','10','01'), ('10','0'*10,'01'), ('10','12','01')]:
            with self.assertRaises(framed.FrameError):
                framed.encode(words)
        for blob in [b'', b'\xff', b'\xff\xff', b'\xff\xff\xff']:
            with self.assertRaises(framed.FrameError):
                framed.decode(blob)


if __name__ == '__main__':
    unittest.main()
