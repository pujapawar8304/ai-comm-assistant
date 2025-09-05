# 📧 AI Communication Assistant – Enhanced

An AI-powered email assistant built with **Streamlit** and **OpenAI**, designed to:
- Upload customer email CSVs
- Process and enrich emails with priority, sentiment, and topics
- Store processed emails in a local SQLite database
- Generate **AI-drafted replies** using OpenAI’s GPT models
- Save, edit, and mark replies as resolved
- Download enriched CSVs with replies

---

## 🚀 Features
- 📊 Dashboard with key email metrics (total, urgent, pending, resolved)
- 📈 Priority distribution bar chart and timeline chart
- 📨 Queue of emails with **AI-generated draft replies**
- ✍️ Edit and save replies directly in the app
- ✅ Mark emails as resolved
- 💾 Save to SQLite (`emails.db`) + export `processed_emails.csv`

---

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/pujapawar8304/ai-comm-assistant.git
   cd ai-comm-assistant
