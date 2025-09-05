# AI Communication Assistant (Enhanced)

This enhanced version adds:
- Analytics charts (priority counts, timeline)
- AI reply generation (OpenAI) with fallback stub when no key
- Improved urgency rules & topic extraction
- Persistence to SQLite (emails.db) and processed_emails.csv
- UI controls to generate/save replies and mark emails as Resolved

## Run locally
1. Create and activate a venv
2. Install requirements: `pip install -r requirements.txt`
3. Set your OpenAI API key as a user environment variable `OPENAI_API_KEY` or create a `.env` file
4. Run: `streamlit run dashboard.py`
