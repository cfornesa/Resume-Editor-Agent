"""
================================================================================
SYSTEM ARCHITECT: Chris Fornesa
PROJECT: Resume & Career Engineer (Veracity Edition)
MISSION: Professionalizing resumes via STAR logic with zero inflationary bias.
GOVERNANCE: Local PII Redaction, Ethical Model Routing (Mistral), Veracity Lockdown.
================================================================================
"""

import os
import re
import gc
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from flask_cors import CORS

# INITIALIZATION: FastAPI handles high-concurrency async routing with minimal overhead.
app = FastAPI(title="Resume & Career Engineer - Mistral Edition")

# 1. CORS PROTOCOL (The Digital Handshake)
# CONCEPTUAL EXPLANATION: Configures Cross-Origin Resource Sharing to allow 
# secure data exchange between the Hostinger frontend and the Replit API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. PRIVACY SCRUBBER (PII Sanitization Layer)
# MISSION ALIGNMENT: Essential for career services where users share contact info.
# Locally redacts PII to ensure professional data remains sovereign.
def redact_pii(text: str) -> str:
    PII_PATTERNS = {
        "EMAIL": r'[\w\.-]+@[\w\.-]+\.\w+',
        "PHONE": r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
        "SSN": r'\b(?!666|000|9\d{2})\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}\b',
        "ADDRESS": r'\d{1,5}\s\w+.\s(\b\w+\b\s){1,2}\w+,\s\w+,\s[A-Z]{2}\s\d{5}'
    }
    for label, pattern in PII_PATTERNS.items():
        # Corrected flag: re.IGNORECASE ensures robust detection.
        text = re.sub(pattern, f"[{label}_REDACTED]", text, flags=re.IGNORECASE)
    return text

# 3. EXECUTIVE PROTOCOL: VERACITY LOCKDOWN
# FRAMEWORK: STAR Method (Situation, Task, Action, Result) + Proportionality.
# The 'No-Markdown' rule ensures the text is ready for direct copy-paste into Word/PDF.
def get_resume_system_prompt():
    return (
        "You are the GAIL Expert Career Strategist. YOU MUST RESPOND IN ENGLISH ONLY.\n\n"
        "GOALS:\n"
        "Transform raw work history into high-impact professional narratives without inflationary bias.\n\n"
        "STRICT FORMATTING RULE:\n"
        "DO NOT USE MARKDOWN. Do not use asterisks (*) for bolding or italics. Use plain text only.\n"
        "Use clear headers and standard bullet points for structural clarity.\n\n"
        "ACTIONS (VERACITY LOCKDOWN):\n"
        "1. ZERO EMBELLISHMENT: Do not add software, skills, or tools not found in the input.\n"
        "2. PROPORTIONALITY: Match the depth of the original input; do not over-summarize.\n"
        "3. STAR METHOD: Use '[X]' for missing metrics to prompt user verification.\n\n"
        "LANGUAGE:\n"
        "Executive and honest. STRICTLY ENGLISH ONLY."
    )

class ResumeRequest(BaseModel):
    name: str
    occupation: str
    industry: str
    contact: str
    job_description: str
    summary: str
    skills: str
    experience: str
    education: str
    awards: str
    history: List[Dict] = []

# 4. HEALTH CHECK (System Vitality)
@app.get("/")
async def health_check():
    return {
        "status": "online", 
        "agent": "Career Engineer",
        "mode": "Strict-Veracity-Enabled",
        "model": "ministral-14b-2512"
    }

# 5. MAIN API ENDPOINT (/chat)
@app.post("/chat")
async def process_resume(request: ResumeRequest):
    from openai import OpenAI

    # Consolidate all form fields for the AI context
    raw_content = (
        f"Name: {request.name}\n"
        f"Target Occupation: {request.occupation}\n"
        f"Industry: {request.industry}\n"
        f"Contact: {request.contact}\n"
        f"Target JD: {request.job_description}\n"
        f"Summary: {request.summary}\n"
        f"Skills: {request.skills}\n"
        f"Experience: {request.experience}\n"
        f"Education: {request.education}\n"
        f"Awards: {request.awards}"
    )

    safe_input = redact_pii(raw_content)
    api_key = os.environ.get('MISTRAL_API_KEY')

    if not api_key:
        return {"reply": "Error: MISTRAL_API_KEY missing from server secrets."}

    # CHOICE: Mistral AI prioritized for audited environmental transparency.
    client = OpenAI(api_key=api_key, base_url="https://api.mistral.ai/v1")

    messages = [
        {"role": "system", "content": get_resume_system_prompt()},
        {"role": "user", "content": f"Optimize this resume data. Do not add unlisted skills:\n{safe_input}"}
    ]

    try:
        response = client.chat.completions.create(
            model="ministral-14b-latest", 
            messages=messages,
            temperature=0.2, # Deterministic setting for veracity and accuracy.
            max_tokens=1200
        )

        reply_text = response.choices[0].message.content

        # STEP 6: Ecological Resource Management (Garbage Collection)
        del messages, safe_input, raw_content
        gc.collect()

        return {"reply": reply_text.strip()}

    except Exception as e:
        gc.collect()
        return {"reply": f"System Error: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")