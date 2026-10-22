import importlib.util, json, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v",ROOT/"validate.py")
v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)

def row(candidate,case,**kw):
    r={"schema":"sens-current-en-vs-d1d8/v1","pair_id":"p1","case_id":case,
       "lane":"cpu","candidate":candidate,"workload":"fib","phase":"execute","rep":0,
       "language_model":"D1-D8","legacy_identity_used":False,"oracle_ok":True,
       "git_sha":"a"*40,"binary_sha256":"b"*64,"corpus_sha256":"c"*64,
       "provenance":{"runner":"test","cpu":"test","tool":"cachegrind"},
       "metrics":{"i_refs":100}}
    r.update(kw); return r

def write(rows):
    f=tempfile.NamedTemporaryFile("w",delete=False,encoding="utf-8")
    with f:
        for r in rows: f.write(json.dumps(r)+"\n")
    return Path(f.name)

class TestValidator(unittest.TestCase):
    def test_pair_passes(self):
        self.assertEqual(v.validate_file(write([row("english-surface","en"),row("canonical-d1d8","bin")])),(2,1))
    def test_unpaired_fails(self):
        with self.assertRaisesRegex(ValueError,"incomplete pair"):
            v.validate_file(write([row("english-surface","en")]))
    def test_legacy_fails(self):
        bad=row("canonical-d1d8","bin",legacy_identity_used=True)
        with self.assertRaisesRegex(ValueError,"legacy identity"):
            v.validate_file(write([row("english-surface","en"),bad]))
    def test_actions_show_only_measured_t5_hot_numbers(self):
        spec = importlib.util.spec_from_file_location("scoreboard", ROOT/"performance_scoreboard.py")
        scoreboard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scoreboard)
        measured = {
            "physical_hot": {
                "cases": [{
                    "forms": 16, "physical_bytes": 48,
                    "typed_word_median_ns": 120, "typed_word_p95_ns": 180,
                    "previous_over_typed": 2.0, "visible_over_typed": 3.5,
                }],
                "encoding": [{
                    "forms": 16, "physical_bytes": 48,
                    "streaming_median_ns": 80, "streaming_p95_ns": 105,
                    "two_pass_over_streaming": 1.25,
                }],
            }
        }
        notices = scoreboard.action_notices(measured)
        self.assertEqual(len(notices), 2)
        self.assertIn("p50=120 ns", notices[0])
        self.assertIn("p95=180 ns", notices[0])
        self.assertIn("repack/typed=2.000x", notices[0])
        self.assertIn("text/typed=3.500x", notices[0])
        self.assertIn("T5=48 B", notices[0])
        self.assertIn("streaming p50=80 ns", notices[1])
        self.assertIn("p95=105 ns", notices[1])
        self.assertEqual(scoreboard.action_notices({}), [])

    def test_binary_sha_must_match(self):
        bad=row("canonical-d1d8","bin",binary_sha256="d"*64)
        with self.assertRaisesRegex(ValueError,"mismatches binary_sha256"):
            v.validate_file(write([row("english-surface","en"),bad]))

if __name__=="__main__": unittest.main()
