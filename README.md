# 🧠 Project: AutoResearcher (Agentic AI) — Rebuilt from Scratch

### 🎯 Goal (keep this crystal clear)

> Build an **agentic AI system** that autonomously plans, searches, evaluates sources, synthesizes information, and produces a structured research report.

Not a chatbot.
Not “ask → answer”.
A **goal-driven agent**.

---

## 🏗️ High-Level Architecture (simple but powerful)

```
User Topic
   ↓
Planner Agent
   ↓
Task Queue (state)
   ↓
Search Agent → Scraper Agent → Evaluator Agent
   ↓
Vector Store (Memory)
   ↓
Synthesis Agent
   ↓
Report Generator (Markdown / PDF)
```

Each box = **agent or tool**, not a prompt dump.

---

## 🧩 Core Agents (start with THESE 4)

### 1️⃣ Planner Agent (the brain)

**Input:** Research topic
**Output:** Ordered list of tasks

Example:

```json
[
  "Find 5 authoritative sources on topic",
  "Extract key facts and statistics",
  "Identify competing viewpoints",
  "Summarize findings",
  "Generate final report"
]
```

👉 This is what makes it **agentic**.

---

### 2️⃣ Search + Scrape Agent

**Responsibilities**

* Query web search API (Tavily / SerpAPI / DuckDuckGo)
* Select *which links are worth reading*
* Scrape clean text

**Important**
Do NOT scrape everything.
Have the agent **decide** which links to follow.

---

### 3️⃣ Evaluator Agent (🔥 huge differentiator)

This agent:

* Scores sources on:

  * credibility
  * recency
  * relevance
* Discards weak sources

Example output:

```json
{
  "url": "...",
  "credibility": 0.82,
  "reason": "Peer-reviewed, recent, domain authority"
}
```

Most people skip this. You won’t.

---

### 4️⃣ Synthesis Agent

* Pulls top chunks from vector store
* Writes a **structured report**
* Sections:

  * Overview
  * Key findings
  * Conflicting viewpoints
  * Conclusion
  * References

---

## 🧠 Memory (don’t overcomplicate)

Start with:

* **ChromaDB or FAISS**
* Store:

  * chunk text
  * source URL
  * evaluator score

Later you can add:

* reflection memory
* failed paths

---

## 🛠️ Tech Stack (resume-friendly & sane)

### Backend

* **Python**
* **FastAPI**
* **LangGraph** (IMPORTANT → explicit agent state)
* **Pydantic** for state schemas

### AI

* OpenAI / Gemini / Claude
* Embeddings (OpenAI or local)

### Frontend 

* Streamlit OR Next.js
* Keep UI dead simple initially

---
We’ll get you building *today* 🚀
