import os
import re
import gc
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI(title="Resume Editor Agent")

# 1. CORS CONFIGURATION (Essential for Replit to Hostinger communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. PRIVACY SCRUBBER (Redacts PII, SSNs, and Physical Addresses)
def redact_pii(text: str) -> str:
    """
    Scrubs sensitive contact info before it leaves the Replit environment.
    Essential for Resumes which naturally contain high-density PII.
    """
    patterns = {
        "EMAIL": r'[\w\.-]+@[\w\.-]+\.\w+',
        "PHONE": r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
        "SSN": r'\b(?!666|000|9\d{2})\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}\b',
        "ADDRESS": r'\d{1,5}\s\w+.\s(\b\w+\b\s){1,2}\w+,\s\w+,\s[A-Z]{2}\s\d{5}'
    }
    for label, pattern in patterns.items():
        text = re.sub(pattern, f"[{label}_REDACTED]", text, flags=re.IGNORECASE)
    return text

# 3. INTEGRATED GAIL FRAMEWORK (Proportionality & Veracity Protocol)
def get_resume_system_prompt():
    """
    GOALS: Tailor resumes for ATS compatibility while maintaining factual integrity.
    ACTIONS: 
        - PROPORTIONAL DENSITY: Match the word length and detail level of the user's input.
        - ACTION-ORIENTED VERACITY: Use strong verbs; use '[X]' for missing metrics.
        - ANTI-HALLUCINATION: Do not invent roles, dates, or companies.
    INFORMATION: 
        - Align content with the 'Target Job Description' provided by the user.
        - Utilize the STAR (Situation, Task, Action, Result) method for bullet points.
    LANGUAGE: 
        - STRICTURE: RESPOND IN ENGLISH ONLY.
        - TONE: Professional, executive, and authoritative.
    """
    return (
        "You are an Expert Career Strategist. YOU MUST RESPOND IN ENGLISH ONLY.\n\n"
        "GOALS:\n"
        "Optimize the provided resume data for impact and ATS-readiness.\n\n"
        "ACTIONS (PROPORTIONALITY & VERACITY):\n"
        "1. LENGTH MATCHING: Maintain a similar volume of content to the input. Do not over-summarize.\n"
        "2. NO HALLUCINATIONS: Never invent accomplishments. Use '[X]' to prompt for missing numbers.\n"
        "3. STAR ALIGNMENT: Rephrase experience using the STAR method for maximum clarity.\n\n"
        "INFORMATION:\n"
        "Integrate keywords from the 'Target Job Description'. Respect [REDACTED] placeholders.\n\n"
        "LANGUAGE:\n"
        "Executive and punchy. Use Markdown headers for clear sectioning. STRICTLY ENGLISH ONLY."
    )

# Updated Pydantic Model to match your HTML form fields
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

# 4. HEALTH CHECK (Verifies server status and safety protocols)
@app.get("/")
async def health():
    return {
        "status": "Resume Agent Online", 
        "mode": "Proportional-Veracity-Enabled",
        "privacy": "Full-Scrub-Active"
    }

# 5. MAIN EDITING ENDPOINT
@app.post("/chat")
async def process_resume(request: ResumeRequest):
    # DEFERRED IMPORT: Minimizes RAM usage during idle time
    from openai import OpenAI

    # Consolidate UI fields for processing
    raw_content = f"""
    Name: {request.name}
    Occupation: {request.occupation}
    Industry: {request.industry}
    Contact: {request.contact}
    Target JD: {request.job_description}
    Summary: {request.summary}
    Skills: {request.skills}
    Experience: {request.experience}
    Education: {request.education}
    Awards: {request.awards}
    """

    # Redact input locally to protect user identities
    safe_input = redact_pii(raw_content)

    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        return {"error": "DeepSeek API Key missing in Replit Secrets."}

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    # Construct message chain for DeepSeek-V3
    messages = [
        {"role": "system", "content": get_resume_system_prompt()},
        {"role": "user", "content": f"Optimize the following resume data:\n{safe_input}"}
    ]

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            # Low temperature ensures the agent sticks to the facts provided
            temperature=0.3,
            max_tokens=2000
        )

        reply = response.choices[0].message.content

        # 6. MEMORY MANAGEMENT (GARBAGE COLLECTION)
        del messages, safe_input, raw_content
        gc.collect()

        return {"reply": reply}
    except Exception as e:
        gc.collect()
        return {"error": f"Editing interrupted: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    # Optimized run for Replit
    uvicorn.run(app, host="0.0.0.0", port=5000)