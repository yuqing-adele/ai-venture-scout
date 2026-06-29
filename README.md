# AI Venture Scout

**A multi-agent AI system that researches startup opportunities and generates investment-grade analysis reports.**

Built with LangGraph, Claude API (Anthropic), and Tavily Search — designed to help technical founders in Shenzhen identify the most viable deep-tech products to build.

---

## What It Does

You describe your team and constraints in one sentence:

> "5-person team in Shenzhen, 2M RMB budget, focus on AI & robotics hardware."

The system spins up **10+ specialized AI agents** that run in parallel to research markets, patents, investment trends, supply chains, and policies. It then scores every opportunity and delivers a complete report — with citations.

**Sample output (Top 5 recommendations):**

| Rank | Product Direction | Score |
|------|------------------|-------|
| 1 | Edge AI Industrial Vision System | 87/100 |
| 2 | AI Camera / Vision Module | 82/100 |
| 3 | AMR Core Control System | 78/100 |
| 4 | UAV + AI Vision System | 74/100 |
| 5 | Lightweight Embodied Robot | 71/100 |

Each recommendation includes: market size, 5-year CAGR, Shenzhen supply chain feasibility, BOM cost estimate, certification requirements, applicable government subsidies, competitive landscape, and build timeline — all with source citations.

---

## System Architecture

```
User Input
    │
    ▼
Direction Planner
    │
    ├── Technology Scout ──┐
    ├── Market Agent       │
    ├── Patent Agent       │  (parallel)
    ├── Investment Agent   │
    ├── Policy Agent       │
    └── Competitor Agent ──┘
                │
                ▼
        Product Generator
         (20–30 candidates)
                │
         ★ Human Checkpoint 1 ★  ← user filters directions
                │
    ┌───────────┴───────────┐
    Deep Research × N products  (parallel, 5 dimensions each)
    Market | Tech | Competition | Supply Chain | Policy
    └───────────────────────┘
                │
         Evaluation Agent
          (100-point scoring)
                │
         ★ Human Checkpoint 2 ★  ← user adjusts weights
                │
          Report Agent
                │
         Final Report (Markdown + PDF)
```

**Key design principles:**
- Every agent outputs structured JSON with `citation` objects — no hallucinated numbers
- `tool_use` mode enforces valid schema output from Claude
- Parallel execution via LangGraph `Send` API cuts research time from ~70 min to ~12 min
- Human-in-the-loop checkpoints via LangGraph `interrupt()`
- All Tavily searches cached (24–72h TTL) to minimize API costs

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Agent Orchestration | [LangGraph](https://langchain-ai.github.io/langgraph/) |
| LLM | Claude claude-sonnet-4-6 / Haiku 4.5 (Anthropic) |
| Web Search | [Tavily API](https://tavily.com) |
| Academic Data | [OpenAlex API](https://openalex.org) + ArXiv |
| Data Validation | Pydantic v2 |
| CLI | Rich |
| PDF Export | WeasyPrint |

---

## Project Structure

```
ai-venture-scout/
├── agents/
│   ├── base.py              # tool_use wrapper, JSON cleaning, retry
│   ├── _schemas.py          # JSON Schema definitions for all agents
│   ├── direction_planner.py
│   ├── technology_scout.py
│   ├── market_agent.py
│   ├── patent_agent.py
│   ├── investment_agent.py
│   ├── policy_agent.py
│   ├── competitor_agent.py
│   ├── product_generator.py
│   ├── deep_research.py     # 5 dimensions in parallel threads
│   ├── evaluation_agent.py  # 100-point scoring rubric
│   └── report_agent.py
├── models/
│   └── schemas.py           # Pydantic models for all data structures
├── workflow/
│   └── graph.py             # LangGraph StateGraph + human checkpoints
├── tools/
│   ├── tavily_tool.py       # search with domain targeting + caching
│   └── openalex_tool.py
├── main.py                  # interactive CLI
├── run_full.py              # auto-run (for testing)
├── export_pdf.py            # Markdown → PDF
└── test_all.py              # 12/12 unit tests
```

---

## Setup

**Requirements:** Python 3.11+, conda or virtualenv

```bash
# 1. Clone and create environment
git clone https://github.com/yuqing-adele/ai-venture-scout.git
cd ai-venture-scout
conda create -n venture-scout python=3.13
conda activate venture-scout
pip install -r requirements.txt

# 2. Configure API keys
cp .env.example .env
# Edit .env:
# ANTHROPIC_API_KEY=sk-ant-...    → https://console.anthropic.com
# TAVILY_API_KEY=tvly-...         → https://tavily.com (free tier: 1000/month)
# CONTACT_EMAIL=your@email.com   → for OpenAlex rate limit (optional)
```

**API cost per full run:** ~$0.10–0.20 USD

---

## Usage

### Interactive mode (with human checkpoints)

```bash
python main.py
```

You'll be prompted for your team background, then see two review points during the analysis.

### Auto-run mode

Edit `USER_INPUT` in `run_full.py`, then:

```bash
python run_full.py
```

### Export report to PDF

```bash
python export_pdf.py                      # converts latest report
python export_pdf.py reports/report_X.md  # specific report
```

---

## Scoring Rubric

Each startup opportunity is scored out of 100 across 5 dimensions:

| Dimension | Weight | Key Criteria |
|-----------|--------|-------------|
| Market Opportunity | 30 pts | TAM size, 5yr CAGR, demand authenticity |
| Shenzhen Feasibility | 25 pts | LCSC component availability, local ecosystem, certification complexity |
| Small Team Executability | 20 pts | MVP timeline, budget needed, tech fit |
| Competitive Landscape | 15 pts | Big tech threat, market whitespace |
| Market Timing | 10 pts | TRL maturity, policy tailwinds |

---

## Data Sources

| Source | Data Type | Access |
|--------|-----------|--------|
| Tavily API | Web search, news, reports | Free 1K/mo |
| OpenAlex | Academic papers, citation trends | Free, open |
| ArXiv | AI/robotics preprints | Free, open |
| Papers with Code | ML papers + benchmarks | Free, open |
| sz.gov.cn + district sites | Shenzhen policies & subsidies | Public |
| miit.gov.cn | National industrial policy | Public |
| Crunchbase (free tier) | Funding events | Free tier |
| LCSC.com | Component availability & pricing | Public |

---

## Example Report Structure

```
# AI Venture Scout Report

## Executive Summary

## Top 5 Opportunities
### 1. [Product] — 87/100
  - Why this matters
  - Market Analysis (TAM/SAM/SOM)
  - Shenzhen Supply Chain
  - Team Executability (timeline, budget, MVP scope)
  - Competitive Landscape
  - Policy Support (national + district level)
  - Key Risks & Strengths
  - Why this fits YOUR team

## Honorable Mentions (6–10 products)

## Final Recommendation

## References (all citations with URLs)
```

---

## License

MIT

---

*Built with Claude API + LangGraph. Not affiliated with Anthropic or LangChain.*
