# ArchAgent Sample System

A sample e-commerce order platform designed to test ArchAgent's architectural review capabilities.

## Architecture

This system demonstrates:
- **Bounded Contexts**: orders, payments, notifications, analytics
- **Layered Architecture**: controller → service → repository → model
- **Event-Driven Communication**: Contexts communicate via events
- **Security Boundaries**: Special rules for the payments context

## Quick Start

### 1. Setup Environment

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 2. Start ArchAgent

```bash
docker compose up -d
```

Wait for services to be ready:
- Engine API: http://localhost:8000
- Dashboard: http://localhost:3000
- Health check: http://localhost:8000/health

### 3. Run Tests

```bash
./run-tests.sh
```

This will run all test diffs through ArchAgent and display results.

### 4. Review Individual Diffs

```bash
# Test a specific violation
archagent review --diff test-diffs/01-layer-violation-controller-to-repository.diff

# Test clean changes
archagent review --diff test-diffs/08-clean-valid-changes.diff
```

## Test Diffs Overview

The `test-diffs/` directory contains 8 test cases:

1. **Layer Violation** - Controller bypasses service layer
2. **Forbidden Context Dependency** - Direct orders→notifications call
3. **Cross-Context Model Sharing + Security** - Payment logging violations
4. **Analytics Forbidden Dependencies** - Analytics accessing other contexts
5. **Model Layer Violation** - Model importing service layer
6. **Notifications Direct Dependency** - Should use events not direct calls
7. **Circular Dependency Risk** - Orders→analytics creates cycle risk
8. **Clean Valid Changes** - Proper event-driven pattern (should pass)

See `test-diffs/README.md` for detailed documentation.

## Providing Feedback

Train ArchAgent by marking findings as valid or false positives:

```bash
archagent feedback <review-id> <finding-id> valid
archagent feedback <review-id> <finding-id> false_positive

# After 20+ annotations
archagent retrain
archagent stats
```

## Architecture Intent

The architecture rules are defined in `architecture-intent.yaml`:
- Bounded context boundaries and dependencies
- Layer separation rules
- Communication patterns
- Security constraints

## Stopping Services

```bash
docker compose down

# Remove all data
docker compose down -v
```
ANTHROPIC_API_KEY=sk-ant-your-key-here

