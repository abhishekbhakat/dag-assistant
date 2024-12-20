"""DAG Scoring System"""

from typing import Any

# Scoring deductions for various issues
SCORING_MATRIX = {
    # Critical Issues (30-40% deduction)
    "top_level_code": {
        "deduction": 40,
        "description": "Top-level code detected (e.g., API calls, DB queries, heavy imports)",
        "category": "Critical",
        "rationale": "Severely impacts scheduler performance, executed every parse",
    },
    "dynamic_start_date": {"deduction": 35, "description": "Dynamic start_date using datetime.now()", "category": "Critical", "rationale": "Breaks idempotency and causes scheduling issues"},
    "no_retries": {"deduction": 30, "description": "No retry mechanism configured", "category": "Critical", "rationale": "Critical for task reliability in distributed environments"},
    # Major Issues (15-25% deduction)
    "direct_db_access": {
        "deduction": 25,
        "description": "Direct database access without proper connection handling",
        "category": "Major",
        "rationale": "Can cause connection leaks and performance issues",
    },
    "missing_provider_package": {
        "deduction": 20,
        "description": "Not using available provider package for integration",
        "category": "Major",
        "rationale": "Missing optimized and maintained provider features",
    },
    "dynamic_task_mapping": {"deduction": 20, "description": "Dynamic task mapping at runtime", "category": "Major", "rationale": "Can cause DAG parsing issues and scheduler overhead"},
    # Minor Issues (5-10% deduction)
    "no_documentation": {"deduction": 10, "description": "Missing or insufficient DAG documentation", "category": "Minor", "rationale": "Impacts maintainability and team collaboration"},
    "no_tags": {"deduction": 5, "description": "No tags defined for DAG", "category": "Minor", "rationale": "Makes DAG organization and filtering difficult"},
    "no_sla": {"deduction": 5, "description": "No SLA defined for critical tasks", "category": "Minor", "rationale": "Missing SLA monitoring for important tasks"},
}


def calculate_task_prognosis(task) -> dict[str, Any]:
    """Calculate prognosis for a single task."""
    score = 100.0
    issues = []

    # Check retry configuration
    if not task.retries:
        score -= SCORING_MATRIX["no_retries"]["deduction"]
        issues.append({"type": "no_retries", "message": "Task has no retry mechanism configured", "task_id": task.task_id})

    # Check execution timeout
    if not task.execution_timeout:
        score -= 5
        issues.append({"type": "no_timeout", "message": "Task has no execution timeout set", "task_id": task.task_id})

    # Check for depends_on_past
    if task.depends_on_past:
        score -= 10
        issues.append({"type": "depends_on_past", "message": "Task uses depends_on_past which can cause scheduling issues", "task_id": task.task_id})

    # Check for proper queue assignment
    if not task.queue:
        score -= 5
        issues.append({"type": "no_queue", "message": "Task has no specific queue assigned", "task_id": task.task_id})

    return {"task_id": task.task_id, "score": max(0.0, score), "issues": issues}


def calculate_dag_prognosis(dag) -> dict[str, Any]:
    """Calculate prognosis for a DAG."""
    score = 100.0
    issues = []
    task_scores = {}

    # Check start_date configuration
    if not dag.start_date:
        score -= SCORING_MATRIX["dynamic_start_date"]["deduction"]
        issues.append({"type": "no_start_date", "message": "DAG has no start_date configured"})

    # Check documentation
    if not dag.doc_md and not dag.description:
        score -= SCORING_MATRIX["no_documentation"]["deduction"]
        issues.append({"type": "no_documentation", "message": "DAG lacks documentation"})

    # Check tags
    if not dag.tags:
        score -= SCORING_MATRIX["no_tags"]["deduction"]
        issues.append({"type": "no_tags", "message": "DAG has no tags defined"})

    # Analyze each task
    for task in dag.tasks:
        task_prognosis = calculate_task_prognosis(task)
        task_scores[task.task_id] = task_prognosis

        # Adjust DAG score based on task issues
        if task_prognosis["score"] < 70:  # Critical task issues
            score -= 5
        elif task_prognosis["score"] < 85:  # Major task issues
            score -= 2

    # Check overall DAG complexity
    if len(dag.tasks) > 50:
        score -= 10
        issues.append({"type": "high_complexity", "message": f"DAG has {len(dag.tasks)} tasks, consider breaking it down"})

    return {"dag_id": dag.dag_id, "score": max(0.0, score), "issues": issues, "task_scores": task_scores}


def get_score_color(score: float) -> str:
    """Get color for prognosis score."""
    if score >= 90:
        return "green"
    elif score >= 70:
        return "yellow"
    else:
        return "red"


def calculate_score(analysis: dict[str, Any]) -> float:
    """Calculate DAG score based on analysis results."""
    score = 100.0
    for issue, details in analysis.get("issues", {}).items():
        if issue in SCORING_MATRIX:
            score -= SCORING_MATRIX[issue]["deduction"]
    return max(0.0, score)
