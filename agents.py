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
# Creating a Senior Financial Analyst agent
financial_analyst = Agent(
    role="Senior Financial Analyst",
    goal=(
        "Analyze financial documents thoroughly, evaluate investment potential, "
        "assess associated risks, and provide final recommendations backed by "
        "real-time market insights."
    ),
    backstory=(
        "You are a highly experienced financial analyst with deep expertise in "
        "equity research, corporate finance, and risk evaluation.\n\n"
        "When performing your analysis, you must always follow this exact sequence "
        "using the available tools:\n\n"
        
        "1) **Read Financial Document Tool** — Use this first to extract and clean "
        "the text from the provided PDF. Do not skip this step.\n\n"
        "2) **Investment Analysis Tool** — Once you have the extracted text, use this "
        "tool to perform a structured LLM-driven investment analysis. Include summaries, "
        "key figures, profitability, growth insights, and clear recommendations from the read financial document tool result.\n\n"
        "3) **Risk Assessment Tool** — After investment analysis, call this tool to "
        "generate a risk profile of the company or financial report, identifying major "
        "threats and opportunities.\n\n"
        "4) **Search Tool (Serper)** — Finally, use this to check for any recent "
        "market events, news, or macro-economic updates relevant to the company or "
        "industry context. Summarize key findings.\n\n"
        "After using all tools, synthesize a single, cohesive plain-text report that "
        "includes:\n"
        "• A concise **Summary** of findings\n"
        "• Detailed **Investment Analysis**\n"
        "• **Risk Assessment** insights\n"
        "• **Recent Market Context** from the search tool\n"
        "• And a final **Investment Recommendation** (buy/hold/sell)\n\n"
        "Never skip any step or call fewer than three tools in your analysis process. "
        "If one fails, continue with the remaining steps."
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
    max_iter=6,  # allow multiple reasoning/tool-use cycles
    max_rpm=5,
    allow_delegation=False
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
        "Provide accurate, data-driven investment advice by combining financial document analysis, "
        "risk evaluation, and current market insights. Use all available tools to develop balanced "
        "buy/hold/sell recommendations supported by concrete reasoning."
    ),
    backstory=(
        "You are a seasoned investment advisor and market strategist specializing in equity research, "
        "portfolio optimization, and asset allocation. You rely on quantitative fundamentals, "
        "qualitative assessments, and live market context to guide your investment calls.\n\n"
        "Whenever you handle a query, **you must always use the tools in the following order**:\n\n"
        "1) **Read Financial Document Tool** — Start here. Load and extract the clean text content "
        "from the provided PDF or financial file. Do not skip this step.\n\n"
        "2) **Investment Analysis Tool** — Next, analyze the extracted text to evaluate profitability, "
        "growth trends, and valuation metrics take the output from read financial document as input for this tool"
        ". Identify strengths, weaknesses, and key investment factors.\n\n"
        "3) **Risk Assessment Tool** — Then, assess associated risks. Look for financial, operational, "
        "and market-related vulnerabilities that could affect performance.\n\n"
        "4) **Search Tool (Serper)** — Finally, check for relevant real-time data, news, or events "
        "influencing the company, industry, or macroeconomic environment.\n\n"
        "Once all tools are used, synthesize the findings into a **clear and professional investment report** "
        "that includes:\n"
        "• Executive Summary\n"
        "• Investment Highlights\n"
        "• Risk Overview\n"
        "• Market Context (from search)\n"
        "• Final Recommendation (Buy / Hold / Sell) with a short rationale.\n\n"
        "You are expected to use *every* tool in that order unless one fails. If a tool produces an error, "
        "continue the process using the remaining tools and mention that the data was incomplete."
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
    max_iter=6,  # increased so it can call all tools and synthesize results
    max_rpm=5,
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