ld # Test Diffs for ArchAgent Sample System

This directory contains test diffs to demonstrate ArchAgent's ability to detect various architectural violations.

## Architecture Overview

The sample system follows these principles:
- **Bounded Contexts**: orders, payments, notifications, analytics (isolated domains)
- **Layered Architecture**: controller → service → repository → model
- **Event-Driven Communication**: Contexts communicate via events, not direct calls
- **Security Boundaries**: Payments context has special security requirements

## Test Diff Files

### 1. Layer Violation (Controller → Repository)
**File**: `01-layer-violation-controller-to-repository.diff`

**Violation**: Controller directly accesses repository, bypassing the service layer

**Expected Detection**: 
- Layer violation: Controllers forbidden from importing repositories
- Violates the rule: "Controllers handle HTTP only — delegate all logic to services"

### 2. Forbidden Context Dependency
**File**: `02-forbidden-context-dependency-orders-to-notifications.diff`

**Violation**: Orders context directly imports and instantiates NotificationService

**Expected Detection**:
- Bounded context violation: orders → notifications is forbidden
- Should use event-driven communication instead

### 3. Cross-Context Model Sharing + Security
**File**: `03-cross-context-model-sharing-and-security.diff`

**Violations**:
1. Payment service imports Order model from orders context
2. Logging of card numbers in payments context

**Expected Detection**:
- Cross-context model sharing violation
- Security rule violation: "No logging of card numbers" in payments

### 4. Analytics Forbidden Dependencies
**File**: `04-analytics-forbidden-dependencies.diff`

**Violation**: Analytics context directly depends on orders and payments repositories

**Expected Detection**:
- Multiple forbidden dependencies
- Analytics should have no dependencies on other contexts

### 5. Model Layer Violation
**File**: `05-model-layer-violation.diff`

**Violation**: Model imports from service layer

**Expected Detection**:
- Layer violation: Models should be pure data structures
- Rule: "Models are pure data structures — no dependencies"

### 6. Notifications Direct Dependency
**File**: `06-notifications-direct-dependency.diff`

**Violation**: Notifications calls orders service directly instead of event-based

**Expected Detection**:
- Communication pattern violation
- Should use events, not direct calls

### 7. Circular Dependency Risk
**File**: `07-circular-dependency-risk.diff`

**Violation**: Orders importing analytics creates circular dependency risk

**Expected Detection**:
- Potential circular dependency
- Acyclic dependency rule violation

### 8. Clean Valid Changes (Control)
**File**: `08-clean-valid-changes.diff`

**Status**: ✅ Valid changes that follow architectural intent

**Should Pass**: No violations, proper event-driven communication

## Running Tests

### Prerequisites
```bash
# From the sample-system directory
cd /path/to/sample-system

# Ensure .env file exists with API key
cat ../.env
```

### Start ArchAgent
```bash
docker compose up -d

# Wait for services to be ready
docker compose logs -f engine
```

### Test Individual Diffs
```bash
# Test a violation diff
archagent review --diff test-diffs/01-layer-violation-controller-to-repository.diff

# Test the clean diff (should have no findings)
archagent review --diff test-diffs/08-clean-valid-changes.diff
```

### Test All Diffs
```bash
# Create a test script
for diff in test-diffs/*.diff; do
  echo "=== Testing $diff ==="
  archagent review --diff "$diff" --format text
  echo ""
done
```

### Expected Results Summary

| Diff | Expected Findings | Severity |
|------|------------------|----------|
| 01-layer-violation | Layer violation (controller→repository) | HIGH |
| 02-forbidden-context | Forbidden dependency (orders→notifications) | HIGH |
| 03-cross-context-model | Model sharing + security violation | CRITICAL |
| 04-analytics-forbidden | Multiple forbidden dependencies | HIGH |
| 05-model-layer | Model layer dependency violation | MEDIUM |
| 06-notifications-direct | Direct call instead of event | HIGH |
| 07-circular-dependency | Circular dependency risk | HIGH |
| 08-clean-valid | No violations ✅ | NONE |

## Providing Feedback

After reviewing, you can provide feedback to train the reward model:

```bash
# Get the review ID from the output
REVIEW_ID="<review-id-from-output>"
FINDING_ID="<finding-id-from-output>"

# Mark as valid violation
archagent feedback $REVIEW_ID $FINDING_ID valid

# Mark as false positive
archagent feedback $REVIEW_ID $FINDING_ID false_positive

# Check training progress
archagent stats
```

## Testing the Feedback Loop

1. Run all diffs and mark findings (20+ annotations needed)
2. Check stats: `archagent stats`
3. Retrain model: `archagent retrain`
4. Re-run diffs to see improved confidence scores
5. Low-confidence findings should be suppressed

## Architecture Intent Reference

The architectural rules are defined in `architecture-intent.yaml`:
- Bounded context ownership and dependencies
- Layer patterns and allowed/forbidden imports
- Communication patterns (event vs direct)
- Security rules for sensitive contexts

## Troubleshooting

### Engine not responding
```bash
docker compose ps
docker compose logs engine
```

### CLI can't find server
```bash
export ARCHAGENT_SERVER=http://localhost:8000
archagent review --server http://localhost:8000 --diff test-diffs/01-*.diff
```

### Database issues
```bash
docker compose down -v
docker compose up -d
```
diff --git a/src/orders/services/order.service.ts b/src/orders/services/order.service.ts
index 1234567..abcdefg 100644
--- a/src/orders/services/order.service.ts
+++ b/src/orders/services/order.service.ts
@@ -28,6 +28,12 @@ export class OrderService {
       totalAmount: saved.totalAmount,
     });
 
+    // CLEAN: Proper event-driven communication
+    // Instead of directly calling notifications, we publish an event
+    await this.eventBus.publish("order.payment-required", {
+      orderId: saved.id,
+      amount: saved.totalAmount,
+    });
+
     return saved;
   }
 
@@ -47,4 +53,11 @@ export class OrderService {
   async getCustomerOrders(customerId: string): Promise<Order[]> {
     return this.orderRepo.findByCustomerId(customerId);
   }
+
+  async validateOrder(orderId: string): Promise<boolean> {
+    const order = await this.orderRepo.findById(orderId);
+    return order !== null && 
+           order.status !== OrderStatus.CANCELLED &&
+           order.items.length > 0;
+  }
 }

