import pandas as pd
import re

# ---- Load Emails ----
def load_emails(file) -> pd.DataFrame:
    """Load CSV of emails and ensure required columns exist."""
    df = pd.read_csv(file)

    # Ensure required columns
    required_cols = ["id", "sender", "subject", "body", "sent_date"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""  # add missing cols with empty values

    return df


# ---- Classify Urgency ----
def classify_email(row) -> str:
    """Classify email urgency based on subject/body keywords."""
    urgent_keywords = ["urgent", "immediately", "critical", "cannot access", "asap"]
    text = f"{row.get('subject','')} {row.get('body','')}".lower()

    if any(word in text for word in urgent_keywords):
        return "Urgent"
    return "Not Urgent"


# ---- Summarize Email ----
def summarize_email(body: str) -> str:
    """Basic summary: take first 25 words of email body."""
    if not isinstance(body, str):
        return ""
    words = body.split()
    return " ".join(words[:25]) + ("..." if len(words) > 25 else "")


# ---- Priority Queue ----
def build_priority_queue(df: pd.DataFrame):
    """Return indices sorted by urgency and recency (Urgent first, then latest emails)."""
    if "Urgency" not in df.columns:
        df["Urgency"] = df.apply(classify_email, axis=1)

    # Assign numeric priority (Urgent=0, Not Urgent=1) for sorting
    df["_priority_score"] = df["Urgency"].apply(lambda x: 0 if x == "Urgent" else 1)

    if "sent_date" in df.columns:
        try:
            df["sent_date"] = pd.to_datetime(df["sent_date"], errors="coerce")
        except Exception:
            pass

    ordered_idx = df.sort_values(
        by=["_priority_score", "sent_date"],
        ascending=[True, False]
    ).index

    return ordered_idx
