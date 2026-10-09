#!/usr/bin/env python3
"""Conservative regression tests for exact-D1 legacy COND carrier audit."""
import unittest
from check_d1_cond_carriers import audit, lex, read_forms


class AuditTests(unittest.TestCase):
    def test_definite_bad_carriers(self):
        for expected in ('0', '1', '(0)', '(1)', '()', 't'):
            with self.subTest(expected=expected):
                code = f'(00000111 ((00100010 a b) {expected} pass))'
                findings = audit(code, 'x.lisp')
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0]['severity'], 'error')

    def test_exact_two_part_predicate_allowed(self):
        self.assertEqual(audit('(00000111 ((00100010 a b) pass))', 'x'), [])

    def test_typed_expected_expression_allowed(self):
        code = '(00000111 ((00100010 a b) (00100010 c d) pass))'
        self.assertEqual(audit(code, 'x'), [])

    def test_historical_eq_is_not_misclassified(self):
        self.assertEqual(audit('(00000111 ((00000011 a b) (1) pass))', 'x'), [])

    def test_nested_works_and_preserves_line(self):
        code = '(foo ; comment with ( bogus )\n (00000111\n   ((00100010 a b) (1) pass)))'
        findings = audit(code, 'fixture.lisp')
        self.assertEqual([(f['line'], f['kind']) for f in findings], [(3, 'EQUAL_EXPECTED_SINGLETON_LIST')])

    def test_strings_do_not_create_forms(self):
        self.assertEqual(audit('(quote "((00100010 a b) (1) yes)")', 'x'), [])

    def test_not_of_equal_is_review_not_proven_error(self):
        code = '(00000111 (((00100001 (00100010 a b))) pass))'
        self.assertEqual(audit(code, 'x'), [])  # nested list is not a direct NOT query
        code = '(00000111 ((00100001 (00100010 a b)) pass))'
        f = audit(code, 'x')
        self.assertEqual(f[0]['severity'], 'review')

    def test_comment_and_utf8(self):
        self.assertEqual(audit('; ((00100010 a b) (1) pass)\n(00001001 українська "()")', 'x'), [])

    def test_char_literals_and_nested_block_comments(self):
        sample = '#| (00000111 ((00100010 a b) 1 bad)) #| nested |# |#\n' \
                 '(list #\\( #\\; #\\) (00000111 ((00100010 a b) (1) fail)))'
        findings = audit(sample, 'char.lisp')
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['line'], 2)

    def test_invalid_input_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unclosed list'):
            read_forms('(00000111')
        with self.assertRaisesRegex(ValueError, 'unterminated string'):
            lex('(quote "unfinished)')


if __name__ == '__main__':
    unittest.main()
