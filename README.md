# AI-Powered Shift Planning & Roster System

A production-ready, fully offline roster scheduling system with an AI engine, supporting **Medical** and **IT** domains.

---

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run (seeds DB automatically on first run)
python main.py
```

Open **http://localhost:8000** in your browser.

---

## Project Structure

```
Roster/
├── main.py                    # Entry point
├── seed_data.py               # Standalone seed script
├── requirements.txt
├── roster.spec                # PyInstaller build spec
├── app/
│   ├── __init__.py            # App factory
│   ├── config.py              # Settings
│   ├── api/                   # FastAPI routers
│   │   ├── employees.py
│   │   ├── departments.py
│   │   ├── schedules.py
│   │   ├── shifts.py
│   │   ├── simulation.py
│   │   └── ui.py
│   ├── agents/                # AI Engine
│   │   ├── availability_agent.py
│   │   ├── rotation_agent.py
│   │   ├── optimization_agent.py
│   │   ├── conflict_agent.py
│   │   ├── learning_agent.py
│   │   └── orchestrator.py
│   ├── services/              # Business logic
│   ├── models/                # SQLAlchemy models
│   ├── db/                    # Database setup & seed
│   ├── utils/                 # Logger, validators
│   ├── templates/             # Jinja2 HTML templates
│   └── static/                # CSS, JS
└── tests/                     # Pytest tests
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/employees/` | List employees |
| `POST` | `/api/employees/` | Create employee |
| `GET`  | `/api/departments/` | List departments |
| `POST` | `/api/schedules/generate` | **Generate AI schedule** |
| `GET`  | `/api/schedules/` | Fetch schedule entries |
| `POST` | `/api/schedules/override` | Manual override |
| `POST` | `/api/simulate/` | What-if simulation |
| `GET`  | `/api/schedules/export/csv` | Export CSV |
| `GET`  | `/api/schedules/export/excel` | Export Excel |

Full Swagger docs: **http://localhost:8000/api/docs**

---

## AI Engine Pipeline

```
LearningAgent → AvailabilityAgent → RotationAgent
    → OptimizationAgent (Greedy) → ConflictAgent
```

### Medical Domain Rules
- Mandatory department rotation every 15 days
- Scoring: Rotation(40%) + Availability(30%) + Rest(20%) + Fairness(10%)
- Max 3 consecutive nights, min 8h rest
- ICU/Emergency load balancing

### IT Domain Rules
- Skill-based assignment (Python, Docker, AWS, etc.)
- Scoring: Skill Match(40%) + Workload(30%) + Availability(20%) + Weekend(10%)
- Max 2 consecutive nights
- On-call rotation fairness

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Build Executable (.exe)

```bash
pip install pyinstaller
pyinstaller roster.spec
# Output: dist/RosterSystem/RosterSystem.exe
```

---

## Domain Toggle

The UI has a **Medical / IT** toggle in the navbar that:
- Persists selection in `localStorage`
- Passes `roster_type` to all API calls
- Shows a **Smart Suggestion Banner** explaining the scheduling logic for the selected domain
- Controls which employees, departments, and scheduling rules are active

---

## Configuration

Create a `.env` file to override defaults:

```env
DATABASE_URL=sqlite:///./roster.db
DEBUG=false
MAX_SHIFTS_PER_WEEK_MEDICAL=6
MAX_SHIFTS_PER_WEEK_IT=5
DEFAULT_REST_HOURS_MEDICAL=8
MEDICAL_ROTATION_WEIGHT=0.40
IT_SKILL_WEIGHT=0.40
```
