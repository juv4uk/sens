            self.assertEqual(state["summary"]["files_blocked"], 1)
            self.assertIn("ambiguous W8", state["files"][0]["reason"])



    def test_global_text7_call_head_uses_same_frame_as_define_target(self):
        source="""\\
(00001001 foo
  (00001000 ()
    1))
(foo)
"""
        projection,resolver=self.migrate(source)
        frame=mod.frame_text7(
            mod.text7_encode("foo",self.text7,mod.Tok("ATOM","foo",0)),
            mod.Tok("ATOM","foo",0),
        )
        frame_text=" ".join(frame)
        self.assertGreaterEqual(projection.count(frame_text),2)
        self.assertEqual(resolver.counts["pass4-text7-global"],1)
        self.assertIn(frame_text, projection)
        self.assertIn("tak", projection)
        self.assertNotIn("foo", projection)


    def test_real_machine_block_closes_all_global_and_local_symbolic_words(self):
        source=(ROOT/"lib"/"machine"/"block.lisp").read_text(encoding="utf-8")
        projection,resolver=self.migrate(source)
        words=projection.split()
        self.assertTrue(words)
        self.assertGreaterEqual(
            resolver.counts["pass1-sens8"],
            17,
            "all 17 historical callable heads must be recognized even when additional exact W8 evidence is present",
        )

        for name in (
            "machine-block",
            "machine-block-empty",
            "machine-block-one",
            "machine-block-append",
            "machine-block-concat",
            "machine-block-forms",
        ):
            frame=mod.frame_text7(
                mod.text7_encode(name,self.text7,mod.Tok("ATOM",name,0)),
                mod.Tok("ATOM",name,0),
            )
            self.assertIn(
                " ".join(frame),
                projection,
                f"missing canonical global Text7 frame for {name}",
            )

        forms_frame=mod.frame_text7(
            mod.text7_encode("forms",self.text7,mod.Tok("ATOM","forms",0)),
            mod.Tok("ATOM","forms",0),
        )
        self.assertGreaterEqual(
            projection.count(" ".join(forms_frame)),
            2,
            "lambda binder and local reference must share one Text7 binding frame",
        )

        payload=mod.encode_projection(projection)
        self.assertEqual(mod.decode_bytes(payload),words)
        self.assertTrue(payload, "physical T5 candidate must contain bytes")


    def test_let_and_let_star_bindings_use_contextual_text7_without_treating_binding_lists_as_calls(self):
        for source, head, expected_env in (
            ("(let ((x 1)) x)\n", "001000", 1),
            ("(let* ((x 1) (y x)) y)\n", "001001", 1),
        ):
            projection, resolver = self.migrate(source)
            words = projection.split()
            self.assertIn(head, words)
            x_frame = " ".join(
                mod.frame_text7(
                    mod.text7_encode("x", self.text7, mod.Tok("ATOM", "x", 0)),
                    mod.Tok("ATOM", "x", 0),
                )
            )
            self.assertIn(x_frame, projection)
            self.assertEqual(resolver.counts["pass2-my-lisp"], expected_env)
            self.assertNotIn(" x ", " " + projection + " ")

    def test_machine_block_local_callable_shadows_builtin_surface(self):
        source="""\\
(00001001 first
  (00001000 (first)
    (first)))
"""
        projection,resolver=self.migrate(source)
        words=projection.split()
        first_frame=mod.frame_text7(
            mod.text7_encode("first",self.text7,mod.Tok("ATOM","first",0)),
            mod.Tok("ATOM","first",0),
        )
        self.assertGreaterEqual(projection.count(" ".join(first_frame)),2)


if __name__=="__main__":
    unittest.main()