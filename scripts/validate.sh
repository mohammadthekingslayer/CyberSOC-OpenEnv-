#!/usr/bin/env bash
# Validate the project setup
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🔍 Validating CyberSOC OpenEnv project..."
echo ""

ERRORS=0

# Check Python version
echo "=== Python Version ==="
python --version 2>&1
echo ""

# Check required packages
echo "=== Package Check ==="
for pkg in pydantic fastapi uvicorn openai numpy pandas pytest dotenv docker; do
    if python -c "import $pkg" 2>/dev/null; then
        echo "  ✅ $pkg"
    else
        echo "  ❌ $pkg NOT FOUND"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Check project structure
echo "=== Structure Check ==="
REQUIRED_DIRS=(
    "src/cyber_soc_env"
    "src/cyber_soc_env/tasks"
    "src/cyber_soc_env/graders"
    "src/cyber_soc_env/env"
    "src/cyber_soc_env/api"
    "src/cyber_soc_env/utils"
    "tests"
    "scripts"
    "server"
)
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir/"
    else
        echo "  ❌ $dir/ MISSING"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Check key files
echo "=== File Check ==="
REQUIRED_FILES=(
    "openenv.yaml"
    "pyproject.toml"
    "requirements.txt"
    ".env.example"
    ".gitignore"
    "README.md"
    "inference.py"
)
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file MISSING"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Run tests
echo "=== Running Tests ==="
python -m pytest tests/ -v --tb=short 2>&1 || ERRORS=$((ERRORS + 1))
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "✅ All validations passed!"
else
    echo "❌ $ERRORS validation(s) failed!"
fi

exit $ERRORS
