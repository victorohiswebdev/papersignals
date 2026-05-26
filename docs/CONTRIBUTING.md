# Contributing to PaperSignals

Thanks for your interest! This project is in early development and all contributions are welcome.

## Getting Started

```bash
git clone https://github.com/victorohiswebdev/papersignals.git
cd papersignals
pip install -e ".[dev]"
python -c "import nltk; nltk.download('punkt_tab', quiet=True)"
```

## Running Tests

```bash
pytest -v --tb=short
```

## Code Style

We use `ruff` for linting:
```bash
ruff papersignals/ tests/
```

## What Needs Help

- **Phase 2 features** — ArXiv corpus baseline generator in `papersignals/corpus/`
- **More test fixtures** — Real academic texts at various quality levels
- **Wordlist expansion** — Adding to the AI-favored words, transition words, hedging words lists
- **Documentation** — Tutorials, blog posts, examples
- **Dashboard** — FastAPI backend + Next.js frontend (see ARCHITECTURE.md)

## Pull Request Process

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-idea`)
3. Write tests for your changes
4. Ensure all tests pass
5. Submit a PR with a clear description

## Questions?

Open an issue, or reach out to victorohisprojects@gmail.com.
