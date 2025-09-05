
import streamlit as st
import pandas as pd
from email_utils import process_and_enrich, upsert_emails
from model import draft_reply
import sqlite3, json
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="AI Support Assistant (Enhanced)", layout="wide")
st.title("📧 AI Communication Assistant – Enhanced")

DATA_DIR = Path(".")
DB_PATH = DATA_DIR / "emails.db"
PROCESSED_CSV = DATA_DIR / "processed_emails.csv"

def load_processed_from_db(db_path=DB_PATH):
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    df = pd.read_sql_query("SELECT * FROM emails", conn, parse_dates=["sent_date","updated_at"])
    conn.close()
    return df

uploaded = st.file_uploader("Upload Email CSV", type=["csv"])

if uploaded:
    with st.spinner("Processing and enriching emails..."):
        df_new = process_and_enrich(uploaded)
        df_new.to_csv(PROCESSED_CSV, index=False)
        upsert_emails(df_new, db_path=DB_PATH)
    st.success("Processed and saved to DB and processed_emails.csv")

df = load_processed_from_db()
if df is None and PROCESSED_CSV.exists():
    df = pd.read_csv(PROCESSED_CSV, parse_dates=["sent_date"])

if df is None:
    st.info("No processed emails found. Upload a CSV to begin.")
    st.stop()

# parse JSON-like columns
if "topics" in df.columns and df["topics"].dtype == object:
    try:
        df["topics"] = df["topics"].apply(lambda x: json.loads(x) if isinstance(x, str) and x.startswith('[') else x)
    except Exception:
        pass

st.subheader("Key Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Emails", int(len(df)))
col2.metric("Urgent", int((df['priority'] == "Urgent").sum()) if 'priority' in df.columns else 0)
col3.metric("Pending", int((df['status'] == "Pending").sum()) if 'status' in df.columns else 0)
col4.metric("Resolved", int((df['status'] == "Resolved").sum()) if 'status' in df.columns else 0)

st.subheader("Analytics")
priority_counts = df['priority'].value_counts() if 'priority' in df.columns else pd.Series()
st.bar_chart(priority_counts)

if 'sent_date' in df.columns:
    timeline = df.copy()
    timeline['date_only'] = pd.to_datetime(timeline['sent_date']).dt.date
    timeline = timeline.groupby(['date_only','priority']).size().unstack(fill_value=0)
    if not timeline.empty:
        st.line_chart(timeline)

st.subheader("Email Queue (select an email to view details)")
display_cols = ["id","sender","subject","sent_date","priority","sentiment","status"]
display_cols = [c for c in display_cols if c in df.columns]
st.dataframe(df[display_cols].sort_values(by=["priority","sent_date"], ascending=[False, False]).reset_index(drop=True))

selected_id = st.number_input("Enter email id to inspect (use 'id' from table above)", min_value=0, step=1, value=0)
selected_row = None
if selected_id:
    matches = df[df["id"]==int(selected_id)]
    if not matches.empty:
        selected_row = matches.iloc[0]
    else:
        st.warning("No email with that id found in processed data.")

if selected_row is not None:
    st.markdown(f"**From:** {selected_row['sender']}  \n**Subject:** {selected_row['subject']}  \n**Received:** {selected_row['sent_date']}  \n**Priority:** {selected_row['priority']}  \n**Sentiment:** {selected_row['sentiment']}  \n**Topics:** {selected_row['topics']}")
    st.subheader("Email Body")
    st.write(selected_row["body"])
    ai_text = selected_row.get("ai_reply") if "ai_reply" in selected_row.index else None
    ai_draft = st.text_area("AI Draft Reply (editable)", value=ai_text or "", height=250, key=f"draft_{selected_id}")
    generate = st.button("Generate AI Reply for this email", key="gen_"+str(selected_id))
    if generate:
        with st.spinner("Generating reply..."):
            reply = draft_reply(selected_row["subject"], selected_row["body"])
            ai_draft = reply
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()
            c.execute("UPDATE emails SET ai_reply=?, status=?, updated_at=? WHERE id=?", (ai_draft, "Pending", datetime.utcnow().isoformat(), int(selected_id)))
            conn.commit()
            conn.close()
            st.success("AI reply generated and saved to DB.")
    save_reply = st.button("Save edited reply", key="save_"+str(selected_id))
    if save_reply:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("UPDATE emails SET ai_reply=?, updated_at=? WHERE id=?", (ai_draft, datetime.utcnow().isoformat(), int(selected_id)))
        conn.commit()
        conn.close()
        st.success("Edited reply saved.")
    if st.button("Mark as Resolved", key="resolve_"+str(selected_id)):
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("UPDATE emails SET status=?, updated_at=? WHERE id=?", ("Resolved", datetime.utcnow().isoformat(), int(selected_id)))
        conn.commit()
        conn.close()
        st.success("Marked email as Resolved.")

with open(PROCESSED_CSV, "rb") as f:
    st.download_button("Download processed_emails.csv", f, file_name="processed_emails.csv")

st.info("Notes: This app saves processed emails to a local SQLite DB (emails.db) and processed_emails.csv. In production, secure your OPENAI_API_KEY as an environment variable or platform secret.")
