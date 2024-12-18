# Version Compatibility Design

## Options

1. **Memoization**
   - ✓ Fast lookups, predictable
   - ✗ High maintenance, storage heavy

2. **Event-based**
   - ✓ Real validation, self-updating
   - ✗ Slow, resource intensive

3. **Hybrid (Recommended)**
   - Core rules in code (breaking changes, patterns)
   - Cache per version combo
   - Validate on cache miss
   ```
   .grapher_cache/
     versions/
       python-3.8_airflow-2.7_aws-8.1.0/
         rules.json    # Validated rules
         failures.json # Known issues
   ```
   - Event validation for unknowns

## Implementation Options

1. **Ruff Integration**
   - ✓ Fast Rust engine, wide adoption
   - ✗ Limited to static analysis
   - ✗ Complex contribution process
   - ✗ Hard to add Airflow runtime logic

2. **CrewAI (Recommended)**
   - ✓ Direct agent interactions
   - ✓ Dynamic runtime checks
   - ✓ Flexible agent workflows
   - ✓ Can use Ruff as component
   - ✗ More initial setup needed
