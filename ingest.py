
import imaplib, email, csv, os
from email.header import decode_header
from datetime import datetime, timezone, timedelta

SUPPORT_KEYWORDS = ["support","query","request","help"]

def _decode_header(value):
    if not value:
        return ""
    parts = decode_header(value)
    result = ""
    for text, enc in parts:
        if isinstance(text, bytes):
            result += text.decode(enc or "utf-8", errors="ignore")
        else:
            result += text
    return result

def fetch_imap(host, username, password, mailbox="INBOX", days_back=7, out_csv="fetched_emails.csv"):
    imap = imaplib.IMAP4_SSL(host)
    imap.login(username, password)
    imap.select(mailbox)
    since = (datetime.utcnow() - timedelta(days=days_back)).strftime("%d-%b-%Y")
    typ, data = imap.search(None, f'(SINCE "{since}")')
    ids = data[0].split()
    rows = []
    for idb in ids:
        typ, msg_data = imap.fetch(idb, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        subject = _decode_header(msg.get("Subject"))
        from_ = _decode_header(msg.get("From"))
        date_ = msg.get("Date")
        # build body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == "text/plain" and part.get("Content-Disposition") is None:
                    body += part.get_payload(decode=True).decode(errors="ignore")
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")
        # filter by subject keywords
        s = subject.lower()
        if any(k in s for k in SUPPORT_KEYWORDS):
            rows.append({"sender": from_, "subject": subject, "body": body, "sent_date": date_})
    # save CSV
    if rows:
        keys = ["sender","subject","body","sent_date"]
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(rows)
    imap.logout()
    return out_csv
