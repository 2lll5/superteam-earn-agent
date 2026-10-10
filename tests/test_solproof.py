import unittest
from solproof.__main__ import evaluate, decode58, ProofError, validate_address

DEST = "11111111111111111111111111111111"
OTHER = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
ACCOUNT = "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"


def sol_tx(net=500000000, sent=500000000, err=None):
    return {"slot": 12, "meta": {"err": err,
             "preBalances": [1000000000, 10], "postBalances": [1000000000 + net, 10]},
            "transaction": {"message": {"accountKeys": [DEST, OTHER],
                "instructions": [{"program": "system", "parsed": {"type": "transfer",
                    "info": {"destination": DEST, "source": OTHER, "lamports": sent}}}]}}}


def spl_tx(net=20000000, kind="transferChecked", owner=DEST):
    return {"slot": 13, "meta": {"err": None, "preBalances": [1, 1, 1],
        "postBalances": [1, 1, 1],
        "preTokenBalances": [{"accountIndex": 2, "owner": DEST, "mint": MINT,
                              "uiTokenAmount": {"amount": "2000000", "decimals": 6}}],
        "postTokenBalances": [{"accountIndex": 2, "owner": owner, "mint": MINT,
                              "uiTokenAmount": {"amount": str(2000000 + net), "decimals": 6}}],
        "innerInstructions": [{"instructions": [{"program": "spl-token",
                              "parsed": {"type": kind, "info": {
                              "destination": ACCOUNT, "mint": MINT,
                              "tokenAmount": {"amount": "20000000", "decimals": 6}}}}]}]},
        "transaction": {"message": {"accountKeys": [OTHER, DEST, ACCOUNT],
                                  "instructions": []}}}


class Tests(unittest.TestCase):
    def test_address(self):
        validate_address(DEST)
        self.assertEqual(len(decode58(DEST)), 32)
        with self.assertRaises(ProofError):
            validate_address("not0base58")

    def test_native_transfer(self):
        x = evaluate(sol_tx(), "test", DEST)
        self.assertTrue(x["verified"])
        self.assertEqual(x["amount"], "0.5")
        self.assertEqual(evaluate(sol_tx(net=100000000), "test", DEST)["amount"], "0.1")
        self.assertFalse(evaluate(sol_tx(net=0), "test", DEST)["verified"])
        self.assertFalse(evaluate(sol_tx(err={"x":"failed"}), "test", DEST)["verified"])
        self.assertFalse(evaluate(None, "test", DEST)["verified"])
        self.assertFalse(evaluate(sol_tx(), "test", OTHER)["verified"])

    def test_spl_transfer_and_rejection(self):
        x = evaluate(spl_tx(), "test", DEST, MINT)
        self.assertTrue(x["verified"])
        self.assertEqual(x["amount"], "20")
        self.assertFalse(evaluate(spl_tx(net=0), "test", DEST, MINT)["verified"])
        self.assertFalse(evaluate(spl_tx(kind="transfer"), "test", DEST, MINT)["verified"])
        self.assertFalse(evaluate(spl_tx(owner=OTHER), "test", DEST, MINT)["verified"])

    def test_unparsed_no_approval(self):
        tx = sol_tx()
        tx["transaction"]["message"]["instructions"] = [{"programId": DEST}]
        self.assertFalse(evaluate(tx, "test", DEST)["verified"])


if __name__ == "__main__":
    unittest.main()
