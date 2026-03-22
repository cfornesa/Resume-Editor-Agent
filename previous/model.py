import os
import re
import gc
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Dict

# Define the expected structure of a resume request
class ResumeRequest(BaseModel):
    name: str
    occupation: str
    industry: str
    job_description: str
    summary: str
    skills: str
    experience: str
    education: str
    awards: str
    history: List[Dict] = []

# Redact personally identifiable information before sending to the model
def redact_pii(text: str) -> str:
    PII_PATTERNS = {
        "EMAIL":   r'[\w\.-]+@[\w\.-]+\.\w+',
        "PHONE":   r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
        "SSN":     r'\b(?!666|000|9\d{2})\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}\b',
        "ADDRESS": r'\d{1,5}\s\w+.\s(\b\w+\b\s){1,2}\w+,\s\w+,\s[A-Z]{2}\s\d{5}'
    }
    for label, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"[{label}_REDACTED]", text, flags=re.IGNORECASE)
    return text

# System prompt for Phase 1: initial resume construction
def get_build_system_prompt():
    return (
        "You are the GAIL Expert Career Strategist. YOU MUST RESPOND IN ENGLISH ONLY.\n\n"
        "GOALS:\n"
        "Transform raw work history into a complete, high-impact professional resume without inflationary bias.\n\n"
        "STRICT FORMATTING RULE:\n"
        "DO NOT USE MARKDOWN. Do not use asterisks (*) for bolding or italics. Use plain text only.\n"
        "Use clear section headers and standard bullet points for structural clarity.\n\n"
        "ACTIONS (VERACITY LOCKDOWN):\n"
        "1. ZERO EMBELLISHMENT: Do not add software, skills, or tools not found in the input.\n"
        "2. PROPORTIONALITY: Match the depth of the original input; do not over-summarize.\n"
        "3. STAR METHOD: Use '[X]' for missing metrics to prompt user verification.\n"
        "4. STRUCTURE: Output a complete resume with sections: Contact, Summary, Skills, Experience, Education, Awards.\n\n"
        "LANGUAGE:\n"
        "Executive and honest. STRICTLY ENGLISH ONLY."
    )

# System prompt for Phase 2: conversational fine-tuning
def get_edit_system_prompt():
    return (
        "You are the GAIL Expert Career Strategist in fine-tuning mode. YOU MUST RESPOND IN ENGLISH ONLY.\n\n"
        "GOALS:\n"
        "Edit and refine an existing resume based on specific user feedback and instructions.\n\n"
        "STRICT FORMATTING RULE:\n"
        "DO NOT USE MARKDOWN. Do not use asterisks (*) for bolding or italics. Use plain text only.\n"
        "Use clear section headers and standard bullet points for structural clarity.\n\n"
        "ACTIONS:\n"
        "1. Apply only the changes explicitly requested by the user; preserve all other sections as-is.\n"
        "2. ZERO EMBELLISHMENT: Do not add skills or tools not present in the original data.\n"
        "3. Return the full updated resume after applying the requested edits.\n\n"
        "LANGUAGE:\n"
        "Executive and honest. STRICTLY ENGLISH ONLY."
    )

# Initialize the Mistral client using the environment API key
def get_client():
    api_key = os.environ.get('MISTRAL_API_KEY')
    if not api_key:
        raise ValueError("MISTRAL_API_KEY missing from environment.")
    return OpenAI(api_key=api_key, base_url="https://api.mistral.ai/v1")

# Phase 1: Generate an initial resume from structured form data
def build_resume(resume_data: str) -> dict:
    client = get_client()
    safe_input = redact_pii(resume_data)
    messages = [
        {"role": "system", "content": get_build_system_prompt()},
        {"role": "user", "content": f"Build a complete professional resume from this data. Do not add unlisted skills:\n{safe_input}"}
    ]
    try:
        response = client.chat.completions.create(
            model="ministral-14b-latest",
            messages=messages,
            temperature=0.2,
            max_tokens=1500
        )
        reply = response.choices[0].message.content.strip()
        del messages, safe_input
        gc.collect()
        return {"reply": reply, "phase": "build"}
    except Exception as e:
        gc.collect()
        return {"reply": f"System Error: {str(e)}", "phase": "build"}

# Phase 2: Fine-tune the resume based on user chat instructions and prior history
def edit_resume(current_resume: str, user_message: str, history: List[Dict]) -> dict:
    client = get_client()
    messages = [{"role": "system", "content": get_edit_system_prompt()}]
    for entry in history:
        messages.append({"role": entry.get("role", "user"), "content": entry.get("content", "")})
    messages.append({
        "role": "user",
        "content": f"Current Resume:\n{current_resume}\n\nEdit Request: {user_message}"
    })
    try:
        response = client.chat.completions.create(
            model="ministral-14b-latest",
            messages=messages,
            temperature=0.3,
            max_tokens=1500
        )
        reply = response.choices[0].message.content.strip()
        del messages
        gc.collect()
        return {"reply": reply, "phase": "edit"}
    except Exception as e:
        gc.collect()
        return {"reply": f"System Error: {str(e)}", "phase": "edit"}