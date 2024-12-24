from pathlib import Path
from typing import Any

from airflow.models.dag import DAG
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from airflow_crew.tools.support import analyzers
from airflow_crew.tools.support.docker_manager import AirflowVersionConfig, DockerEnvironmentManager


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

        Args:
            code (str): The DAG code to analyze
            dag (DAG, optional): DAG object for runtime analysis

        Returns:
            dict: Analysis results with score, color indicator, and detailed analysis
        """
        return analyzers.analyze_dag(code, dag)


class PerformanceAnalysisInput(BaseModel):
    """Input schema for PerformanceAnalysisTool."""

    dag_path: Path = Field(..., description="Path to DAG file to analyze")
    config: AirflowVersionConfig = Field(..., description="Airflow version configuration")
    task_id: str | None = Field(None, description="Optional task ID to profile")
    duration: int = Field(default=60, description="Duration in seconds for profiling")


class PerformanceAnalysisTool(BaseTool):
    """Performance analysis tool"""

    name: str = "performance_analysis"
    description: str = "Analyze DAG performance using py-spy in Docker environment"
    args_schema: type[BaseModel] = PerformanceAnalysisInput

    def __init__(self):
        super().__init__()
        self.docker_manager = DockerEnvironmentManager()

    def _run(self, dag_path: Path, config: AirflowVersionConfig, task_id: str | None = None, duration: int = 60) -> dict[str, Any]:
        try:
            # Create container if not exists
            if not self.docker_manager.container:
                self.docker_manager.create_container(config, dag_path)

            # Run task test to get process
            cmd = ["airflow", "tasks", "test"]
            if task_id:
                cmd.extend([Path(dag_path).stem, task_id, "2024-01-01"])
            else:
                cmd.extend(["dags", "list-tasks", Path(dag_path).stem])

            exit_code, output = self.docker_manager.execute_command(cmd)

            if exit_code != 0:
                return {"success": False, "error": f"Failed to run task: {output}"}

            # Get task process PID
            exit_code, pid_output = self.docker_manager.execute_command(["pgrep", "-f", "airflow"])

            if exit_code != 0:
                return {"success": False, "error": "Failed to get task PID"}

            # Collect comprehensive performance metrics
            metrics = self.docker_manager.get_performance_metrics(pid=int(pid_output.strip()), duration=duration)

            # Analyze metrics and generate insights
            insights = self._analyze_performance_metrics(metrics)

            return {"success": True, "metrics": metrics, "insights": insights, "recommendations": self._generate_recommendations(metrics, insights), "task_output": output}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _analyze_performance_metrics(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Analyze performance metrics to identify issues and patterns."""
        insights = {
            "cpu": {
                "high_utilization": any(u > 80 for u in metrics["cpu"].get("utilization_percent", [])),
                "hotspots": metrics["cpu"].get("hotspots", [])[:5],
            },
            "memory": {
                "leaks_detected": len(metrics["memory"].get("leaks", [])) > 0,
                "large_objects": metrics["memory"].get("large_objects", [])[:5],
            },
            "io": {
                "high_wait_time": metrics["io"].get("io_wait", 0) > 5.0,
                "inefficient_patterns": self._detect_io_patterns(metrics["io"]),
            },
            "database": {
                "slow_queries": metrics["db"].get("slow_queries", [])[:5],
                "connection_issues": self._analyze_db_patterns(metrics["db"]),
            },
            "scheduling": {
                "parse_time_issues": metrics["scheduling"].get("dag_file_parse_time", 0) > 2.0,
                "queue_bottlenecks": self._analyze_queue_metrics(metrics["scheduling"]),
            },
        }
        return insights

    def _detect_io_patterns(self, io_metrics: dict[str, Any]) -> list[str]:
        """Detect inefficient I/O patterns."""
        patterns = []
        if io_metrics.get("random_reads", 0) > io_metrics.get("sequential_reads", 0):
            patterns.append("High random read ratio")
        return patterns

    def _analyze_db_patterns(self, db_metrics: dict[str, Any]) -> list[str]:
        """Analyze database operation patterns."""
        issues = []
        for query in db_metrics.get("queries", []):
            if query.get("execution_time", 0) > 1.0:
                issues.append(f"Slow query: {query.get('sql', 'Unknown')}")
        return issues

    def _analyze_queue_metrics(self, scheduling_metrics: dict[str, Any]) -> list[str]:
        """Analyze task queue metrics."""
        issues = []
        queue_metrics = scheduling_metrics.get("queue_metrics", {})
        if any(t > 60 for t in queue_metrics.get("waiting_time", [])):
            issues.append("Long queue waiting times")
        return issues

    def _generate_recommendations(self, metrics: dict[str, Any], insights: dict[str, Any]) -> list[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        # CPU recommendations
        if insights["cpu"]["high_utilization"]:
            recommendations.append("Consider splitting CPU-intensive tasks or increasing resources")

        # Memory recommendations
        if insights["memory"]["leaks_detected"]:
            recommendations.append("Memory leaks detected - review resource cleanup in tasks")

        # I/O recommendations
        if insights["io"]["high_wait_time"]:
            recommendations.append("High I/O wait times - consider optimizing data access patterns")

        # Database recommendations
        if insights["database"]["slow_queries"]:
            recommendations.append("Optimize database queries or consider using provider-specific operators")

        # Scheduling recommendations
        if insights["scheduling"]["parse_time_issues"]:
            recommendations.append("High DAG parse time - review top-level code and imports")

        return recommendations

    def cleanup(self):
        """Cleanup Docker resources"""
        self.docker_manager.cleanup()
