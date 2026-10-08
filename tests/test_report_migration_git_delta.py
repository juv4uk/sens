"""No inflated migration counts: compare immutable Git triples across commits."""
from __future__ import annotations
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from report_migration_git_delta import difference, snapshot, main
from sens_t5_codec import encode_words


class TrackedMigrationDeltaTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo=Path(self.tmp.name)
        self.call("init","-q", "-b","main")
        self.call("config","user.email","fixture@example.test")
        self.call("config","user.name","Migration CI")
        (self.repo/"lib").mkdir()
        (self.repo/"tests/fixtures").mkdir(parents=True)
        (self.repo/"lib/first.lisp").write_text("(як-є ())\n",encoding="utf-8")
        self.commit("source only")
        self.base=self.head()

    def call(self,*args):
        subprocess.run(["git","-C",str(self.repo),*args],check=True,
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    def commit(self,message):
        self.call("add","-A")
        self.call("commit","-q","-m",message)
    def head(self):
        return subprocess.check_output(["git","-C",str(self.repo),"rev-parse","HEAD"],text=True).strip()
    def add_triple(self,stem,source="(як-є ())\n",words=("10","001","01")):
        p=self.repo/stem
        p.parent.mkdir(parents=True,exist_ok=True)
        p.with_suffix(".lisp").write_text(source,encoding="utf-8")
        p.with_suffix(".sens").write_bytes(encode_words(list(words)))
        p.write_bytes((" ".join(words)+"\n").encode("ascii"))

    def test_one_nonfixture_first_time_and_zero_oracle_claims(self):
        self.add_triple("lib/first")
        self.commit("first real file pairing")
        out=difference(self.repo,self.base,self.head())
        self.assertEqual(out["base_census"]["lisp_count"],1)
        self.assertEqual(out["new_triples"],1)
        self.assertEqual(out["new_non_fixture_triples"],1)
        self.assertEqual(out["new_fixture_triples"],0)
        self.assertEqual(out["new_mechanically_verified"],1)
        self.assertEqual(out["head_census"]["unpaired_count"],0)
        self.assertIsNone(out["oracle_certified_original_executables"])
        self.assertIn("NOT_ATTESTED",out["new_files"][0]["semantic_oracle"])
        self.assertEqual(out["new_files"][0]["physical_bytes"],2)

    def test_fixture_does_not_claim_historical_executable_migration(self):
        self.add_triple("tests/fixtures/fixture")
        self.commit("add only a test fixture")
        out=difference(self.repo,self.base,self.head())
        self.assertEqual(out["new_fixture_triples"],1)
        self.assertEqual(out["new_non_fixture_triples"],0)

    def test_pair_without_view_is_not_valid_triple(self):
        (self.repo/"lib/first.sens").write_bytes(encode_words(["10","01"]))
        self.commit("missing canonical view")
        out=difference(self.repo,self.base,self.head())
        self.assertEqual(out["new_invalid_or_incomplete"],1)
        self.assertEqual(out["new_pairs"],1)
        self.assertEqual(out["new_triples"],0)
        self.assertEqual(out["head_census"]["paired_count"],1)
        self.assertEqual(out["head_census"]["triple_count"],0)
        self.assertEqual(main(["--root",str(self.repo),"--base",self.base,
                               "--head",self.head(),"--strict"]),2)

    def test_wrong_view_and_noncanonical_T5_fail(self):
        self.add_triple("lib/first")
        (self.repo/"lib/first").write_text("10  001 01\n",encoding="ascii")
        self.commit("noncanonical human spaces")
        out=difference(self.repo,self.base,self.head())
        self.assertEqual(out["new_invalid_or_incomplete"],1)
        (self.repo/"lib/first").write_text("10 001 01\n",encoding="ascii")
        (self.repo/"lib/first.sens").write_bytes(bytes([243]))
        self.commit("out of range packed byte")
        out=difference(self.repo,self.base,self.head())
        self.assertEqual(out["head_census"]["invalid_triples"],1)

    def test_existing_incomplete_pair_repaired_is_not_new_pair(self):
        (self.repo/"lib/first.sens").write_bytes(encode_words(["10","01"]))
        self.commit("existing physical pair but no view")
        before=self.head()
        (self.repo/"lib/first").write_bytes(b"10 01\n")
        self.commit("repair existing incomplete triple")
        out=difference(self.repo,before,self.head())
        self.assertEqual(out["new_pairs"],0)
        self.assertEqual(out["new_triples"],0)
        self.assertEqual(out["repaired_existing_triples"],["lib/first.lisp"])
        self.assertEqual(out["head_census"]["valid_triples"],1)

    def test_existing_pair_not_counted_twice_after_other_changes(self):
        self.add_triple("lib/first")
        self.commit("new pair")
        after=self.head()
        (self.repo/"note.txt").write_text("work without program migration")
        self.commit("code but no program pair")
        out=difference(self.repo,after,self.head())
        self.assertEqual(out["new_triples"],0)
        self.assertEqual(out["head_census"]["paired_count"],1)

    def test_triple_deletion_visible_and_strict_fails(self):
        self.add_triple("lib/first")
        self.commit("pair")
        before=self.head()
        (self.repo/"lib/first.sens").unlink()
        self.commit("delete packed byte file")
        out=difference(self.repo,before,self.head())
        self.assertEqual(out["removed_pairs"],["lib/first.lisp"])
        self.assertEqual(main(["--root",str(self.repo),"--base",before,
                               "--head",self.head(),"--strict"]),2)


if __name__=="__main__":
    unittest.main()
