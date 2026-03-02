# Cookie Traverser

Automated tool to capture and compare site cookies.

## Installation

1. Install Poetry: `pip install poetry`
2. Install dependencies: `poetry install`
3. Install Chromium: `poetry run playwright install chromium`

## Usage

1. Update `config.toml` (see examples in the file)
2. Run: `poetry run start`

## Output

Results are saved to `cookie_report.json`.
