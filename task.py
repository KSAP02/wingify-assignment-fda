## Importing libraries and files
from crewai import Task

from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from tools import search_tool, risk_assessment_tool, read_data_tool, analyze_investment_tool

# prepare normalized tools
tool_read = read_data_tool
tool_invest = analyze_investment_tool
tool_risk = risk_assessment_tool
tool_search = search_tool

# Creating a task to analyze a financial document
analyze_financial_document = Task(
    description=(
        "Analyze the provided financial document and respond to the user's query: {query}. "
        "Use the financial report as the primary source, supported by additional context if needed. "
        "Identify key financial metrics, summarize overall performance, and highlight significant "
        "trends or anomalies. Provide investment-relevant insights that directly address the user's request."
    ),
    expected_output=(
        "A clear, structured analysis of the financial document that includes:\n"
        "- Summary of key financial metrics (revenue, net income, margins, etc.)\n"
        "- Notable strengths or weaknesses in performance\n"
        "- Relevant market or industry context\n"
        "- Investment implications (if applicable)\n"
        "Output should be concise, professional, and fact-based."
    ),
    agent=financial_analyst,
    tools=[tool_read],
    async_execution=False,
)

# Creating an investment analysis task
investment_analysis = Task(
    description=(
        "Using the financial document data, provide an investment analysis in response to the user's query: {query}. "
        "Focus on key performance indicators such as revenue, profit margins, cash flow, and growth outlook. "
        "Combine insights from the document with relevant market or industry trends to make a recommendation. "
        "Highlight both opportunities and risks, and ensure that the analysis is evidence-based."
    ),
    expected_output=(
        "A professional investment analysis that includes:\n"
        "- Key financial highlights (revenue, margins, profitability, growth)\n"
        "- Observed trends or anomalies in the data\n"
        "- Market or industry context from external sources (if relevant)\n"
        "- A clear investment recommendation (Buy / Hold / Sell) with rationale\n"
        "- A confidence score (0.0–1.0) indicating certainty of the recommendation"
    ),
    agent=investment_advisor,
    tools=[
        tool_read,
        tool_invest,
        tool_search
    ],
    async_execution=False,
)

# Creating a risk assessment task
risk_assessment = Task(
    description=(
        "Perform a comprehensive risk assessment based on the financial document in response to the user's query: {query}. "
        "Identify financial, operational, regulatory, and market risks. "
        "Estimate likelihood and potential impact, explain key risk drivers, and suggest practical mitigations. "
        "Incorporate external context if relevant (e.g., regulatory changes, supply chain news)."
    ),
    expected_output=(
        "A structured risk assessment that includes:\n"
        "- A clear risk headline summarizing overall risk posture\n"
        "- 3–6 specific risks identified (financial, operational, regulatory, market)\n"
        "- Likelihood & impact assessment for each risk (Low / Medium / High)\n"
        "- Explanation of underlying drivers for each risk\n"
        "- Recommended mitigations (actionable steps)\n"
        "- Monitoring indicators or KPIs to track risks\n"
        "- Confidence score (0.0–1.0) representing certainty of the analysis"
    ),
    agent=risk_assessor,
    tools=[
        tool_read,
        tool_risk,
        tool_invest
    ],
    async_execution=False,
)

# Creating a verification task
verification = Task(
    description=(
        "Verify whether the uploaded document is a valid financial document relevant to analysis. "
        "Check if it contains financial information such as revenue, net income, balance sheets, "
        "or other corporate financial data. If the document is unrelated (e.g., personal notes, grocery list), "
        "clearly state that it is not a financial report."
    ),
    expected_output=(
        "A professional verification result that includes:\n"
        "- A clear Yes/No decision on whether the document is a financial report\n"
        "- If Yes: a brief explanation of why (e.g., mentions revenue, income, balance sheet)\n"
        "- If No: a short explanation of why it is not suitable for financial analysis\n"
        "- Optional: confidence score (0.0–1.0)"
    ),
    agent=verifier,
    tools=[tool_read],
    async_execution=False
)
