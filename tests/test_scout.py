import unittest
from scout.__main__ import unwrap_listings, listing_summary, issue_identity, issue_body

class ScoutTests(unittest.TestCase):
    def test_nested_data(self):
        self.assertEqual(unwrap_listings({'data': {'listings': [{'id':'a'}]}}), [{'id':'a'}])

    def test_agent_only(self):
        x=listing_summary({'id': 'one','title':'Python data analytics bounty','agentAccess':'AGENT_ONLY', 'slug':'s'})
        self.assertGreaterEqual(x['score'], 4)
        self.assertEqual(x['access'], 'AGENT_ONLY')
        self.assertIn('superteam-scout-id:one', issue_identity(x))

    def test_human_only_excluded(self):
        self.assertIsNone(listing_summary({'id':'two','agentAccess':'HUMAN_ONLY','title':'Python'}))

    def test_payment_or_secrets_excluded(self):
        self.assertIsNone(listing_summary({'id':'three','title':'Python: buy tokens and enter'}))
        self.assertIsNone(listing_summary({'id':'four','title':'Python: paste your private key'}))

    def test_github_issue_does_not_claim_winning(self):
        x=listing_summary({'id':'i', 'title':'Research task', 'slug':'research', 'reward': {'amount':50, 'token':'USDC'}})
        body=issue_body(x)
        self.assertIn('NOT SUBMITTED',body)
        self.assertIn('unverified',body)

if __name__=='__main__':
    unittest.main()
