.PHONY: install test clean lint

install:
	pip install -e ".[dev]"
	python -c "import nltk; nltk.download('punkt_tab', quiet=True)"

install-full:
	pip install -e ".[dev,corpus]"
	python -c "import nltk; nltk.download('punkt_tab', quiet=True)"

test:
	pytest -v --tb=short

test-cov:
	pytest -v --tb=short --cov=papersignals --cov-report=term-missing

lint:
	ruff papersignals/ tests/

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

example:
	python examples/example_usage.py

.PHONY: init-git
init-git:
	git add -A && git commit -m "Initial commit: project scaffold" && git push origin main
