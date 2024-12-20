from airflow.models.dag import DAG
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from airflow_crew.tools.support import analyzers, scoring


class StaticAnalysisInput(BaseModel):
    """Input schema for StaticAnalysisTool."""

    code: str = Field(..., description="DAG code to analyze")
    dag: DAG | None = Field(None, description="DAG object for runtime analysis")


class StaticAnalysisTool(BaseTool):
    """DAG static analysis tool"""

    name: str = "static_analysis"
    description: str = "Analyze DAG code for issues and improvements"
    args_schema: type[BaseModel] = StaticAnalysisInput

    def _run(self, code: str, dag: DAG | None = None) -> dict:
        """Run static analysis on DAG code.

        Returns:
            dict: Analysis results with score, color indicator, and detailed analysis
        """
        # Static code analysis
        imports = analyzers.analyze_imports_ast(code)
        dependencies = analyzers.analyze_dependencies(code)
        top_level = analyzers.analyze_top_level_code_ast(code)
        providers = analyzers.analyze_missing_providers(imports["imports"])

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
            metadata = analyzers.analyze_dag_metadata(dag)
            task_metrics = {}
            for task in dag.tasks:
                task_metrics[task.task_id] = analyzers.analyze_task_complexity(task)

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


class PatternDetectionInput(BaseModel):
    """Input schema for PatternDetectionTool."""

    code: str = Field(..., description="DAG code to analyze for patterns")


class PatternDetectionTool(BaseTool):
    """DAG pattern detection tool"""

    name: str = "pattern_detection"
    description: str = "Detect patterns and anti-patterns in DAG code"
    args_schema: type[BaseModel] = PatternDetectionInput

    def _run(self, code: str) -> dict:
        # Implementation goes here
        pass


class PerformanceAnalysisInput(BaseModel):
    """Input schema for PerformanceAnalysisTool."""

    dag_id: str = Field(..., description="DAG ID to analyze performance")


class PerformanceAnalysisTool(BaseTool):
    """Performance analysis tool"""

    name: str = "performance_analysis"
    description: str = "Analyze performance of DAG"
    args_schema: type[BaseModel] = PerformanceAnalysisInput

    def _run(self, dag_id: str) -> dict:
        # Implementation goes here
        pass
