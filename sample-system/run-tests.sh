#!/bin/bash
# Test script for running all ArchAgent test diffs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIFF_DIR="$SCRIPT_DIR/test-diffs"

echo "🧪 ArchAgent Sample System Test Suite"
echo "======================================"
echo ""

# Check if archagent is available
if ! command -v archagent &> /dev/null; then
    echo "❌ archagent CLI not found. Please install it first:"
    echo "   cd ../cli && ./install.sh"
    exit 1
fi

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ ArchAgent engine not running. Start it with:"
    echo "   docker compose up -d"
    exit 1
fi

echo "✅ ArchAgent engine is running"
echo ""

# Test each diff file
VIOLATIONS=0
CLEAN=0
TOTAL=0

for diff in "$DIFF_DIR"/*.diff; do
    TOTAL=$((TOTAL + 1))
    filename=$(basename "$diff")

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📄 Test: $filename"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Run review
    if archagent review --diff "$diff" --format text; then
        if [[ "$filename" == *"clean"* ]]; then
            echo "✅ PASS: Clean diff validated successfully"
            CLEAN=$((CLEAN + 1))
        else
            echo "⚠️  WARNING: Expected violations but none found"
        fi
    else
        if [[ "$filename" == *"clean"* ]]; then
            echo "❌ FAIL: Clean diff should not have violations"
        else
            echo "✅ PASS: Violations detected as expected"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    fi

    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Total tests: $TOTAL"
echo "Violations detected: $VIOLATIONS"
echo "Clean diffs passed: $CLEAN"
echo ""
echo "💡 Next steps:"
echo "   1. Review findings in the dashboard: http://localhost:3000"
echo "   2. Provide feedback: archagent feedback <review-id> <finding-id> <valid|false_positive>"
echo "   3. Check stats: archagent stats"
echo "   4. Retrain after 20+ annotations: archagent retrain"

