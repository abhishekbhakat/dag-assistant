# DAG Assistant

AI-powered Apache Airflow DAG assistant that analyzes, fixes, and generates DAGs using best practices.

## Features

- DAG Analysis with iterative optimization
- Automated fixes with version control
- Natural language DAG generation
- Multi-agent architecture for specialized tasks
- Runtime validation in isolated environments

## Workflow

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

## Agents

- **dag-prognosis**
- **lead-author**
- **airflow-cli**
- **providers-author**
- **ruff-formatter**
- **python-profiler**
- **mock-env**
