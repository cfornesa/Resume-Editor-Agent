import os
import re
import gc
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI(title="Political Behavior Agent")

# 1. CORS CONFIGURATION (Essential for Hostinger-Replit Handshake)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. PRIVACY SCRUBBER (Redacts PII to protect user identities in sensitive research)
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

# 3. INTEGRATED GAIL FRAMEWORK (Analytical & English-Anchored)
def get_political_system_prompt():
    """
    GOALS: Synthesize political science theory with behavioral data analysis.
    ACTIONS: 
        - Analyze queries through the lens of political psychology (e.g., bias, heuristic use).
        - SCOPE GUARD: If the query is unrelated to politics or social science, state 
          'I focus solely on political behavior' and pivot to a relevant concept.
    INFORMATION: 
        - Utilize peer-reviewed frameworks and historical political case studies.
    LANGUAGE: 
        - STRICTURE: RESPOND IN ENGLISH ONLY.
        - TONE: Academic, objective, and analytical.
    """
    return (
        "You are an Expert Political Behavior Consultant. YOU MUST RESPOND IN ENGLISH ONLY.\n\n"
        "GOALS:\n"
        "Provide objective, data-driven analysis of political psychology and human behavior.\n\n"
        "ACTIONS:\n"
        "1. ANALYTICAL DEPTH: When discussing political trends, reference psychological "
        "mechanisms like 'In-group favoritism' or 'Cognitive dissonance'.\n"
        "2. SCOPE CONTROL: For non-political/social science topics, state 'I focus solely on "
        "political behavior' and pivot to a social science theory.\n\n"
        "INFORMATION:\n"
        "Maintain strict neutrality. Do not advocate for specific parties; analyze the "
        "BEHAVIOR and MOTIVATION behind political actors.\n\n"
        "LANGUAGE:\n"
        "Academic and precise. STRICTLY ENGLISH ONLY."
    )

class ChatRequest(BaseModel):
    message: str
    history: List[Dict] = []

# 4. HEALTH CHECK (Ensures the analytical safeguards are active)
@app.get("/")
async def health():
    return {
        "status": "Political Behavior Agent Online",
        "mode": "Neutrality-Protocol-Active",
        "privacy": "Full-Scrub-Active"
    }

# 5. MAIN CHAT ENDPOINT
@app.post("/chat")
async def process_chat(request: ChatRequest):
    from openai import OpenAI

    # Redact input locally
    safe_input = redact_pii(request.message)

    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        return {"error": "DeepSeek API Key missing."}

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    # Construct message chain
    messages = [{"role": "system", "content": get_political_system_prompt()}] + request.history
    messages.append({"role": "user", "content": safe_input})

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            # Temperature 0.4 ensures high objective consistency
            temperature=0.4
        )

        reply = response.choices[0].message.content

        # 6. MEMORY MANAGEMENT (GARBAGE COLLECTION)
        del messages, safe_input
        gc.collect()

        return {"reply": reply}
    except Exception as e:
        gc.collect()
        return {"error": f"Analysis interrupted: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)