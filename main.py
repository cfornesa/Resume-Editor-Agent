import os
import re
import gc
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI(title="Resume Editor Agent")

# 1. CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. PRIVACY SCRUBBER (Redacts PII locally)
def redact_pii(text: str) -> str:
    patterns = {
        "EMAIL": r'[\w\.-]+@[\w\.-]+\.\w+',
        "PHONE": r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
        "SSN": r'\b(?!666|000|9\d{2})\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}\b',
        "ADDRESS": r'\d{1,5}\s\w+.\s(\b\w+\b\s){1,2}\w+,\s\w+,\s[A-Z]{2}\s\d{5}'
    }
    for label, pattern in patterns.items():
        text = re.sub(pattern, f"[{label}_REDACTED]", text, flags=re.IGNORECASE)
    return text

# 3. INTEGRATED GAIL FRAMEWORK (Veracity & Proportionality Protocol)
def get_resume_system_prompt():
    """
    GOALS: Professionalize resume content without inflationary bias.
    ACTIONS: 
        - STRICT INCLUSION: Only use tools/skills explicitly listed in the input.
        - VERACITY LOCKDOWN: Forbidden from assuming proficiency in SPSS, Stata, or Alteryx.
        - STAR ALIGNMENT: Rewrite experience using the STAR (Situation, Task, Action, Result) method.
    INFORMATION: 
        - Proportional Response: Match the volume and depth of the user's original input.
    LANGUAGE: 
        - STRICTURE: RESPOND IN ENGLISH ONLY. 
        - TONE: Executive, honest, and professional.
    """
    return (
        "You are an Expert Career Strategist. YOU MUST RESPOND IN ENGLISH ONLY.\n\n"
        "ACTIONS (VERACITY LOCKDOWN):\n"
        "1. ZERO EMBELLISHMENT: Do not add any software, skills, or tools not found in the input.\n"
        "2. PROPORTIONALITY: Maintain a similar word count to the user's input. Do not over-summarize.\n"
        "3. STAR METHOD: Restructure experience for impact. Use '[X]' for missing numbers.\n\n"
        "LANGUAGE:\n"
        "Executive and professional. STRICTLY ENGLISH ONLY."
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

# 4. HEALTH CHECK
@app.get("/")
async def health():
    return {"status": "Resume Agent Online", "mode": "Strict-Veracity-Enabled"}

# 5. MAIN EDITING ENDPOINT
@app.post("/chat")
async def process_resume(request: ResumeRequest):
    from openai import OpenAI

    # Consolidate all form fields for the AI
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
    client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

    messages = [
        {"role": "system", "content": get_resume_system_prompt()},
        {"role": "user", "content": f"Optimize this resume data. Do not add unlisted skills:\n{safe_input}"}
    ]

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.2 # Crucial for veracity
        )

        reply_text = response.choices[0].message.content

        # 6. MEMORY MANAGEMENT
        del messages, safe_input, raw_content
        gc.collect()

        return {"reply": reply_text}

    except Exception as e:
        gc.collect()
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)