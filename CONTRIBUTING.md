# Contributing to AI Meeting Agent

Thank you for your interest in contributing to the **AI Meeting Agent**! We welcome community contributions to help improve the platform's reliability, AI accuracy, and integrations.

To ensure a smooth collaboration, please follow the guidelines below.

---

## Code of Conduct

We expect all contributors to adhere to standard professional conduct:
- Be respectful, constructive, and collaborative.
- Focus on technical improvements and documentation clarity.

---

## Getting Started

### 1. Setup Your Local Environment
Follow the installation steps in the main [README.md](README.md) to set up:
- Docker and Docker Compose
- Node.js (for the MCP Server)
- Python 3.11 virtual environment

### 2. Run Tests and Linters
Before submitting a pull request, ensure all code conforms to linting conventions:
- **Backend (Python)**: Format code using `black` and check for errors using `flake8`.
- **MCP Server (Node.js)**: Ensure there are no runtime warnings on startup. Run:
  ```bash
  npm run start
  ```
  And verify using the MCP Inspector:
  ```bash
  npx @modelcontextprotocol/inspector node server.js
  ```

---

## Development Workflow

### 1. Branching Policy
We use a standard branching workflow:
- Always create a new branch from `main` for your feature or bug fix:
  ```bash
  git checkout -b feature/your-feature-name
  ```
  or
  ```bash
  git checkout -b bugfix/your-bugfix-name
  ```

### 2. Coding Standards
- **Keep it Async**: Ensure all database interactions in the FastAPI service layer use SQLAlchemy's `AsyncSession`.
- **Thread Safety**: When creating background workers or tasks, avoid sharing database connections or event loops across worker threads.
- **Diagnostics to Stderr**: In the MCP server, write all logging and debugging outputs to `stderr` (`console.error`). `stdout` (`console.log`) is strictly reserved for JSON-RPC messages.

### 3. Submitting a Pull Request
1. Commit your changes with clear, descriptive commit messages.
2. Push your branch to GitHub:
   ```bash
   git push origin feature/your-feature-name
   ```
3. Open a Pull Request (PR) against the `main` branch.
4. Provide a clear description of the problem solved and the tests performed.
