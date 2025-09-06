import streamlit as st
import pandas as pd
import sqlite3, json, io
from pathlib import Path
from datetime import datetime
from email_utils import process_and_enrich, upsert_emails
from model import draft_reply

st.set_page_config(page_title="📧 AI Email Assistant (Full)", layout="wide")
st.title("📧 AI Communication Assistant – Full")

DATA_DIR = Path(".")
DB_PATH = DATA_DIR / "emails.db"
PROCESSED_CSV = DATA_DIR / "processed_emails.csv"

# -------------------- Helper Functions --------------------
def load_processed_from_db(db_path=DB_PATH):
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    df = pd.read_sql_query("SELECT * FROM emails", conn, parse_dates=["sent_date","updated_at"])
    conn.close()
    return df

# -------------------- Upload & Process Emails --------------------
uploaded = st.file_uploader("Upload Email CSV", type=["csv"])

if uploaded:
    with st.spinner("Processing and enriching emails..."):
        # handle file-like object
        df_new = process_and_enrich(io.BytesIO(uploaded.read()))
        df_new.to_csv(PROCESSED_CSV, index=False)
        upsert_emails(df_new, db_path=DB_PATH)
    st.success("✅ Processed and saved to DB + processed_emails.csv")

df = load_processed_from_db()
if df is None and PROCESSED_CSV.exists():
    df = pd.read_csv(PROCESSED_CSV, parse_dates=["sent_date"])

if df is None:
    st.info("No processed emails found. Upload a CSV to begin.")
    st.stop()

# Parse topics JSON safely
if "topics" in df.columns and df["topics"].dtype == object:
    try:
        df["topics"] = df["topics"].apply(
            lambda x: json.loads(x) if isinstance(x, str) and (x.startswith("[") or x.startswith("{")) else x
        )
    except Exception:
        pass

# -------------------- Metrics --------------------
st.subheader("📊 Key Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Emails", int(len(df)))
col2.metric("Urgent", int((df['priority'] == "Urgent").sum()) if 'priority' in df.columns else 0)
col3.metric("Pending", int((df['status'] == "Pending").sum()) if 'status' in df.columns else 0)
col4.metric("Resolved", int((df['status'] == "Resolved").sum()) if 'status' in df.columns else 0)

# -------------------- Analytics --------------------
st.subheader("📈 Analytics")
if 'priority' in df.columns:
    st.bar_chart(df['priority'].value_counts())

if 'sent_date' in df.columns:
    timeline = df.copy()
    timeline['date_only'] = pd.to_datetime(timeline['sent_date']).dt.date
    timeline = timeline.groupby(['date_only','priority']).size().unstack(fill_value=0)
    if not timeline.empty:
        st.line_chart(timeline)

# -------------------- Email Queue --------------------
st.subheader("📬 Email Queue")
display_cols = ["id","sender","subject","sent_date","priority","sentiment","status"]
display_cols = [c for c in display_cols if c in df.columns]
st.dataframe(df[display_cols].sort_values(by=["priority","sent_date"], ascending=[False, False]).reset_index(drop=True))

selected_id = st.number_input("Enter email id to inspect (use 'id' from table above)", min_value=1, step=1, value=1)
selected_row = df[df["id"]==int(selected_id)].iloc[0] if int(selected_id) in df["id"].values else None

if selected_row is not None:
    st.markdown(f"**From:** {selected_row['sender']}  \n**Subject:** {selected_row['subject']}  \n**Received:** {selected_row['sent_date']}  \n**Priority:** {selected_row['priority']}  \n**Sentiment:** {selected_row['sentiment']}  \n**Topics:** {selected_row['topics']}")
    st.subheader("Email Body")
    st.write(selected_row["body"])

    ai_text = selected_row.get("ai_reply") if "ai_reply" in selected_row.index else None
    ai_draft = st.text_area("AI Draft Reply (editable)", value=ai_text or "", height=250, key=f"draft_{selected_id}")

    if st.button("🤖 Generate AI Reply for this email", key=f"gen_{selected_id}"):
        with st.spinner("Generating reply..."):
            reply = draft_reply(selected_row["subject"], selected_row["body"])
            ai_draft = reply
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()
            c.execute("UPDATE emails SET ai_reply=?, status=?, updated_at=? WHERE id=?", (ai_draft, "Pending", datetime.utcnow().isoformat(), int(selected_id)))
            conn.commit()
            conn.close()
            st.success("✅ AI reply generated and saved.")

    if st.button("💾 Save Edited Reply", key=f"save_{selected_id}"):
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("UPDATE emails SET ai_reply=?, updated_at=? WHERE id=?", (ai_draft, datetime.utcnow().isoformat(), int(selected_id)))
        conn.commit()
        conn.close()
        st.success("✅ Reply saved.")

    if st.button("✅ Mark as Resolved", key=f"resolve_{selected_id}"):
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("UPDATE emails SET status=?, updated_at=? WHERE id=?", ("Resolved", datetime.utcnow().isoformat(), int(selected_id)))
        conn.commit()
        conn.close()
        st.success("✅ Email marked as Resolved.")

# -------------------- Bulk AI Reply Generator --------------------
st.subheader("⚡ Bulk AI Reply Generator (Quick Mode)")

if st.button("Generate AI Replies for All Emails"):
    with st.spinner("Generating replies..."):
        df["ai_reply"] = df.apply(lambda row: draft_reply(row["subject"], row["body"]), axis=1)
        df.to_csv(PROCESSED_CSV, index=False)
        upsert_emails(df, DB_PATH)   # <-- FIX: update DB as well
    st.success("✅ AI Replies generated for all emails.")
    st.dataframe(df[["sender","subject","ai_reply"]])

    st.download_button(
        label="⬇️ Download processed_emails.csv",
        data=open(PROCESSED_CSV, "rb").read(),
        file_name="processed_emails.csv",
        mime="text/csv"
    )

# -------------------- Download --------------------
with open(PROCESSED_CSV, "rb") as f:
    st.download_button("⬇️ Download Current processed_emails.csv", f, file_name="processed_emails.csv")

st.info("ℹ️ Notes: This app uses both a local SQLite DB (emails.db) and CSV (processed_emails.csv). In production, secure your OPENAI_API_KEY via environment variables or platform secrets.")
