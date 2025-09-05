import pandas as pd

def load_emails(file):
    return pd.read_csv(file)

def classify_email(row):
    urgent_keywords = ["urgent", "help", "error", "asap", "unable"]
    text = (str(row['subject']) + " " + str(row['body'])).lower()
    return "Urgent" if any(word in text for word in urgent_keywords) else "Not Urgent"

def summarize_email(body, max_words=20):
    words = body.split()
    return " ".join(words[:max_words]) + ("..." if len(words) > max_words else "")
