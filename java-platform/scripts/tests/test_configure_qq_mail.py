import contextlib
import importlib.util
import io
from pathlib import Path
import smtplib
import tempfile
import unittest
from unittest.mock import patch

source = Path(__file__).resolve().parents[1] / "configure-qq-mail.py"
spec = importlib.util.spec_from_file_location("qq_mail", source)
qq_mail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qq_mail)


class QqMailSetupTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_prepare_keeps_existing_credentials(self):
        settings = qq_mail.prepare(self.root)
        settings.write_text("SMTP_USER=sample@qq.com\nSMTP_PASSWORD=abcdefghijklmnop\n")
        qq_mail.prepare(self.root)
        self.assertEqual(qq_mail.credentials(settings), ("sample@qq.com", "abcdefghijklmnop"))

    def test_empty_or_duplicate_settings_are_rejected(self):
        settings = qq_mail.prepare(self.root)
        with self.assertRaises(ValueError):
            qq_mail.credentials(settings)
        settings.write_text("SMTP_USER=sample@qq.com\nSMTP_PASSWORD=abcdefghijklmnop\nSMTP_USER=other@qq.com\n")
        with self.assertRaises(ValueError):
            qq_mail.credentials(settings)

    def test_update_preserves_database_secrets_and_original_backup(self):
        target = self.root / ".env"
        original = b"# Keep this comment\nDB_PASSWORD=original-secret\nJWT_SECRET=jwt-secret\nSMTP_HOST=mailpit\nSMTP_PORT=1025\nSMTP_PORT=1026\n"
        target.write_bytes(original)
        qq_mail.apply(self.root, "sample@qq.com", "abcdefghijklmnop")
        content = target.read_text()
        self.assertIn("DB_PASSWORD=original-secret\n", content)
        self.assertIn("JWT_SECRET=jwt-secret\n", content)
        self.assertIn("# Keep this comment\n", content)
        self.assertEqual(content.count("SMTP_PORT="), 1)
        self.assertIn("SMTP_SSL=true\n", content)
        self.assertIn("MAIL_FROM=sample@qq.com\n", content)
        qq_mail.apply(self.root, "sample@qq.com", "ponmlkjihgfedcba")
        self.assertEqual((self.root / ".runtime/qq-mail.previous.env").read_bytes(), original)

    def test_rejected_authentication_keeps_active_settings_and_hides_secret(self):
        original = b"DB_PASSWORD=preserve\nSMTP_HOST=mailpit\n"
        (self.root / ".env").write_bytes(original)
        settings = qq_mail.prepare(self.root)
        secret = "abcdefghijklmnop"
        settings.write_text("SMTP_USER=sample@qq.com\nSMTP_PASSWORD=" + secret + "\n")
        error = io.StringIO()
        with patch.object(qq_mail, "ROOT", self.root), patch("sys.argv", [str(source)]), patch.object(qq_mail, "verify", side_effect=smtplib.SMTPAuthenticationError(535, b"Rejected")), contextlib.redirect_stderr(error):
            with self.assertRaises(SystemExit) as result:
                qq_mail.main()
        self.assertEqual(result.exception.code, 2)
        self.assertEqual((self.root / ".env").read_bytes(), original)
        self.assertNotIn(secret, error.getvalue())


if __name__ == "__main__":
    unittest.main()
