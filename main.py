import os
import re
import gc
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI(title="Tanaga Poetry Agent")

# 1. CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. PRIVACY SCRUBBER
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

# 3. INTEGRATED GAIL FRAMEWORK (Syllabic & Rhyme Strictness)
def get_tanaga_system_prompt():
    """
    GOALS: Generate authentic Filipino Tanagas (4 lines, 7 syllables each).
    ACTIONS: 
        - STRUCTURAL CHECK: Verify that each line has exactly 7 syllables.
        - RHYME CHECK: Adhere to the traditional AAAA or AABB rhyme schemes.
    INFORMATION: 
        - Incorporate traditional 'Talinghaga' (metaphor) based on user themes.
    LANGUAGE: 
        - STRICTURE: RESPOND IN ENGLISH ONLY (unless Tagalog is requested for the poem).
        - TONE: Poetic, rhythmic, and culturally respectful.
    """
    return (
        "You are a Master of the Traditional Tanaga. YOU MUST RESPOND IN ENGLISH.\n\n"
        "GOALS:\n"
        "Compose a poem with 4 lines, 7 syllables per line, and a consistent rhyme scheme.\n\n"
        "ACTIONS:\n"
        "1. SYLLABLE COUNT: Before outputting, mentally verify each line is exactly 7 syllables.\n"
        "2. THEME: Use the user's prompt to create deep metaphors (Talinghaga).\n\n"
        "INFORMATION:\n"
        "Respect the Filipino heritage of the form. Use [REDACTED] as a metaphor for silence.\n\n"
        "LANGUAGE:\n"
        "Poetic and precise. STRICTLY ENGLISH FOR EXPLANATIONS."
    )

class PoetryRequest(BaseModel):
    theme: str
    history: List[Dict] = []

# 4. HEALTH CHECK
@app.get("/")
async def health():
    return {"status": "Tanaga Agent Online", "mode": "Structural-Strictness-Active"}

# 5. MAIN CHAT ENDPOINT
@app.post("/chat")
async def process_chat(request: PoetryRequest):
    from openai import OpenAI
    safe_input = redact_pii(request.theme)
    client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

    messages = [{"role": "system", "content": get_tanaga_system_prompt()}] + request.history
    messages.append({"role": "user", "content": safe_input})

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.8 # Higher temperature for poetic creativity
        )
        reply = response.choices[0].message.content
        del messages, safe_input
        gc.collect()
        return {"reply": reply}
    except Exception as e:
        gc.collect()
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)