import pandas as pd
import re, json
import sqlite3
from datetime import datetime
from pathlib import Path

# -------------------- Filters & Keywords --------------------
SUBJECT_FILTERS = ["support", "query", "request", "help"]
URGENT_KEYWORDS = [
    "urgent", "immediate", "immediately", "critical", "highly critical", "down", "blocked",
    "inaccessible", "cannot access", "can't access", "cannot", "can't", "password", "reset link",
    "charged twice", "billing error", "refund", "system is completely inaccessible", "servers are down"
]
NEGATIVE_KEYWORDS = ["unable", "cannot", "can't", "error", "down", "inaccessible", "blocked", "urgent", "failure", "problem", "frustrat"]
POSITIVE_KEYWORDS = ["thank you", "thanks", "appreciate", "great", "good", "excellent"]

EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
PHONE_REGEX = r"(\+?\d[\d\-\s()]{7,}\d)"

TOPIC_KEYWORDS = {
    "Account Verification": ["verify", "verification", "verification email"],
    "Login/Access": ["log in", "login", "password", "reset", "cannot access", "blocked", "inaccessible"],
    "Billing/Pricing": ["billing", "charged twice", "refund", "pricing", "tiers", "invoice"],
    "Downtime/Outage": ["down", "servers are down", "downtime", "outage"],
    "Integrations/API": ["api", "integration", "crm", "third-party", "third party"]
}

DB_PATH = Path("emails.db")

# -------------------- Email Processing --------------------
def load_emails(file_path):
    df = pd.read_csv(file_path, parse_dates=["sent_date"])
    return df

def subject_filter_mask(df):
    return df["subject"].str.lower().str.contains("|".join(SUBJECT_FILTERS), na=False)

def contains_any(text, keywords):
    if not isinstance(text, str):
        return False
    t = text.lower()
    return any(kw in t for kw in keywords)

def classify_sentiment(row):
    text = f"{row.get('subject','')} {row.get('body','')}"
    if contains_any(text, NEGATIVE_KEYWORDS):
        return "Negative"
    if contains_any(text, POSITIVE_KEYWORDS):
        return "Positive"
    return "Neutral"

def classify_priority(row):
    text = f"{row.get('subject','')} {row.get('body','')}"
    return "Urgent" if contains_any(text, URGENT_KEYWORDS) else "Not urgent"

def extract_emails(text):
    matches = re.findall(EMAIL_REGEX, str(text))
    return list(dict.fromkeys(matches)) if matches else None

def extract_phones(text):
    matches = re.findall(PHONE_REGEX, str(text))
    cleaned = [re.sub(r"[^\d+]", "", m) for m in matches]
    return list(dict.fromkeys(cleaned)) if cleaned else None

def tag_topics(text):
    t = str(text).lower()
    matched = []
    for label, kws in TOPIC_KEYWORDS.items():
        if any(kw in t for kw in kws):
            matched.append(label)
    return matched if matched else None

# -------------------- Database --------------------
def ensure_db(db_path=DB_PATH):
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        subject TEXT,
        body TEXT,
        sent_date TEXT,
        priority TEXT,
        sentiment TEXT,
        topics TEXT,
        extracted_emails TEXT,
        extracted_phones TEXT,
        ai_reply TEXT,
        status TEXT,
        updated_at TEXT,
        UNIQUE(sender, subject, sent_date)
    )""")
    conn.commit()
    return conn

def upsert_emails(df, db_path=DB_PATH):
    conn = ensure_db(db_path)
    c = conn.cursor()
    for _, row in df.iterrows():
        sent_date = None
        sd = row.get("sent_date")
        if pd.notna(sd):
            try:
                sent_date = pd.to_datetime(sd).isoformat()
            except Exception:
                sent_date = str(sd)
        topics = json.dumps(row.get("topics")) if row.get("topics") is not None else None
        extracted_emails = json.dumps(row.get("extracted_emails")) if row.get("extracted_emails") is not None else None
        extracted_phones = json.dumps(row.get("extracted_phones")) if row.get("extracted_phones") is not None else None
        ai_reply = row.get("ai_reply") or None
        status = row.get("status") or "Pending"
        c.execute("""INSERT OR REPLACE INTO emails
            (id, sender, subject, body, sent_date, priority, sentiment, topics, extracted_emails, extracted_phones, ai_reply, status, updated_at)
            VALUES (
                COALESCE((SELECT id FROM emails WHERE sender=? AND subject=? AND sent_date=?), NULL),
                ?,?,?,?,?,?,?,?,?,?,?,?
            )
        """, (
            row.get("sender"), row.get("subject"), sent_date,
            row.get("sender"), row.get("subject"), row.get("body"),
            sent_date, row.get("priority"), row.get("sentiment"), topics,
            extracted_emails, extracted_phones, ai_reply, status,
            datetime.utcnow().isoformat()
        ))
    conn.commit()
    conn.close()

# -------------------- Full Processing --------------------
def process_and_enrich(file_path):
    df = load_emails(file_path)
    df = df[subject_filter_mask(df)].copy().reset_index(drop=True)
    df["sentiment"] = df.apply(classify_sentiment, axis=1)
    df["priority"] = df.apply(classify_priority, axis=1)
    df["extracted_emails"] = df["body"].apply(extract_emails)
    df["extracted_phones"] = df["body"].apply(extract_phones)
    df["topics"] = (df["subject"] + " " + df["body"]).apply(tag_topics)
    df["ai_reply"] = None
    df["status"] = "Pending"
    try:
        df["sent_date"] = pd.to_datetime(df["sent_date"])
    except Exception:
        pass
    return df
