<p align="center">
  <b>GamED.AI</b><br>
  <i>A Hierarchical Multi-Agent Framework for Automated Educational Game Generation</i>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> |
  <a href="#architecture">Architecture</a> |
  <a href="#citation">Citation</a> |
  <a href="#license">License</a>
</p>

---

GamED.AI automatically transforms educational questions into interactive web-based games. Given any question — from "Label the parts of a plant cell" to "Trace through bubble sort" — the V4 pipeline orchestrates specialized AI agents across 6 phases to produce fully playable games covering 15 mechanic types.

## Citation

```bibtex
@inproceedings{agarwal-etal-2026-gamedai,
    title = "{GamED.AI}: A Hierarchical Multi-Agent Framework for Automated Educational Game Generation",
    author = "Agarwal, Shiven and Shah, Yash and Shekhar, Ashish Raj and Bordoloi, Priyanuj and De, Sandipan and Gupta, Vivek",
    booktitle = "Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics: System Demonstrations",
    month = aug,
    year = "2026",
    publisher = "Association for Computational Linguistics",
}
```

---

## Quick Start

### 1. Install Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set API Keys

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY (for Gemini) or GROQ_API_KEY (free tier)
```

### 3. Generate a Game

```bash
python run.py "Label the parts of a plant cell"
```

Output: `output/label-the-parts-of-a-plant-cell.json` (also copied to `frontend/public/games/`)

### 4. Play the Game

```bash
cd ../frontend
npm install
npm run dev
# Open http://localhost:3000
```

Load the generated JSON via drag-drop, file picker, or URL parameter (`/play?game=label-the-parts-of-a-plant-cell`).

---

## CLI Options

```
python run.py "Your question here"              # Generate a game
python run.py "Your question" -o my_game.json   # Custom output path
python run.py --dry-run                          # Test graph compilation only
python run.py --list-questions                   # Show example questions
python run.py -v "Your question"                 # Verbose debug logging
```

---

## Repository Structure

```
GamED-AI/
├── backend/
│   ├── run.py                      # CLI entry point
│   ├── app/
│   │   ├── v4/                     # V4 pipeline (46 files)
│   │   │   ├── graph.py            # LangGraph StateGraph (22 nodes)
│   │   │   ├── state.py            # V4MainState TypedDict
│   │   │   ├── agents/             # Pipeline agents (12 files)
│   │   │   ├── validators/         # Quality gates (6 files)
│   │   │   ├── schemas/            # Pydantic models
│   │   │   └── prompts/            # Agent prompt templates
│   │   ├── agents/                 # Graph factory + instrumentation
│   │   ├── config/                 # Model presets, mechanic contracts
│   │   ├── services/               # LLM service, web search, asset gen
│   │   ├── db/                     # SQLAlchemy models + database
│   │   ├── routes/                 # FastAPI endpoint (generate)
│   │   └── utils/                  # Logging config
│   ├── scripts/                    # V4 test scripts
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/play/               # Game player page (drag-drop JSON)
│   │   └── components/templates/   # Game rendering (15 mechanic types)
│   └── public/games/               # Generated game JSONs (gitignored)
└── docs/
    └── ARCHITECTURE.md
```

---

## Architecture

The V4 pipeline is a 3-stage Creative Cascade in LangGraph with 22 nodes across 6 phases:

1. **Phase 0 — Context Gathering** (parallel): Input analysis + domain knowledge retrieval
2. **Phase 1 — Concept Design**: Game concept with learning objective, template, mechanic contract + validation loop
3. **Phase 1b — Scene Design** (parallel via `Send()`): Per-scene creative designs
4. **Phase 2 — Game Plan** (deterministic): Scene IDs, score contracts, asset needs, transition graph
5. **Phase 3 — Content + Assets** (parallel): Scene content generation + asset workers
6. **Phase 4 — Assembly** (deterministic): Combines everything into a verified JSON blueprint

Quality Gates at each phase boundary execute without LLM inference for constant cost and formal verifiability.

Supported mechanics: drag-drop, click-to-identify, trace-path, sequencing, sorting, memory-match, branching-scenario, compare-contrast, description-matching, hierarchical, state-tracer, bug-hunter, algorithm-builder, complexity-analyzer, constraint-puzzle.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed pipeline diagrams.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

Copyright 2026 Shiven Agarwal, Yash Shah, Ashish Raj Shekhar, Priyanuj Bordoloi, Sandipan De, Vivek Gupta
