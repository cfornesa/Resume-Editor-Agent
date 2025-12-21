import os
import gc
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI()

# 1. KEEP CORS GLOBAL (Needed for the OPTIONS check)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. HEALTH CHECK (Already good, kept here)
@app.get("/")
async def health_check():
    return {"status": "ok", "message": "DeepSeek Resume Agent API is running"}

class ResumeRequest(BaseModel):
    occupation: str
    industry: str
    job_description: str
    name: str
    contact: str
    summary: str
    skills: str
    experience: str
    education: str
    awards: str
    history: List[Dict[str, Any]] = []

# 3. DEFER PROMPT CONSTRUCTION
def get_resume_system_prompt():
    GOALS = "..." # (Paste your full GOALS string here)
    ACTIONS = "..." # (Paste your full ACTIONS string here)
    INFORMATION = "..." # (Paste your full INFORMATION string here)
    LANGUAGE = "..." # (Paste your full LANGUAGE string here)
    return f"{GOALS}\n{ACTIONS}\n{INFORMATION}\n{LANGUAGE}"

@app.post("/chat")
async def process_resume(req: ResumeRequest):
    # 4. DEFERRED OPENAI IMPORT
    from openai import OpenAI

    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        return {"error": "DEEPSEEK_API_KEY is not configured"}

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    user_payload = f"""
    Desired Occupation: {req.occupation}
    Industry: {req.industry}
    Job Description: {req.job_description}
    Name: {req.name}
    Contact: {req.contact}
    Summary: {req.summary}
    Skills: {req.skills}
    Experience: {req.experience}
    Education: {req.education}
    Awards/Certificates: {req.awards}
    """

    system_prompt = get_resume_system_prompt()
    messages = [{"role": "system", "content": system_prompt}] + req.history
    messages.append({"role": "user", "content": user_payload})

    try:
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=messages
        )

        # 5. GARBAGE COLLECTION
        res_content = response.choices[0].message.content
        del messages
        gc.collect()

        return {"reply": res_content}
    except Exception as e:
        gc.collect()
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)