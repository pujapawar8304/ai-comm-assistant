
import os
import openai
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def draft_reply(subject, body):
    """Draft a short professional empathetic reply using OpenAI.
    If OPENAI_API_KEY is not set, returns a safe stub reply.
    """
    if not OPENAI_API_KEY:
        # fallback stub (safe for hackathon / offline)
        return f"Hello,\n\nThanks for reaching out about \"{subject}\". We apologize for the trouble. Our team is looking into this and will get back to you shortly with next steps.\n\nBest regards,\nSupport Team"
    openai.api_key = OPENAI_API_KEY
    prompt = f"""You are a helpful customer support agent. Write a concise, empathetic, and professional reply to the following customer email. Keep it actionable and ask for any missing info needed to resolve the issue.

Subject: {subject}

Message:
{body}

Reply:"""
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=200,
            temperature=0.6,
            n=1
        )
        text = response.choices[0].text.strip()
        return text
    except Exception as e:
        return f"[AI generation error: {e}] Hello, thanks for contacting support about '{subject}'. We'll follow up shortly."
