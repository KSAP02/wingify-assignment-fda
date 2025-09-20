## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()


from crewai import Agent

# CrewAI OpenAI LLM wrapper
from langchain_openai import ChatOpenAI

from tools import search_tool, risk_assessment_tool, read_data_tool, analyze_investment_tool


### Loading LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",        # or "gpt-4o-mini" or "gpt-3.5-turbo"
    temperature=0.2,       # deterministic output
    api_key=os.getenv("OPENAI_API_KEY")  # reads from .env
)

# prepare normalized tools
tool_read = read_data_tool
tool_invest = analyze_investment_tool
tool_risk = risk_assessment_tool
tool_search = search_tool


# Creating a Senior Financial Analyst agent
financial_analyst = Agent(
    role="Senior Financial Analyst",
    goal=(
        "Analyze financial documents, assess risks, and provide clear, "
        "well-structured investment insights based on both company filings "
        "and external market information."
    ),
    backstory=(
        "You are an experienced financial analyst with expertise in corporate "
        "finance, equity research, and market analysis. You combine structured "
        "financial document review with real-time market data to produce "
        "investment recommendations. You are precise, data-driven, and "
        "transparent about uncertainties in your analysis."
    ),
    tools=[
        tool_read,
        tool_invest,
        tool_risk,
        tool_search
    ],
    llm=llm,
    memory=True,
    verbose=True,
    max_iter=3,
    max_rpm=2,
    allow_delegation=True
)

# Creating a Financial Document Verifier agent
verifier = Agent(
    role="Financial Document Verifier",
    goal=(
        "Verify whether an uploaded document is a financial report or contains "
        "financial information relevant to investment and risk analysis."
    ),
    backstory=(
        "You are a diligent compliance analyst with experience in reviewing corporate filings, "
        "financial statements, and related documents. Your job is to quickly determine "
        "whether a document is valid for financial analysis. You are detail-oriented, "
        "focused on accuracy, and strict about rejecting irrelevant files."
    ),
    tools=[tool_read],
    llm=llm,
    memory=True,
    verbose=True,
    max_iter=2,
    max_rpm=2,
    allow_delegation=False
)


# Creating an Investment Advisor agent
investment_advisor = Agent(
    role="Investment Advisor",
    goal=(
        "Provide professional, data-driven investment advice based on company filings, "
        "risk analysis, and real-time market context. Summarize key opportunities, "
        "highlight risks, and make clear recommendations such as buy/hold/sell."
    ),
    backstory=(
        "You are a seasoned financial advisor with expertise in equity research, "
        "portfolio management, and market strategy. You focus on aligning investment "
        "recommendations with financial fundamentals and market conditions. "
        "Your guidance is balanced, evidence-based, and avoids unnecessary hype. "
        "You clearly explain the reasoning behind your recommendations."
    ),
    tools=[
        tool_read,
        tool_invest,
        tool_risk,
        tool_search
    ],
    llm=llm,
    memory=True,
    verbose=True,
    max_iter=3,
    max_rpm=2,
    allow_delegation=False
)


# Creating a Risk Assessor agent
risk_assessor = Agent(
    role="Risk Assessment Specialist",
    goal=(
        "Identify and assess key financial and operational risks from company filings "
        "and market data. Provide likelihood and impact ratings, explain potential drivers, "
        "and suggest mitigation strategies."
    ),
    backstory=(
        "You are a risk management expert with experience in financial compliance, "
        "corporate governance, and market risk analysis. You specialize in reviewing "
        "company reports to uncover vulnerabilities such as regulatory, liquidity, "
        "operational, and market risks. You communicate risks clearly and recommend "
        "practical mitigation strategies to decision-makers."
    ),
    tools=[
        tool_read,
        tool_risk,
        tool_search
    ],
    llm=llm,
    memory=True,
    verbose=True,
    max_iter=3,
    max_rpm=2,
    allow_delegation=False
)