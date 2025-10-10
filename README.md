# 📊 Financial Document Analyzer

An AI-powered FastAPI + CrewAI application that reads financial documents, verifies them, performs investment analysis, and generates risk assessments using LLMs and external tools (e.g., Serper for search).

The system uses:

* **FastAPI** for serving API endpoints.
* **CrewAI** to orchestrate multiple agents and tasks.
* **Custom tools** (PDF Reader, Investment Analysis, Risk Assessment, Search).
* **OpenAI LLMs** for intelligent financial reasoning.

---

## 🚀 Features

* Upload and analyze **financial documents** (PDFs).
* Agents:

  * **Verifier** → checks if a document is financial.
  * **Financial Analyst** → performs core analysis.
  * **Investment Advisor** → provides actionable recommendations.
  * **Risk Assessor** → identifies risk factors.
* Task orchestration via **CrewAI** (`Process.sequential`).
* Output stored in `output/` with timestamp.
* Includes **test client script (`client.py`)** for easy local testing.

---

## ⚙️ Setup Instructions

### 1. Clone and install

```bash
git clone <repo-url>
cd financial-document-analyzer-debug
python -m venv fda_venv
source fda_venv/bin/activate   # Linux/Mac
fda_venv\Scripts\activate     # Windows

pip install -r requirements-crewai.txt
```

### 2. Environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-key
SERPER_API_KEY=your-serper-key
```

### 3. Run FastAPI server

```bash
# Either:
python main.py

# Or (preferred for reload):
uvicorn main:app --reload
```

Server will be running at:
👉 `http://localhost:8000`

---

## 📡 API Documentation

### Health check

```http
GET /
```

**Response:**

```json
{"message": "Financial Document Analyzer API is running"}
```

---

### Analyze financial document

```http
POST /analyze
```

**Form-data parameters:**

* `file`: PDF file (UploadFile).
* `query`: (optional) user query, default = `"Analyze this financial document for investment insights"`.

**Example with `curl`:**

```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@data\TSLA-Q2-2025-Update.pdf" \
  -F "query=Summarize the Q2 earnings"
```

**Response:**

```json
{
  "status": "success",
  "query": "Summarize the Q2 earnings",
  "analysis": "... full multi-agent analysis ...",
  "file_processed": "data/TSLA-Q2-2025-Update.pdf",
  "output_file": "output/analysis_20250920_abc123.txt"
}
```

---

## 🐛 Bugs Found & Fixes

1. **Dependency conflicts (`crewai`, `crewai-tools`, `embedchain`)**

   * Conflict due to mismatched `chromadb` and `pypdf` versions.
   * 🔧 **Fix:** Pinned only `crewai` and `crewai-tools` versions. Left other packages unpinned so `pip` could auto-resolve.

2. **Tool integration errors**

   * Error:

     ```
     Input should be a valid dictionary or instance of BaseTool
     ```
   * Cause: Passing raw functions or class methods into `Agent(tools=...)`.
   * 🔧 **Fix:** Converted class methods into standalone functions with `@tool` decorator OR normalized them into dicts (`{"name": ..., "arun": ...}`).

3. **`asyncio.run()` inside running event loop**

   * Error:

     ```
     asyncio.run() cannot be called from a running event loop
     ```
   * Cause: Tools tried to call `asyncio.run()` inside FastAPI’s async loop.
   * 🔧 **Fix:** Used `async def` + `await loop.run_in_executor(...)` to handle blocking I/O (PDF parsing).

4. **Risk Tool `self` argument issue**

   * Error:

     ```
     risk_assessment_tool() missing 1 required positional argument: 'self'
     ```
   * Cause: Tool defined as class method, so Python expected `self`.
   * 🔧 **Fix:** Refactored tools into standalone functions or `@staticmethod`.

5. **FastAPI reload warning**

   * Warning:

     ```
     You must pass the application as an import string to enable 'reload' or 'workers'.
     ```
   * Cause: Used `uvicorn.run(app, reload=True)` inside `main.py`.
   * 🔧 **Fix:** Run either `python main.py` (no reload) or `uvicorn main:app --reload`.

---

## 🧪 Testing the API

Included a `client.py` script for easy testing.

### Usage:

```bash
python client.py
```

**client.py**:

* Automatically loads `data\TSLA-Q2-2025-Update.pdf`.
* Sends a POST request to `/analyze`.
* Prints JSON response with analysis and output file path.

This eliminates the need for a frontend during development.

---

## 📚 Learnings

* **CrewAI agents & tasks**

  * Agents represent roles (Analyst, Verifier, Advisor, Risk Assessor).
  * Tasks orchestrate workflows sequentially with assigned agents and tools.
  * Tools must be in a valid format (BaseTool/dict) for Pydantic validation.

* **Asynchronous programming**

  * Tools don’t *have* to be async.
  * But in FastAPI + CrewAI context, async prevents blocking.

* **Dependency management**

  * CrewAI evolves fast, so pinning only core dependencies (`crewai`, `crewai-tools`) avoids most version hell.
  * Other deps (`pypdf`, `httpx`, `fastapi`) can float.

* **Testing strategy**

  * Built `client.py` to simulate frontend.
  * Debugged tools in isolation with `debug_normalized_tools.py`.
  * Used `output/` directory for persisted results → easy to validate outputs across runs.

---

## 📂 Project Structure

```
financial-document-analyzer-debug/
│── main.py                  # FastAPI + Crew runner
│── agents.py                # CrewAI agents
│── tasks.py                 # CrewAI tasks
│── tools.py                 # Custom tools (PDF, Investment, Risk, Search)
│── client.py                # Test client script
│── data/                    # Sample financial documents
│── output/                  # Analysis outputs
│── requirements-crewai.txt
│── .env
│── README.md
```

---

## 🙌 Acknowledgements

* [CrewAI](https://github.com/joaomdmoura/crewai)
* [FastAPI](https://fastapi.tiangolo.com/)
* [OpenAI](https://platform.openai.com/)

---
