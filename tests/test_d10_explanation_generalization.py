"""Independent finite relational model check + adversarial proof projection tests."""
import sys
import unittest
from pathlib import Path
from itertools import product
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from d10_explanation_generalization import project,Refusal

RULES=[{'id':'G', 'head':['grandparent','?x','?z'], 'body':[['parent','?x','?y'],['parent','?y','?z']]}]

class EBG(unittest.TestCase):
    def test_shared_existential(self):
        out=project(['grandparent','?A','?C'],RULES,['parent'])
        a,b=out['operational_body']
        self.assertEqual(a[2],b[1]);self.assertEqual(a[1],'?A');self.assertEqual(b[2],'?C')
        self.assertEqual(out['proof_rule_ids'],['G'])

    def test_nested(self):
        rules=[{'id':'r1','head':['secondhand','?a','?b'],'body':[['bridge','?a','?b']]},
               {'id':'r2','head':['bridge','?a','?b'],'body':[['radio','?a','?b'],['trusted','?a','?b']]}]
        out=project(['secondhand','?A','?B'],rules,['radio','trusted'])
        self.assertEqual(out['proof_rule_ids'],['r1','r2'])
        self.assertEqual(out['operational_body'],[['radio','?A','?B'],['trusted','?A','?B']])

    def test_honors_constants(self):
        x=project(['g','a'],[{'id':'r','head':['g','a'],'body':[['ok','a']]}],['ok'])
        self.assertEqual(x['operational_body'],[['ok','a']])
        with self.assertRaises(Refusal):project(['g','b'],[{'id':'r','head':['g','a'],'body':[['ok','a']]}],['ok'])

    def test_variable_identification_reject(self):
        r=[{'id':'r','head':['same','?x','?x'],'body':[['eq','?x','?x']]}]
        with self.assertRaises(Refusal):project(['same','?a','?b'],r,['eq'])
        z=project(['same','?a','?a'],r,['eq'])
        self.assertEqual(z['operational_body'],[['eq','?a','?a']])

    def test_ambiguous(self):
        with self.assertRaises(Refusal):project(['grandparent','a','b'],RULES+RULES[:1].copy(),['parent'])

    def test_recursive(self):
        with self.assertRaises(Refusal):project(['loop','?x'],[{'id':'r','head':['loop','?a'],'body':[['loop','?a']]}],['leaf'])

    def test_missing_dependency(self):
        with self.assertRaises(Refusal):project(['g','?a'],[{'id':'r','head':['g','?x'],'body':[['unknown','?x']]}],['leaf'])

    def test_malformed(self):
        bad=[([],RULES,['parent']),(['?pred','a'],RULES,['parent']),(['x','a'],[{'id':'r','head':['x','a'],'body':[]}],['parent']),(['x','a'],RULES,[]),(['x','a'],None,['parent'])]
        for args in bad:
            with self.subTest(args=args),self.assertRaises(Refusal):project(*args)

    def test_no_fake_control_or_D10_admission(self):
        d=project(['grandparent','?x','?z'],RULES,['parent'])
        self.assertEqual(d['status'],'RESEARCH-HOLD-NOT-RATIFIED')
        self.assertNotIn('coordinate',d)
        self.assertNotIn('ratified_resident',d)

    def test_exact_finite_model_soundness_and_completeness(self):
        # Independent *extensional* three-element truth-table semantics for a single Horn rule.
        names=('a','b','c');pairs=list(product(names,repeat=2))
        schema=project(['grandparent','?x','?z'],RULES,['parent'])
        antecedent=schema['operational_body']
        for bits in range(1<<len(pairs)):
            edges={pair for i,pair in enumerate(pairs) if bits>>i&1}
            relation={(x,z) for x in names for z in names if any((x,y) in edges and (y,z) in edges for y in names)}
            projected={(x,z) for x in names for z in names
                       if any(all((env[u],env[v]) in edges for _,u,v in antecedent)
                              for y in names for env in [{'?x':x,'?z':z,antecedent[0][2]:y}])}
            self.assertEqual(relation,projected, (bits,edges,relation,projected))

if __name__=='__main__':unittest.main()
