# Contributing to GraphRAG Codebase

First off, thanks for taking the time to contribute!

The following is a set of guidelines for contributing to GraphRAG Codebase.
These are mostly guidelines, not rules. Use your best judgment, and feel free
to propose changes to this document in a pull request.

## Code of Conduct

This project and everyone participating in it is governed by the [GraphRAG
Codebase Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are
expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report for GraphRAG Codebase.
Following these guidelines helps maintainers and the community understand your
report, reproduce the behavior, and find related reports.

* **Use the Issue Search** to see if the problem has already been reported.
* **Check if the issue has been fixed** by trying to reproduce it using the
  latest `main` branch.
* **Open a new Issue** and provide as much detail as possible:
  * **Use a clear and descriptive title.**
  * **Describe the exact steps which reproduce the problem.**
  * **Provide specific examples to demonstrate the steps.**
  * **Describe the behavior you observed after following the steps.**
  * **Explain which behavior you expected to see instead and why.**
  * **Include logs** (scrubbed of secrets!).

### Suggesting Enhancements

* **New Language Support**: We welcome extractors for additional languages
  (Go, Rust, TypeScript, etc.)
* **New MCP Tools**: Additional query tools for specific use cases
* **Performance Improvements**: Optimizations for large codebases

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.

## Development Setup

1. **Clone and install dependencies:**

   ```bash
   git clone https://github.com/antonysallas/graphrag-codebase.git
   cd graphrag-codebase
   uv sync
   ```

2. **Start Neo4j:**

   ```bash
   docker run -d --name neo4j \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password \
     neo4j:5
   ```

3. **Copy environment template:**

   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run tests:**

   ```bash
   uv run pytest
   ```

## Styleguides

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Python Style

* We use `ruff` for formatting and linting.
* We use `mypy` for type checking.
* Target Python 3.13+.

Run checks before submitting your PR:

```bash
uv run ruff check src/ --fix
uv run ruff format src/
uv run mypy src/ --strict
uv run pytest
```

## Adding New Language Support

To add support for a new language:

1. Install the tree-sitter grammar package (e.g., `tree-sitter-go`)
2. Create a new extractor in `src/extractors/{language}/`
3. Implement the `BaseExtractor` interface
4. Add schema profile in `config/schema.yaml` if needed
5. Register the extractor in the detection logic
6. Add tests in `tests/`

See `src/extractors/python/` for a reference implementation.

## License

By contributing, you agree that your contributions will be licensed under its
GPL-3.0 License.
