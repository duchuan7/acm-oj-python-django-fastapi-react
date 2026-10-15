"""Prepare QQ SMTP credentials locally, verify authentication, then update .env.

Uses Python's standard library. Never prints credentials or sends a message.
"""

import argparse
import os
from pathlib import Path
import re
import smtplib
import ssl
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = "# Fill locally. SMTP_PASSWORD is the QQ SMTP authorization code.\nSMTP_USER=\nSMTP_PASSWORD=\n"
MAIL_KEYS = {
    "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_AUTH",
    "SMTP_SSL", "SMTP_STARTTLS", "MAIL_FROM",
}


def prepare(root):
    settings = root / ".runtime" / "qq-mail.env"
    settings.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(settings, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return settings
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(TEMPLATE)
    return settings


def credentials(settings):
    values = {}
    for line in settings.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or key not in {"SMTP_USER", "SMTP_PASSWORD"} or key in values:
            raise ValueError("Use exactly one SMTP_USER and one SMTP_PASSWORD entry.")
        values[key] = value.strip()
    address = values.get("SMTP_USER", "").lower()
    secret = values.get("SMTP_PASSWORD", "")
    if not re.fullmatch(r"[a-z0-9._%+-]+@qq\.com", address):
        raise ValueError("Fill SMTP_USER with your complete QQ email address.")
    if not re.fullmatch(r"[A-Za-z0-9]{8,128}", secret) or "AUTHORIZATION" in secret.upper():
        raise ValueError("Fill SMTP_PASSWORD with the QQ SMTP authorization code, without quotes or spaces.")
    return address, secret


def verify(address, secret):
    with smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=10, context=ssl.create_default_context()) as client:
        client.login(address, secret)
        status, _ = client.noop()
        if status != 250:
            raise OSError("SMTP connection check failed.")


def apply(root, address, secret):
    target = root / ".env"
    original = target.read_bytes()
    runtime = root / ".runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    backup = runtime / "qq-mail.previous.env"
    try:
        descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(original)
    lines = [
        line for line in original.decode("utf-8-sig").splitlines()
        if not ("=" in line and line.split("=", 1)[0].strip() in MAIL_KEYS)
    ]
    lines += [
        "SMTP_HOST=smtp.qq.com", "SMTP_PORT=465", "SMTP_USER=" + address,
        "SMTP_PASSWORD=" + secret, "SMTP_AUTH=true", "SMTP_SSL=true",
        "SMTP_STARTTLS=false", "MAIL_FROM=" + address,
    ]
    descriptor, temporary = tempfile.mkstemp(prefix="qq-mail-", suffix=".env", dir=runtime)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write("\n".join(lines) + "\n")
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true", help="Create the ignored two-field credential file without changing active mail settings")
    parser.add_argument("--check", action="store_true", help="Verify credentials against QQ without updating .env")
    args = parser.parse_args()
    if args.prepare:
        print("Fill locally: " + str(prepare(ROOT)))
        return
    if not (ROOT / ".env").exists():
        parser.exit(2, "Run scripts/setup.ps1 or scripts/setup.sh first.\n")
    try:
        address, secret = credentials(ROOT / ".runtime" / "qq-mail.env")
        verify(address, secret)
        if not args.check:
            apply(ROOT, address, secret)
    except smtplib.SMTPAuthenticationError:
        parser.exit(2, "QQ rejected SMTP authentication. Enable SMTP and use a new authorization code. Active settings were kept.\n")
    except ValueError as error:
        parser.exit(2, str(error) + " Active settings were kept.\n")
    except (OSError, smtplib.SMTPException):
        parser.exit(2, "Could not complete QQ SMTP setup. Check the credential file, network and file permissions. No credentials were printed.\n")
    if args.check:
        print("QQ SMTP authentication verified. Active settings were kept. No email was sent.")
    else:
        print("QQ SMTP authentication verified; local .env updated. No email was sent.")
        print("Apply to the running API: docker compose up -d --no-deps --wait api")


if __name__ == "__main__":
    main()
