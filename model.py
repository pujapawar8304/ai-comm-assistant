from dotenv import load_dotenv
import os
from openai import OpenAI

# Load .env file
load_dotenv()

# Initialize client with your secret "test key"
client = OpenAI(api_key=os.getenv("test"))

def draft_reply(subject, body):
    """Draft a short professional empathetic reply using OpenAI.
    If API key is missing, returns a fallback stub reply.
    """
    if not os.getenv("test key"):
        return f"Hello,\n\nThanks for reaching out about \"{subject}\". We apologize for the trouble. Our team is looking into this and will get back to you shortly with next steps.\n\nBest regards,\nSupport Team"

    prompt = f"""You are a helpful customer support agent. Write a concise, empathetic, and professional reply to the following customer email. Keep it actionable and ask for any missing info needed to resolve the issue.

Subject: {subject}

Message:
{body}

Reply:"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",   # or "gpt-4o-mini" if you want faster/cheaper
            messages=[
                {"role": "system", "content": "You are a helpful customer support assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.6,
        )
        text = response.choices[0].message.content.strip()
        return text
    except Exception as e:
        return f"[AI generation error: {e}] Hello, thanks for contacting support about '{subject}'. We'll follow up shortly."
