"""DAG Analysis Tools"""

import ast
import os
from typing import Any

import yaml
from airflow_crew.tools.support import scoring

# Load provider mappings
current_dir = os.path.dirname(os.path.abspath(__file__))
provider_mappings_path = os.path.join(current_dir, "provider_mappings.yaml")
with open(provider_mappings_path) as f:
    PROVIDER_MAPPINGS = yaml.safe_load(f)


def get_stdlib_modules() -> set[str]:
    """Get set of Python standard library module names."""
    return {
        "datetime",
        "time",
        "json",
        "os",
        "sys",
        "logging",
        "re",
        "pathlib",
        "collections",
        "itertools",
        "functools",
        "typing",
        "abc",
        "copy",
        "contextlib",
        "warnings",
        "tempfile",
        "shutil",
        "random",
        "uuid",
        "hashlib",
        "base64",
        "urllib",
        "http",
        "email",
        "xml",
        "html",
        "csv",
        "sqlite3",
        "pickle",
        "gzip",
        "zipfile",
        "tarfile",
        "configparser",
    }


def get_trusted_modules() -> set[str]:
    """Get set of trusted module names that shouldn't be flagged as third-party."""
    return {"airflow", "astronomer"}


def get_database_access_modules() -> set[str]:
    """Get set of modules that indicate direct database access."""
    return {
        "sqlalchemy",
        "sqlalchemy.orm",
        "sqlalchemy.sql",
        "sqlalchemy.engine",
        "sqlalchemy.ext",
        "sqlalchemy.dialects",
        "sqlalchemy.pool",
        "sqlalchemy.func",
        "func",
        "orm",
        "Session",
        "sqlalchemy.orm.session",
        "sqlalchemy.orm.query",
        "sqlalchemy.sql.expression",
        "sqlalchemy.engine.create",
        "pymysql",
        "psycopg2",
        "mysql.connector",
        "airflow.utils.db",
        "airflow.utils.db_cleanup",
        "airflow.utils.session",
        "airflow.utils.sqlalchemy",
        "provide_session",
        "NEW_SESSION",
    }


class ImportAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze imports in Python code."""

    def __init__(self):
        self.imports = {"stdlib": set(), "trusted": set(), "third_party": set(), "top_level": set()}
        self.issues = []
        self.stdlib_modules = get_stdlib_modules()
        self.trusted_modules = get_trusted_modules()
        self.db_modules = get_database_access_modules()

    def visit_Import(self, node):
        """Process Import nodes."""
        for name in node.names:
            self._process_import(name.name, node)

    def visit_ImportFrom(self, node):
        """Process ImportFrom nodes."""
        if node.module:
            self._process_import(node.module, node)

    def _process_import(self, name: str, node: ast.AST):
        """Process an import and categorize it."""
        base_module = name.split(".")[0]

        if base_module in self.stdlib_modules:
            self.imports["stdlib"].add(name)
        elif base_module in self.trusted_modules:
            self.imports["trusted"].add(name)
        else:
            self.imports["third_party"].add(name)

        # Check for top-level imports
        if isinstance(node, ast.Import) and not isinstance(node.parent, ast.FunctionDef | ast.ClassDef):
            self.imports["top_level"].add(name)

        # Check for database access
        if name in self.db_modules:
            self.issues.append({"type": "direct_db_access", "message": f"Direct database access detected: {name}", "line": node.lineno})


class TopLevelCodeAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze top-level code patterns."""

    def __init__(self):
        self.issues = {"imports": [], "api_calls": [], "db_operations": [], "airflow_vars": [], "dynamic_dates": []}
        self.sqlalchemy_patterns = {
            "methods": {
                "execute",
                "query",
                "commit",
                "rollback",
                "close",
                "connect",
                "create_engine",
                "sessionmaker",
                "scoped_session",
                "min",
                "max",
                "scalar",
                "all",
                "first",
                "one",
                "count",
                "select_from",
            },
            "classes": {"Engine", "Connection", "Session", "Query", "MetaData", "Table", "func", "orm", "session"},
            "modules": {"sqlalchemy", "orm", "engine", "session", "query", "func"},
            "db_functions": {"run_cleanup", "purge_table", "resetdb", "initdb", "upgradedb", "check_migrations", "reflect_tables", "provide_session", "NEW_SESSION"},
        }

    def visit_Call(self, node):
        """Analyze function/method calls."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.sqlalchemy_patterns["methods"]:
                self.issues["db_operations"].append({"type": "db_operation", "message": f"Database operation at top level: {func_name}", "line": node.lineno})
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id in self.sqlalchemy_patterns["modules"]:
                    self.issues["db_operations"].append({"type": "db_operation", "message": f"Database operation at top level: {node.func.value.id}.{node.func.attr}", "line": node.lineno})


def analyze_imports_ast(source_code: str) -> dict[str, Any]:
    """Analyze imports using AST."""
    tree = ast.parse(source_code)
    analyzer = ImportAnalyzer()
    analyzer.visit(tree)
    return {"imports": analyzer.imports, "issues": analyzer.issues}


def find_provider_for_package(package: str) -> str | None:
    """Find Airflow provider that could replace a third-party package."""
    return PROVIDER_MAPPINGS.get(package)


def analyze_missing_providers(imports: dict[str, set[str]]) -> list[dict[str, Any]]:
    """Analyze missing Airflow providers for third-party imports."""
    issues = []
    for package in imports.get("third_party", set()):
        provider = find_provider_for_package(package)
        if provider:
            issues.append({"type": "missing_provider", "message": f"Consider using {provider} instead of {package}", "package": package, "provider": provider})
    return issues


def analyze_dependencies(dag_file_content: str) -> dict[str, Any]:
    """Analyze task dependency patterns."""
    tree = ast.parse(dag_file_content)
    deps = []
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.RShift | ast.LShift):
            deps.append({"from": node.left, "to": node.right, "type": ">>" if isinstance(node.op, ast.RShift) else "<<"})
    return {"dependencies": deps}


def analyze_task_complexity(task) -> dict[str, Any]:
    """Analyze task complexity based on various factors."""
    metrics = {
        "retries": task.retries if hasattr(task, "retries") else 0,
        "retry_delay": task.retry_delay.total_seconds() if hasattr(task, "retry_delay") else 0,
        "pool": task.pool if hasattr(task, "pool") else None,
        "priority_weight": task.priority_weight if hasattr(task, "priority_weight") else 1,
        "queue": task.queue if hasattr(task, "queue") else None,
        "execution_timeout": task.execution_timeout.total_seconds() if hasattr(task, "execution_timeout") and task.execution_timeout else None,
        "trigger_rule": task.trigger_rule if hasattr(task, "trigger_rule") else None,
        "depends_on_past": task.depends_on_past if hasattr(task, "depends_on_past") else False,
        "wait_for_downstream": task.wait_for_downstream if hasattr(task, "wait_for_downstream") else False,
        "email_on_retry": task.email_on_retry if hasattr(task, "email_on_retry") else False,
        "email_on_failure": task.email_on_failure if hasattr(task, "email_on_failure") else False,
    }

    complexity_score = 0
    if not metrics["retries"]:
        complexity_score += 1
    if metrics["depends_on_past"]:
        complexity_score += 1
    if metrics["wait_for_downstream"]:
        complexity_score += 1
    if not metrics["execution_timeout"]:
        complexity_score += 1

    metrics["complexity_score"] = complexity_score
    return metrics


def analyze_top_level_code_ast(dag_file_content: str) -> dict[str, list[dict[str, Any]]]:
    """Analyze potentially problematic top-level code using AST."""
    tree = ast.parse(dag_file_content)
    analyzer = TopLevelCodeAnalyzer()
    analyzer.visit(tree)
    return analyzer.issues


def analyze_dag_metadata(dag) -> dict[str, Any]:
    """Analyze DAG metadata and configuration."""
    return {
        "schedule_interval": str(dag.schedule_interval),
        "start_date": str(dag.start_date) if dag.start_date else None,
        "end_date": str(dag.end_date) if dag.end_date else None,
        "catchup": dag.catchup,
        "tags": dag.tags,
        "default_args": dag.default_args if hasattr(dag, "default_args") else {},
        "concurrency": dag.concurrency,
        "max_active_runs": dag.max_active_runs,
        "dagrun_timeout": str(dag.dagrun_timeout) if dag.dagrun_timeout else None,
        "description": dag.description if dag.description else None,
    }


def analyze_dag(code: str, dag=None) -> dict[str, Any]:
    """Perform complete DAG analysis and return structured results.

    Args:
        code (str): The DAG code to analyze
        dag (DAG, optional): DAG object for runtime analysis

    Returns:
        dict: Complete analysis results including score, color, and detailed analysis
    """
    # Static code analysis
    imports = analyze_imports_ast(code)
    dependencies = analyze_dependencies(code)
    top_level = analyze_top_level_code_ast(code)
    providers = analyze_missing_providers(imports["imports"])

    # Build recommendations
    recommendations: list[str] = []
    for issue in imports["issues"] + providers:
        if "recommendation" in issue:
            recommendations.append(issue["recommendation"])

    analysis = {
        "summary": "DAG code analysis completed with the following findings:",
        "imports": imports["imports"],
        "issues": imports["issues"] + providers,
        "dependencies": dependencies["dependencies"],
        "top_level_code": top_level,
        "recommendations": recommendations,
    }

    # Runtime analysis if DAG provided
    if dag:
        metadata = analyze_dag_metadata(dag)
        task_metrics = {}
        for task in dag.tasks:
            task_metrics[task.task_id] = analyze_task_complexity(task)

        analysis.update({"metadata": metadata, "task_metrics": task_metrics})

        # Calculate DAG prognosis
        dag_prognosis = scoring.calculate_dag_prognosis(dag)
        analysis["dag_prognosis"] = dag_prognosis
        # Use DAG prognosis score if available
        score = dag_prognosis["score"]
        # Update summary with runtime info
        analysis["summary"] += f"\nRuntime analysis of DAG '{dag.dag_id}' included."
    else:
        # Use static analysis score
        score = scoring.calculate_score(analysis)

    # Add color indicator based on score
    color = "green" if score >= 80 else "yellow" if score >= 60 else "red"

    return {"score": score, "color": color, "analysis": analysis}
