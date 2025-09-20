from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import os
import uuid
import asyncio
from datetime import datetime

from crewai import Crew, Process

# Import agents
from agents import verifier, financial_analyst, investment_advisor, risk_assessor

# Import tasks
from task import verification, analyze_financial_document, investment_analysis, risk_assessment


app = FastAPI(title="Financial Document Analyzer")


def run_crew(query: str, file_path: str = "data\TSLA-Q2-2025-Update.pdf"):
    """Run the full Crew pipeline with all agents and tasks."""
    financial_crew = Crew(
        agents=[verifier, financial_analyst, investment_advisor, risk_assessor],
        tasks=[verification, analyze_financial_document, investment_analysis, risk_assessment],
        process=Process.sequential,  # tasks run in order
    )

    # Run Crew with input variables
    result = financial_crew.kickoff(inputs={"query": query, "file_path": file_path})
    return result


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Financial Document Analyzer API is running"}


@app.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights")
):
    """Analyze an uploaded financial document and return structured results."""

    # Generate unique file path
    # file_id = str(uuid.uuid4())
    os.makedirs("data", exist_ok=True)
    file_path = f"data\TSLA-Q2-2025-Update.pdf"

    try:
        # Save uploaded file
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Default query if empty
        if not query or query.strip() == "":
            query = "Analyze this financial document for investment insights"

        # Run full Crew pipeline
        response = run_crew(query=query.strip(), file_path=file_path)

        # Save result to output directory
        os.makedirs("outputs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"outputs/analysis_{timestamp}.txt"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(str(response))

        return {
            "status": "success",
            "query": query,
            "analysis": str(response),
            "file_processed": file.filename,
            "output_file": output_path,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing financial document: {str(e)}")

    finally:
        # Cleanup uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass  # ignore cleanup errors


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
