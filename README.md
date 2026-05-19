# AI-Agent
To learn AI-Agent

## Setup

Create and activate the virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Set `LLM_API_KEY` in `.env`, then run:

```powershell
python src\main.py
```
