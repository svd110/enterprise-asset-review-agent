# Asset Review Agent

An AI agent that reviews an enterprise software inventory and proposes whether each asset should be maintained, replaced, or investigated, citing the records it used.

The inventory uses real software products with lifecycle and support data taken from official vendor documentation, placed inside a fictional company whose business criticality, maintenance costs, and application dependencies are invented for this project.

Kosha Bank is a fictional mid-size private bank created for this project. Any resemblance to a real institution is unintended.

## Setup

Requires Python 3.10 or later and an OpenAI API key.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then add your OpenAI API key to .env
python scripts/build_db.py
```

## Usage

Ask the agent a question:

```bash
python -m src.agent "Which assets need review?"
```

The output shows each tool the model chose, what the tool returned, the final proposal, and a validation check confirming that every cited asset was retrieved and every date matches the database.

Run the demonstration cases (needs attention, no immediate action, missing information, invalid request, and tool failure):

```bash
python -m demo.run_demo
```

Run the tool tests:

```bash
python -m pytest
```

## Project structure

- `data/`: inventory CSVs and the data dictionary
- `scripts/build_db.py`: builds the SQLite database from the CSVs
- `src/tools.py`: the four tools the agent can call
- `src/agent.py`: tool descriptions, instructions, and the agent loop
- `src/validation.py`: checks answers against the database
- `demo/run_demo.py`: runs the demonstration cases
- `outputs/demo_runs/`: saved demo output
