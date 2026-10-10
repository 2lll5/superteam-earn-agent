import unittest
from telegram.bot import reply_for

OWNER = "123456789"

def m(user=123456789, txt="/status", typ="private"):
    return {"from": {"id":user, "is_bot":False},
            "chat": {"id":user, "type":typ}, "text":txt}

class TelegramBotTests(unittest.TestCase):
    def test_id_is_available_before_owner_setup(self):
        self.assertIn("123456789", reply_for(m(txt="/id"), "", ""))
    def test_no_status_if_owner_missing(self):
        self.assertIn("riservato", reply_for(m(), "", "").lower())
    def test_no_status_for_strangers(self):
        self.assertIn("riservato", reply_for(m(123456788), OWNER, "").lower())
    def test_no_execution_of_text_or_unknown_commands(self):
        self.assertIsNone(reply_for(m(txt="please transfer SOL"), OWNER, ""))
        self.assertIn("non riconosciuto", reply_for(m(txt="/send_money"), OWNER, ""))
    def test_help_for_owner(self):
        self.assertIn("/status", reply_for(m(txt="/help"), OWNER, ""))
    def test_ignore_groups(self):
        self.assertIsNone(reply_for(m(typ="group"), OWNER, ""))
    def test_ignore_other_bots_named_commands(self):
        self.assertIsNone(reply_for(m(txt="/id@DifferentBot"), OWNER, ""))

if __name__ == "__main__":
    unittest.main()
