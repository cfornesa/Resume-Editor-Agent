# DeepSeek Resume Agent

## Overview
A FastAPI-based API that uses DeepSeek's Reasoner model to help job seekers tailor their resumes to match job descriptions. The agent follows the GAIL framework (Goals, Actions, Information, Language) for structured responses.

## Project Structure
- `main.py` - Main FastAPI application with the /chat endpoint
- `pyproject.toml` - Python dependencies managed by uv

## API Endpoints
- `GET /` - Health check endpoint
- `POST /chat` - Resume processing endpoint

### POST /chat Request Body
```json
{
  "occupation": "Software Engineer",
  "industry": "Technology",
  "job_description": "Job posting text...",
  "name": "John Doe",
  "contact": "john@email.com | (555) 123-4567",
  "summary": "Professional summary...",
  "skills": "Python, JavaScript, etc.",
  "experience": "Work history...",
  "education": "Degree information...",
  "awards": "Certifications and awards...",
  "history": []
}
```

## Environment
- Python 3.11
- FastAPI with uvicorn
- OpenAI Python SDK (configured for DeepSeek API)

## Required Secrets
- `DEEPSEEK_API_KEY` - API key from platform.deepseek.com

## Deployment
Configured for autoscale deployment on Replit.
