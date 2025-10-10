
---
# 🧩 Project Changes — Financial Document Analyzer (CrewAI + FastAPI)

## Date: 10th October 2025

---

## 🔧 1. Async I/O and Tool Adjustments

### ➤ Previous Issue
Earlier, several tools (`read_data_tool`, `analyze_investment_tool`, `create_risk_assessment_tool`, etc.) were defined as `async` functions or used `asyncio.run()` internally.  
This caused errors like:
```

RuntimeWarning: coroutine 'read_data_tool' was never awaited
asyncio.run() cannot be called from a running event loop

```

These errors happened because **FastAPI** already operates inside an asynchronous event loop.  
Calling another event loop (`asyncio.run()`) inside it leads to runtime conflicts.

### ✅ Fix Implemented
- Removed all internal `async` definitions and event loop calls from tool functions.
- All tools now run as **standard synchronous (`def`) functions** returning clean strings.
- OpenAI calls inside the tools were updated to use the latest `openai` client (≥1.0.0) in synchronous mode.
- This eliminated nested coroutine issues while maintaining compatibility with CrewAI.

### 🧠 Reason for Change
CrewAI manages asynchrony internally, so using `async` within tools created unnecessary complexity and runtime overlap.  
Now, tools:
- Execute sequentially under CrewAI control.
- Are simpler to maintain.
- Return predictable, synchronous outputs.

---

## 🧰 2. Tool Registration & Task Integration

### ➤ Previous Issue
Agents were defined with multiple tools (`read`, `investment`, `risk`, `search`),  
but CrewAI still raised errors like:
```

Action 'Investment Analysis Tool' don't exist, these are the only available Actions: ...

````

This occurred because CrewAI does **not** automatically expose agent-level tools to tasks.  
Each **Task** must explicitly include the tools it needs.

### ✅ Fix Implemented
- Updated all task definitions to explicitly include all relevant tools:
  ```python
  tools=[
      read_data_tool,
      analyze_investment_tool,
      create_risk_assessment_tool,
      search_tool
  ]

* Now, when a Task runs, the associated agent has access to all these tools.
* The LLM can dynamically select and call the appropriate tool depending on the query context.

### 🧠 Reason for Change

CrewAI isolates tool access per task to maintain control and reproducibility.
Even if tools are attached to an agent, they must still be **declared in the Task** to be registered in the runtime environment.

Now:

* Agents can fully utilize multiple tools in one workflow.
* Multi-step reasoning and data enrichment (read → analyze → assess → search) work end-to-end.

---

## ⚙️ 3. PDF Warning Messages Clarified

### ➤ Symptom

During document reading, the console showed repeated warnings:

```
Cannot set gray non-stroke color because /'P0' is an invalid float value
Cannot set gray non-stroke color because /'P1' is an invalid float value
```

### 🧠 Explanation

These are harmless internal warnings from the PDF parser (`pypdf` or `pdfplumber`).
They appear when the PDF includes invalid color space tokens (like `/P0`, `/P1`) that don’t affect text extraction.


### 🔒 Result

* Text extraction still works correctly.
* No change in actual functionality or accuracy.

---


| **Area**                         | **Description**                                                            | **Outcome**                                 |
| -------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------- |
| **Async tools removed**          | Converted async tools to synchronous ones and removed event loop conflicts | Stable tool execution                       |
| **Task-level tool registration** | Explicitly added all tools inside each Task                                | Agents can now use multiple tools logically |
| **PDF warnings**         | Suppressed harmless `pypdf` color warnings                                 |no functionality loss         |

---

### 🏁 Result

After these changes:

* CrewAI tools execute correctly under FastAPI without async issues.
* Agents can leverage all assigned tools in proper sequence.

The overall CrewAI workflow (Verifier → Financial Analyst → Investment Advisor → Risk Assessor) now runs smoothly with complete task–tool integration.


---
