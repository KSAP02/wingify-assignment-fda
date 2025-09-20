## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()

import httpx
# from crewai_tools import tools as crewai_tools
from crewai.tools import tool
from crewai_tools import SerperDevTool

import re
import logging
from openai import OpenAI
import asyncio
import json
from typing import Optional, Any, List, Dict

## Creating search tool
search_tool = SerperDevTool()

##-------------------------- Creating Financial Document Tool --------------------------##

# Try pdfplumber -> fallback to pypdf
try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

logger = logging.getLogger(__name__)


def _clean_whitespace(text: str) -> str:
    """Normalize whitespace and remove repeated blank lines."""
    if text is None:
        return ""
    # normalize different newlines + remove extra spaces
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # collapse multiple newlines to at most two
    text = re.sub(r"\n{3,}", "\n\n", text)
    # collapse multiple spaces
    text = re.sub(r"[ \t]{2,}", " ", text)
    # strip leading/trailing whitespace
    return text.strip()


# class FinancialDocumentTool:
"""
Tool to read and clean text from PDF financial documents.

By default this returns a single string made by concatenating page texts.
Optionally you can request a list of per-page objects by setting `as_pages=True`.
"""

@tool("Read Financial Document")
def read_data_tool(path: str = "data\TSLA-Q2-2025-Update.pdf", as_pages: bool = False) -> Any:
    """
    Read plain text from a PDF at `path`.

    Args:
        path (str): Local path to the PDF file (default: 'data\TSLA-Q2-2025-Update.pdf').
        as_pages (bool): If True, return a list of per-page dictionaries.
                            If False (default), return a single concatenated string.

    Returns:
        str or List[dict]: If as_pages is False -> a single string containing the whole document
                            with page separators.
                            If as_pages is True  -> list of dicts:
                                [
                                    {"page_number": 1, "text": "...", "num_chars": 1234},
                                    ...
                                ]
    Raises:
        FileNotFoundError: if path does not exist
        RuntimeError: if no supported PDF backend is installed / parsing fails
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF not found at path: {path}")

    pages_out: List[Dict[str, Any]] = []

    # Primary: pdfplumber (better for layout + tables)
    if pdfplumber is not None:
        try:
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages):
                    raw = page.extract_text() or ""
                    text = _clean_whitespace(raw)
                    pages_out.append(
                        {"page_number": i + 1, "text": text, "num_chars": len(text)}
                    )
        except Exception as e:
            logger.warning("pdfplumber parsing failed (%s), will try pypdf fallback: %s", type(e), e)
            pages_out = []

    # Fallback: pypdf (useful when pdfplumber not installed or fails)
    if not pages_out and PdfReader is not None:
        try:
            reader = PdfReader(path)
            for i, page in enumerate(reader.pages):
                try:
                    raw = page.extract_text() or ""
                except Exception:
                    raw = ""
                text = _clean_whitespace(raw)
                pages_out.append(
                    {"page_number": i + 1, "text": text, "num_chars": len(text)}
                )
        except Exception as e:
            logger.error("pypdf parsing also failed: %s", e)
            raise RuntimeError(f"Failed to parse PDF with pdfplumber and pypdf: {e}")

    if not pages_out:
        # No parser available / no pages extracted
        raise RuntimeError("No PDF parser available or PDF parsing produced no text. "
                            "Install pdfplumber or pypdf and retry.")

    if as_pages:
        return pages_out

    # Default: return a single concatenated string with page separators
    parts: List[str] = []
    for p in pages_out:
        parts.append(f"--- PAGE {p['page_number']} ---\n{p['text']}")
    full_report = "\n\n".join(parts)
    return full_report
    

##-------------------------- Creating Investment Analysis Tool --------------------------##

def _extract_assistant_content_from_response(resp) -> str:
    """
    Robust extractor for assistant text from various OpenAI response shapes.
    Returns a string (may be empty).
    """
    # None -> empty
    if resp is None:
        return ""

    # If dict-like
    try:
        if isinstance(resp, dict):
            choices = resp.get("choices") or []
            if choices:
                first = choices[0]
                # new-style message object
                if isinstance(first, dict):
                    msg = first.get("message")
                    if isinstance(msg, dict) and "content" in msg:
                        return msg["content"] or ""
                    if "text" in first and first["text"]:
                        return first["text"]
                return str(first)
    except Exception:
        pass

    # Object-like (OpenAI model objects)
    try:
        choices = getattr(resp, "choices", None)
        if choices:
            first = choices[0]
            # try message.content
            msg = getattr(first, "message", None)
            if msg is not None:
                # msg might be dict-like or object with .content
                if isinstance(msg, dict) and "content" in msg:
                    return msg.get("content") or ""
                content_attr = getattr(msg, "content", None)
                if content_attr:
                    return content_attr
            # older SDK style: .text
            text_attr = getattr(first, "text", None)
            if text_attr:
                return text_attr
            # streaming delta style
            delta = getattr(first, "delta", None)
            if delta:
                c = getattr(delta, "content", None)
                if c:
                    return c
    except Exception:
        pass

    # Fallback to stringification
    try:
        return str(resp)
    except Exception:
        return ""
    

async def _call_openai_chat_plain(prompt: str, model: str = "gpt-4o", max_tokens: int = 1000) -> str:
    """
    Call OpenAI >=1.0.0 client and return the assistant message text directly as a string.
    Returns an "ERROR: ..." string when the client/key is missing or the call fails.
    """
    if OpenAI is None:
        return "ERROR: openai package (>=1.0.0) not installed."

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "ERROR: OPENAI_API_KEY not set in environment."

    client = OpenAI(api_key=api_key)

    def _sync_call():
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.0,
            )
            # extract assistant content robustly
            content = _extract_assistant_content_from_response(resp)
            return content if content is not None else ""
        except Exception as e:
            return f"ERROR: OpenAI call failed: {e}"

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_call)

# class InvestmentTool:

@tool("Investment Analysis Tool")
async def analyze_investment_tool(financial_document_data: str) -> str:
    """
    LLM-driven investment analysis that RETURNS A SINGLE PLAIN TEXT STRING.

    The returned string will include explicit section headers and contain:
        - ONE-LINE SUMMARY (headline)
        - DETAILED ANALYSIS (profitability, revenue trends, margins, growth, segments if present)
        - KEY FIGURES (revenue, net_income, assets, liabilities, equity with numeric values where available)
        - RATIOS (net_income_margin, debt_ratio, equity_to_assets — compute when possible)
        - RISKS (top 3-5 bullet points)
        - RECOMMENDATION (buy/hold/sell — one line)
        - CONFIDENCE (0.0-1.0)
    **It will be returned as plain text only (no JSON, no extra commentary).**

    Returns:
        str: plain-text analysis or an error string beginning with "ERROR:".
    """
    processed_data = financial_document_data

    if not isinstance(processed_data, str) or not processed_data:
        return "ERROR: financial_document_data must be a non-empty string."

    # keep your original double-space removal loop (unchanged)
    i = 0
    while i < len(processed_data):
        if processed_data[i:i+2] == "  ":
            processed_data = processed_data[:i] + processed_data[i+1:]
        else:
            i += 1

    # basic normalization
    processed_data = processed_data.replace("\r\n", "\n").strip()

    # Build a prompt that asks for a single plain-text string only:
    prompt = (
        "You are an expert financial analyst. Analyze the EXCERPT below and RETURN A SINGLE PLAIN-TEXT STRING ONLY.\n\n"
        "Requirements for the OUTPUT STRING (must follow exactly):\n"
        "  - Do NOT return JSON or code blocks. Do NOT add any meta commentary about format.\n"
        "  - Provide the following clearly labeled sections (use uppercase headers):\n"
        "      1) SUMMARY: a one-line headline summarizing the overall situation.\n"
        "      2) DETAILED ANALYSIS: a concise paragraph(s) covering profitability, revenue/margin trends, growth drivers, unusual items, segment highlights if present, and liquidity/leverage commentary.\n"
        "      3) KEY FIGURES: list revenue, net_income, assets, liabilities, equity as numeric values (no commas). If a figure isn't present, write 'N/A'. Include units if the excerpt mentions them (e.g., USD millions).\n"
        "      4) RATIOS: compute net_income_margin, debt_ratio (liabilities/assets), equity_to_assets when possible; otherwise put 'N/A'. Present percentages where appropriate.\n"
        "      5) RISKS: 3 short bullets (each on its own line, prefixed by '- ').\n"
        "      6) RECOMMENDATION: one-line 'buy'/'hold'/'sell' plus a short (1-sentence) rationale.\n"
        "      7) CONFIDENCE: a number between 0.0 and 1.0 representing how confident you are given the excerpt.\n\n"
        "Formatting rules:\n"
        "  - Use clear headers exactly as above (e.g. 'SUMMARY:', 'DETAILED ANALYSIS:', ...).\n"
        "  - Use numeric values without commas (e.g., 1200 or 22.5e9). If the excerpt uses a unit (e.g., 'USD millions'), preserve that unit next to the number.\n"
        "  - Keep the whole output concise (aim for ~8-16 lines) but include all required sections.\n"
        "  - If you cannot determine a value, write 'N/A' for that field.\n\n"
        "Now analyze this EXCERPT and produce the single plain-text string only (no extra text):\n\n"
        + processed_data[:16000]
    )

    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm_text = await _call_openai_chat_plain(prompt, model=model_name, max_tokens=1000)

    # If an error string was returned, propagate it
    if isinstance(llm_text, str) and llm_text.startswith("ERROR:"):
        return llm_text

    # Normalize whitespace and return the plain text result
    return llm_text.strip()


## Creating Risk Assessment Tool
def _normalize_whitespace(s: str) -> str:
    """Minimal normalization so output is tidy."""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s.strip()

# class RiskTool:
    
@tool("Risk Assessment Tool")
async def risk_assessment_tool(financial_document_data: str) -> str:
    """
    Create a risk assessment string from the provided financial document text.

    Returns a single plain-text string containing these sections (exact headers):
        - RISK HEADLINE: one-line headline
        - TOP RISKS: 3-6 bullets
        - RISK DRIVERS: concise paragraphs explaining root causes
        - LIKELIHOOD & IMPACT: short table / lines "Risk | Likelihood | Impact"
        - RECOMMENDED MITIGATIONS: 3-6 bullets
        - MONITORING / KPIs: 3 bullets of measurable signals to watch
        - CONFIDENCE: number between 0.0 and 1.0

    If the OpenAI helper returns an error string beginning with "ERROR:", that string is returned unchanged.
    """
    # Keep original cleaning loop you provided
    processed_data = financial_document_data

    if not isinstance(processed_data, str) or not processed_data:
        return "ERROR: financial_document_data must be a non-empty string."

    i = 0
    while i < len(processed_data):
        if processed_data[i:i+2] == "  ":
            processed_data = processed_data[:i] + processed_data[i+1:]
        else:
            i += 1

    # Minimal normalization
    processed_data = processed_data.replace("\r\n", "\n").strip()

    # Prompt: ask for a single plain-text string with exact headers
    prompt = (
        "You are an experienced risk analyst focused on corporate financial risk.\n\n"
        "Analyze the EXCERPT below and RETURN A SINGLE PLAIN-TEXT STRING ONLY (no JSON, no code blocks, no meta commentary).\n\n"
        "The output MUST contain the following sections, using the EXACT UPPERCASE HEADERS shown (each header followed by its content):\n\n"
        "RISK HEADLINE:\n"
        "  - a one-line headline summarizing the top-level risk posture.\n\n"
        "TOP RISKS:\n"
        "  - 3 to 6 short bullets (each on its own line, prefixed by '- ').\n\n"
        "RISK DRIVERS:\n"
        "  - 1-3 concise paragraphs describing root causes and contextual drivers (market, operations, regulatory, supply, liquidity etc.).\n\n"
        "LIKELIHOOD & IMPACT:\n"
        "  - For each top risk, provide a single-line entry: 'RiskName | Likelihood: Low/Medium/High | Impact: Low/Medium/High'.\n\n"
        "RECOMMENDED MITIGATIONS:\n"
        "  - 3 to 6 actionable mitigation bullets (each on its own line, prefixed by '- ').\n\n"
        "MONITORING / KPIs:\n"
        "  - 3 short bullets describing measurable signals to watch.\n\n"
        "CONFIDENCE:\n"
        "  - A single number between 0.0 and 1.0 representing your confidence in this assessment given only the excerpt.\n\n"
        "Formatting rules (must follow):\n"
        "  - Do NOT include any other sections or trailing commentary beyond the required headers and their content.\n"
        "  - If a value cannot be determined, write 'N/A' (for example in LIKELIHOOD & IMPACT use 'N/A').\n"
        "  - Keep the output concise and focused; prefer clarity over verbosity.\n\n"
        "Now analyze this EXCERPT and produce the single plain-text string only:\n\n"
        + processed_data[:14000]  # truncate to keep tokens bounded
    )

    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm_text = await _call_openai_chat_plain(prompt, model=model_name, max_tokens=900)

    # pass through errors from helper
    if isinstance(llm_text, str) and llm_text.startswith("ERROR:"):
        return llm_text

    # Normalize whitespace before returning (use existing helper if present)
    try:
        normalized = _normalize_whitespace(str(llm_text))
    except Exception:
        # fallback minimal normalization
        normalized = str(llm_text).replace("\r\n", "\n").strip()

    return normalized