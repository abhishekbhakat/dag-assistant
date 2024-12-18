# CrewAI Design

## Agents

1. **dag-prognosis**
   - Static analysis
   - Pattern detection
   - Performance metrics
   - Version compatibility checks

2. **lead-author**
   - Code generation
   - Code review
   - Task orchestration
   - Version management

3. **airflow-cli**
   - DAG parsing
   - Task testing
   - Deployment
   - CLI operations

4. **providers-author**
   - Provider compatibility
   - Import management
   - Connection setup
   - Provider-specific patterns

5. **ruff-formatter**
   - Code formatting
   - Import sorting
   - Style enforcement
   - PEP compliance

6. **python-profiler**
   - Runtime analysis
   - Memory profiling
   - Performance bottlenecks
   - Optimization suggestions

7. **mock-env**
   - Test environment
   - Connection mocking
   - Variable simulation
   - Runtime validation

## Tools

1. **Static Analysis**
   - AST parsing
   - Pattern matching
   - Import analysis
   - Version checking

2. **Runtime Tools**
   - Docker environments
   - Airflow API
   - Python debugger
   - Memory profiler

3. **Code Tools**
   - Git operations
   - Code formatters
   - Linters
   - AST transformers

4. **Testing Tools**
   - Unit test runners
   - Integration tests
   - Mock generators
   - Validation scripts

## Processes

### 1. Analyze DAG
```mermaid
sequenceDiagram
    User->>lead-author: Request analysis
    loop Until Perfect Score
        lead-author->>dag-prognosis: Start analysis
        dag-prognosis->>python-profiler: Check performance
        dag-prognosis->>ruff-formatter: Check style
        dag-prognosis->>mock-env: Validate runtime
        mock-env->>airflow-cli: Parse DAG
        dag-prognosis->>lead-author: Score & Issues
        alt Score < Perfect
            lead-author->>lead-author: Plan refactor
        end
    end
    lead-author->>User: Report status
```

### 2. Fix DAG
```mermaid
sequenceDiagram
    User->>lead-author: Request fix
    loop Until Perfect Score
        lead-author->>dag-prognosis: Analyze issues
        lead-author->>providers-author: Check providers
        providers-author->>mock-env: Test connections
        lead-author->>ruff-formatter: Format code
        lead-author->>python-profiler: Verify performance
        mock-env->>airflow-cli: Validate DAG
        dag-prognosis->>lead-author: Score & Issues
        alt Score < Perfect
            lead-author->>lead-author: Apply fixes
        end
    end
    lead-author->>User: Return optimized DAG
```

### 3. Generate DAG
```mermaid
sequenceDiagram
    User->>lead-author: Generation prompt
    lead-author->>providers-author: Setup imports
    providers-author->>mock-env: Configure env
    loop Until Perfect Score
        lead-author->>dag-prognosis: Validate structure
        lead-author->>ruff-formatter: Format code
        lead-author->>python-profiler: Check efficiency
        mock-env->>airflow-cli: Test DAG
        dag-prognosis->>lead-author: Score & Issues
        alt Score < Perfect
            lead-author->>lead-author: Refine DAG
        end
    end
    lead-author->>User: Return perfect DAG
```

## Tasks

1. **Analysis Tasks**
   - Code quality check
   - Performance analysis
   - Style validation
   - Runtime verification

2. **Fix Tasks**
   - Issue resolution
   - Code reformatting
   - Provider updates
   - Version compatibility

3. **Generation Tasks**
   - Scaffold creation
   - Provider setup
   - Task definition
   - Dependency mapping
 