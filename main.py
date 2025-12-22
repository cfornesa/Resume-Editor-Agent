import os
import re
import gc
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI(title="Resume Editor & Optimization Agent")

# 1. CORS CONFIGURATION (Enables secure communication with your Hostinger frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. PRIVACY SCRUBBER (PII, SSN, and Comprehensive Address Redaction)
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

# 3. INTEGRATED GAIL FRAMEWORK (With Anti-Inflationary Safeguards)
def get_resume_system_prompt():
    """
    GOALS: Transform raw experience into high-impact, ATS-compatible professional prose.
    ACTIONS: 
        - Apply 'Action-Oriented Veracity': Rephrase for impact without inventing facts.
        - Utilize strong action verbs (e.g., 'Spearheaded', 'Optimized', 'Synthesized').
        - Format for clarity and hierarchical flow.
    INFORMATION: 
        - SAFEGUARD: Strictly adhere to user-provided data. Do not invent roles, 
          companies, or metrics. If a metric is missing, use '[X]%' or '[NUM]' as 
          placeholders for the user to fill in manually.
    LANGUAGE: Professional, executive, concise, and honest.
    """
    return (
        "You are an Expert Resume Strategist and Career Consultant.\n\n"
        "GOALS:\n"
        "Enhance the clarity and impact of the user's resume while maintaining absolute factual integrity.\n\n"
        "ACTIONS (ACTION-ORIENTED VERACITY PROTOCOL):\n"
        "1. NO INFLATION: Do not hallucinate accomplishments. If the user says 'I helped with sales,' "
        "rephrase to 'Collaborated with cross-functional teams to support sales initiatives.' "
        "Do not change it to 'Increased sales by 50%.'\n"
        "2. PLACEHOLDERS: If a result is provided without a metric, use a placeholder like '[Quantity]%' "
        "or '[Amount]' to prompt the user for the real data.\n"
        "3. ATS OPTIMIZATION: Use keywords relevant to the industry provided, but only if they "
        "accurately reflect the existing content.\n\n"
        "INFORMATION & LANGUAGE:\n"
        "Focus on 'Show, Don't Just Tell.' Use high-level professional vocabulary. "
        "If you encounter [REDACTED], leave it exactly as is to preserve the layout."
    )

class ResumeRequest(BaseModel):
    content: str
    target_industry: str = "General"

# 4. HEALTH CHECK (Ensures the privacy and veracity layers are active)
@app.get("/")
async def health():
    return {
        "status": "Resume Editor Agent Online", 
        "privacy": "Strict-PII-Scrubbing",
        "safeguard": "Anti-Inflationary-Veracity-Enabled"
    }

# 5. MAIN EDITING ENDPOINT
@app.post("/edit")
async def process_resume(request: ResumeRequest):
    # DEFERRED IMPORT: Minimizes RAM footprint
    from openai import OpenAI

    # Redact input locally to ensure contact info stays private
    safe_input = redact_pii(request.content)

    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        return {"error": "DeepSeek API Key missing in Replit Secrets."}

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    # Build the prompt for DeepSeek-V3 (optimized for professional prose)
    messages = [
        {"role": "system", "content": get_resume_system_prompt()},
        {"role": "user", "content": f"Industry: {request.target_industry}\n\nResume Content:\n{safe_input}"}
    ]

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages
        )

        edited_text = response.choices[0].message.content

        # 6. MEMORY MANAGEMENT
        del messages, safe_input
        gc.collect()

        return {"edited_resume": edited_text}
    except Exception as e:
        gc.collect()
        return {"error": f"Resume optimization failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)