import os
import openai

# Load API key from environment (set in Streamlit Secrets or system env)
OPENAI_API_KEY = os.getenv("test")

def draft_reply(subject, body):
    """Draft a short professional empathetic reply using OpenAI.
    If OPENAI_API_KEY is not set, returns a safe stub reply.
    """
    if not OPENAI_API_KEY:
        # fallback stub (safe for hackathon / offline mode)
        return (
            f"Hello,\n\n"
            f"Thanks for reaching out about \"{subject}\". "
            f"We apologize for the trouble. Our team is looking into this "
            f"and will get back to you shortly.\n\nBest regards,\nSupport Team"
        )

    openai.api_key = OPENAI_API_KEY
    prompt = f"""
You are a helpful customer support agent. Write a concise, empathetic, and professional reply 
to the following customer email. Keep it actionable and ask for any missing info needed 
to resolve the issue.

Subject: {subject}

Message:
{body}

Reply:
"""
    try:
        response = openai.Completion.create(
            model="text-davinci-003",   # legacy GPT-3 model
            prompt=prompt,
            max_tokens=200,
            temperature=0.6,
            n=1
        )
        return response.choices[0].text.strip()

    except Exception as e:
        return f"[AI error: {e}] Hello, thanks for contacting us about '{subject}'. We'll follow up shortly."
