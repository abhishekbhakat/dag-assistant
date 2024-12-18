from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import List, Optional
from pathlib import Path

# If you want to run a snippet of code before or after the crew starts, 
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

class AirflowCrew:
    """AirflowCrew for DAG analysis, fixes and generation"""

    def __init__(self):
        self.agents = self._create_agents()
        self.tasks = {}

    def _create_agents(self) -> dict:
        # Learn more about YAML configuration files here:
        # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
        # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
        return {
            "dag_prognosis": Agent(
                role="DAG Analyzer",
                goal="Analyze DAG code for issues and improvements",
                backstory="Expert in Apache Airflow DAG analysis focusing on code quality and patterns",
                tools=["static_analysis", "pattern_detection"]
            ),
            "lead_author": Agent(
                role="Lead DAG Author",
                goal="Coordinate DAG modifications and generation",
                backstory="Senior Airflow developer who orchestrates all DAG changes",
                tools=["code_generation", "code_review"]
            ),
            "airflow_cli": Agent(
                role="Airflow CLI Expert",
                goal="Handle Airflow CLI operations and testing",
                backstory="DevOps expert managing Airflow deployments and testing",
                tools=["cli_operations", "dag_testing"]
            ),
            "providers_author": Agent(
                role="Provider Specialist",
                goal="Manage provider-specific code and compatibility",
                backstory="Expert in Airflow providers and their best practices",
                tools=["provider_management", "connection_setup"]
            ),
            "ruff_formatter": Agent(
                role="Code Quality Expert",
                goal="Ensure code quality and style standards",
                backstory="Python code quality specialist focusing on best practices",
                tools=["code_formatting", "style_checking"]
            ),
            "python_profiler": Agent(
                role="Performance Analyst",
                goal="Analyze and optimize DAG performance",
                backstory="Performance optimization specialist for Python and Airflow",
                tools=["performance_analysis", "memory_profiling"]
            ),
            "mock_env": Agent(
                role="Environment Manager",
                goal="Manage test environments and validation",
                backstory="Testing environment specialist for Airflow deployments",
                tools=["environment_setup", "connection_mocking"]
            )
        }

    def analyze_dag(self, dag_path: Path) -> dict:
        # To learn more about structured task outputs, 
        # task dependencies, and task callbacks, check out the documentation:
        # https://docs.crewai.com/concepts/tasks#overview-of-a-task
        tasks = [
            Task(
                description="Analyze DAG for issues",
                agent=self.agents["dag_prognosis"]
            ),
            Task(
                description="Check performance metrics",
                agent=self.agents["python_profiler"]
            ),
            Task(
                description="Validate runtime environment",
                agent=self.agents["mock_env"]
            )
        ]
        crew = Crew(
            agents=list(self.agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        return crew.kickoff()

    def fix_dag(self, dag_path: Path, issues: List[str]) -> dict:
        tasks = [
            Task(
                description="Plan DAG fixes",
                agent=self.agents["lead_author"]
            ),
            Task(
                description="Apply provider updates",
                agent=self.agents["providers_author"]
            ),
            Task(
                description="Format and validate code",
                agent=self.agents["ruff_formatter"]
            )
        ]
        crew = Crew(
            agents=list(self.agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        return crew.kickoff()

    def generate_dag(self, prompt: str) -> dict:
        tasks = [
            Task(
                description="Generate DAG structure",
                agent=self.agents["lead_author"]
            ),
            Task(
                description="Setup providers and connections",
                agent=self.agents["providers_author"]
            ),
            Task(
                description="Validate and optimize",
                agent=self.agents["dag_prognosis"]
            )
        ]
        crew = Crew(
            agents=list(self.agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
        return crew.kickoff()
