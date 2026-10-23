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
from sens_t5_t5m_codec import encode_words


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

    def test_symlink_or_gitlink_cannot_inflate_migration_triples(self):
        self.add_triple("lib/first")
        self.commit("ordinary regular-file triple")
        self.assertEqual(snapshot(self.repo, self.head())["valid_triples"], 1)

        # Git index staging works without OS-level symlink privileges, so this
        # test covers the historical Git blobs on all host platforms.
        for member in ("lib/first.lisp", "lib/first.sens", "lib/first"):
            target_blob = subprocess.run(
                ["git", "-C", str(self.repo), "hash-object", "-w", "--stdin"],
                input=b"archived-target-path", stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=True,
            ).stdout.decode("ascii").strip()
            self.call("update-index", "--add", "--cacheinfo",
                      f"120000,{target_blob},{member}")
            self.call("commit", "-q", "-m", "staged historical symlink")
            rows = snapshot(self.repo, self.head())
            self.assertEqual(rows["valid_triples"], 0, member)
            self.assertEqual(rows["invalid_triples"], 1, member)
            self.assertIn("not a regular Git file", rows["rows"][0]["reason"])
            self.assertEqual(main(["--root", str(self.repo), "--base",
                                   self.base, "--head", self.head(),
                                   "--strict"]), 2)
            self.call("add", "--", member)
            self.call("commit", "-q", "-m", "restore regular Git blob")
            self.assertEqual(snapshot(self.repo, self.head())["valid_triples"], 1)

        # A submodule/gitlink is not a .sens byte blob either.
        self.call("update-index", "--add", "--cacheinfo",
                  f"160000,{self.head()},lib/first.sens")
        self.call("commit", "-q", "-m", "staged gitlink instead of T5 bytes")
        rows = snapshot(self.repo, self.head())
        self.assertEqual(rows["valid_triples"], 0)
        self.assertEqual(rows["invalid_triples"], 1)
        self.assertIn("160000", rows["rows"][0]["reason"])

    def test_unpaired_nonregular_lisp_is_not_a_migration_source(self):
        # Git commit history may contain symlink/gitlink paths ending in
        # .lisp; their blobs are not executable Lisp source text.
        target_blob = subprocess.run(
            ["git", "-C", str(self.repo), "hash-object", "-w", "--stdin"],
            input=b"archived-source-path", capture_output=True, check=True,
        ).stdout.decode("ascii").strip()
        self.call("update-index", "--add", "--cacheinfo",
                  f"120000,{target_blob},lib/ghost.lisp")
        self.call("commit", "-q", "-m", "archival .lisp symlink")
        result = snapshot(self.repo, self.head())
        self.assertEqual(result["lisp_count"], 1)
        self.assertEqual(result["unpaired_count"], 1)
        self.assertEqual(result["nonregular_lisp_count"], 1)
        self.assertEqual(result["nonregular_lisp_paths"], ["lib/ghost.lisp"])
        self.assertEqual(result["invalid_triples"], 0)
        self.assertEqual(main(["--root", str(self.repo), "--base",
                               self.base, "--head", self.head(),
                               "--strict"]), 0)

        self.call("update-index", "--add", "--cacheinfo",
                  f"160000,{self.head()},lib/foreign.lisp")
        self.call("commit", "-q", "-m", "archival .lisp gitlink")
        result = snapshot(self.repo, self.head())
        self.assertEqual(result["lisp_count"], 1)
        self.assertEqual(result["unpaired_count"], 1)
        self.assertEqual(result["nonregular_lisp_count"], 2)
        self.assertEqual(result["nonregular_lisp_paths"],
                         ["lib/foreign.lisp", "lib/ghost.lisp"])

        # A falsely paired non-regular source remains an invalid row; it
        # must never acquire an apparently credible source_sha256 receipt.
        (self.repo / "lib/ghost.sens").write_bytes(encode_words(["10", "01"]))
        (self.repo / "lib/ghost").write_bytes(b"10 01\n")
        self.call("add", "--", "lib/ghost.sens", "lib/ghost")
        self.call("commit", "-q", "-m", "attempt to pair archived symlink")
        result = snapshot(self.repo, self.head())
        self.assertEqual(result["paired_count"], 1)
        self.assertEqual(result["valid_triples"], 0)
        self.assertEqual(result["invalid_triples"], 1)
        self.assertEqual(result["unpaired_count"], 1)
        self.assertNotIn("source_sha256", result["rows"][0])
        self.assertIn("mode=120000", result["rows"][0]["reason"])
        self.assertEqual(main(["--root", str(self.repo), "--base",
                               self.base, "--head", self.head(),
                               "--strict"]), 2)

    def test_nonregular_sens_is_not_counted_as_physical_corpus(self):
        # Git 120000/160000 позначає посилання, а не фізичні байти T5.
        blob = subprocess.run(
            ["git", "-C", str(self.repo), "hash-object", "-w", "--stdin"],
            input=b"archived-physical-target", capture_output=True, check=True,
        ).stdout.decode("ascii").strip()
        self.call("update-index", "--add", "--cacheinfo",
                  f"120000,{blob},lib/archived.sens")
        self.call("commit", "-q", "-m", "index-only .sens symlink")
        census = snapshot(self.repo, self.head())
        self.assertEqual(census["sens_count"], 0)
        self.assertEqual(census["nonregular_sens_count"], 1)
        self.assertEqual(census["nonregular_sens_paths"], ["lib/archived.sens"])
        self.assertEqual(census["valid_triples"], 0)

        # Git-посилання на коміт також не є фізичним файлом .sens.
        self.call("update-index", "--add", "--cacheinfo",
                  f"160000,{self.head()},lib/vendor.sens")
        self.call("commit", "-q", "-m", "index-only .sens gitlink")
        census = snapshot(self.repo, self.head())
        self.assertEqual(census["sens_count"], 0)
        self.assertEqual(census["nonregular_sens_count"], 2)
        self.assertEqual(census["nonregular_sens_paths"],
                         ["lib/archived.sens", "lib/vendor.sens"])

        # Справжній байтовий Git-файл рахуємо рівно один раз.
        # Самотній файл або архівне посилання не доводять повну тріаду.
        (self.repo / "lib/payload.sens").write_bytes(encode_words(["10", "01"]))
        self.call("add", "--", "lib/payload.sens")
        self.call("commit", "-q", "-m", "regular orphan physical T5")
        census = snapshot(self.repo, self.head())
        self.assertEqual(census["sens_count"], 1)
        self.assertEqual(census["nonregular_sens_count"], 2)
        self.assertEqual(census["valid_triples"], 0)
        self.assertEqual(census["paired_count"], 0)
        self.assertEqual(main(["--root", str(self.repo), "--base",
                               self.base, "--head", self.head(),
                               "--strict"]), 0)

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
