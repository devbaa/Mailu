"""Pure compatibility contract tests. Run: python3 -m unittest discover -s tests -p test_dovecot24_compat.py"""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "core/admin/mailu/internal/dovecot24_compat.py"
spec = importlib.util.spec_from_file_location("dovecot24_compat", SOURCE)
compat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compat)


class Dovecot24CompatTests(unittest.TestCase):
    def test_preserves_legacy_maildir_and_uid(self):
        result = compat.userdb_fields("user@example.org", 1048576)
        self.assertEqual(result, {
            "uid": 8,
            "gid": 8,
            "home": "/mail/user@example.org",
            "quota_storage_size": "1048576",
        })

    def test_zero_quota(self):
        self.assertEqual(compat.userdb_fields("a@b.test", 0)["quota_storage_size"], "0")

    def test_rejects_unsafe_maildir_names(self):
        for value in ["", "../mailbox", "user/../other", "a\x00b"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                compat.userdb_fields(value, 100)

    def test_rejects_negative_noninteger_and_boolean_quotas(self):
        for value in [-1, True, "100", None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                compat.userdb_fields("a@b.test", value)


if __name__ == "__main__":
    unittest.main()
