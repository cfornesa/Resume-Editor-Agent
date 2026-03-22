import os
import re
import gc
from mistralai import Mistral
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

# Redact personally identifiable information before sending to the agent
def redact_pii(text: str) -> str:
    PII_PATTERNS = {
        "EMAIL":   r'[\w\.-]+@[\w\.-]+\.\w+',
        "PHONE":   r'\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        "SSN":     r'\b(?!666|000|9\d{2})\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}\b',
        "ADDRESS": r'\d{1,5}\s\w+.\s(\b\w+\b\s){1,2}\w+,\s\w+,\s[A-Z]{2}\s\d{5}'
    }
    for label, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"[{label}_REDACTED]", text, flags=re.IGNORECASE)
    return text

# Initialize the Mistral client
def get_client():
    api_key = os.environ.get('MISTRAL_API_KEY')
    if not api_key:
        raise ValueError("MISTRAL_API_KEY missing from environment.")
    return Mistral(api_key=api_key)

# Strip markdown formatting from agent responses
def strip_markdown(text: str) -> str:
    text = re.sub(r'#{1,6}\s*', '', text)                    # headers
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)    # bold/italic
    text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)      # underline
    text = re.sub(r'[–—]', '-', text)                        # normalize unicode dashes to hyphens
    text = re.sub(r'[\U00002600-\U000027BF]', '', text)      # common symbols/emoji block
    text = re.sub(r'[\U0001F000-\U0001FFFF]', '', text)      # extended emoji block
    text = re.sub(r'\n{3,}', '\n\n', text)                   # excess blank lines
    return text.strip()

# Parse the assistant reply from agent response outputs
def parse_reply(response) -> str:
    for output in response.outputs:
        if hasattr(output, "role") and output.role == "assistant":
            content = output.content
            if isinstance(content, list):
                return strip_markdown(content[0].text)
            return strip_markdown(content)
    return ""

# Phase 1: Build an initial resume from structured form data
def build_resume(resume_data: str) -> dict:
    client = get_client()
    agent_id = os.environ.get('AGENT_ID')
    if not agent_id:
        return {"reply": "Error: AGENT_ID missing from environment.", "phase": "build"}

    safe_input = redact_pii(resume_data)

    try:
        response = client.beta.conversations.start(
            agent_id=agent_id,
            inputs=[{
                "role": "user",
                "content": (
                    "BUILD MODE. Construct a complete professional resume from the data below. "
                    "Do not add any skills, tools, or experience not explicitly listed.\n\n"
                    f"{safe_input}"
                )
            }]
        )
        reply = parse_reply(response).strip()
        del safe_input
        gc.collect()
        return {"reply": reply or "Error: Empty response from agent.", "phase": "build"}
    except Exception as e:
        gc.collect()
        return {"reply": f"System Error: {str(e)}", "phase": "build"}

# Phase 2: Fine-tune the resume based on user chat instructions and prior history
def edit_resume(current_resume: str, user_message: str, history: List[Dict]) -> dict:
    client = get_client()
    agent_id = os.environ.get('AGENT_ID')
    if not agent_id:
        return {"reply": "Error: AGENT_ID missing from environment.", "phase": "edit"}

    # Build conversation inputs from history, then append the current edit request
    inputs = []
    for entry in history:
        inputs.append({
            "role": entry.get("role", "user"),
            "content": entry.get("content", "")
        })
    inputs.append({
        "role": "user",
        "content": (
            "EDIT MODE. Apply only the change requested below to the resume. "
            "Return the full updated resume.\n\n"
            f"Current Resume:\n{current_resume}\n\n"
            f"Edit Request: {user_message}"
        )
    })

    try:
        response = client.beta.conversations.start(
            agent_id=agent_id,
            inputs=inputs
        )
        reply = parse_reply(response).strip()
        gc.collect()
        return {"reply": reply or "Error: Empty response from agent.", "phase": "edit"}
    except Exception as e:
        gc.collect()
        return {"reply": f"System Error: {str(e)}", "phase": "edit"}
