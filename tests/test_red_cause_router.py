"""Mechanical cause routing tests only; SENS remains the semantic oracle."""
import datetime as dt
import importlib.util
import pathlib
import unittest

S = pathlib.Path(__file__).resolve().parents[1] / 'scripts/red_cause_router.py'
spec = importlib.util.spec_from_file_location('red_cause_router', S)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
NOW = dt.datetime(2026, 10, 13, 18, 0, tzinfo=dt.timezone.utc)

def t(hours):
    return (NOW - dt.timedelta(hours=hours)).isoformat()


def base(**more):
    case = dict(run_id=123, run_url='https://github.com/juv4uk/sens/actions/runs/123',
                first_seen_at=t(1), cause='AGENT_DEFECT', stamp='REGRESSION',
                owner='swarm', state='open')
    case.update(more)
    return case


class CauseRouterTests(unittest.TestCase):
    def test_two_axes_do_not_confuse(self):
        self.assertEqual([], m.validate_case(base(), NOW))
        self.assertEqual([], m.validate_case(base(cause='TEST_DEFECT'), NOW))

    def test_unclassified_is_blocking_and_escalates_after_24h(self):
        self.assertIn('UNCLASSIFIED', m.validate_case(base(cause=None), NOW))
        self.assertNotIn('ESCALATE_24H', m.validate_case(base(cause=None), NOW))
        self.assertIn('ESCALATE_24H', m.validate_case(base(cause=None, first_seen_at=t(25)), NOW))

    def test_owner_only_for_class_one_and_documented_resolution(self):
        self.assertIn('OWNER_UNCLEAR_MUST_ROUTE_TO_OWNER', m.validate_case(base(cause='OWNER_UNCLEAR'), NOW))
        own = base(cause='OWNER_UNCLEAR', owner='juv4uk', state='resolved')
        self.assertIn('MISSING_RATIFIED_RULE', m.validate_case(own, NOW))

    def test_legacy_requires_provenance(self):
        self.assertIn('MISSING_LEGACY_PROVENANCE', m.validate_case(base(cause='LEGACY_BINDING'), NOW))
        self.assertEqual([], m.validate_case(base(cause='LEGACY_BINDING', legacy_marker='SID8', provenance='#5029'), NOW))

    def test_quarantine_needs_ticket_dates_and_expiry(self):
        r = base(stamp='FLAKE')
        self.assertIn('MISSING_QUARANTINE_TICKET', m.validate_case(r, NOW))
        self.assertIn('INVALID_QUARANTINE_DATES', m.validate_case(r, NOW))
        r.update(ticket='#5029', investigation='runner flake', since=t(1), expires=t(-24))
        self.assertEqual([], m.validate_case(r, NOW))
        r['expires'] = t(2)
        self.assertIn('EXPIRED_QUARANTINE', m.validate_case(r, NOW))

    def test_only_verified_resolutions_count_autonomy(self):
        solved = base(state='resolved', resolved_by='swarm', proof_sha='a'*40,
                      proof_run_url='https://github.com/juv4uk/sens/actions/runs/124')
        unresolved = base(run_id=125, run_url='https://github.com/juv4uk/sens/actions/runs/125', state='open')
        self.assertEqual((1,1), m.audit([solved, unresolved], NOW)[1])
        solved.pop('proof_sha')
        self.assertEqual((0,0), m.audit([solved, unresolved], NOW)[1])

    def test_duplicates_fail_closed(self):
        self.assertIn((123, 'DUPLICATE_RUN'), m.audit([base(), base()], NOW)[0])

    def test_live_inventory_includes_workflows_without_jobs(self):
        old = m.api_get
        def fake(url, token):
            return {'workflow_runs': [{'id':9, 'created_at':t(2), 'html_url':'https://github.com/juv4uk/sens/actions/runs/9',
                         'path':'.github/workflows/domain-bitness-laws.yml', 'head_sha':'b'*40}]}
        try:
            m.api_get=fake
            self.assertIn(9, m.failure_inventory('juv4uk/sens','fake',NOW,48,2))
        finally:
            m.api_get=old


if __name__ == '__main__':
    unittest.main()
