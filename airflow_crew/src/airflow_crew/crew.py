from crewai import Agent, Crew, Task, LLM
from crewai.project import CrewBase, agent, crew
from crewai.flow.flow import Flow, listen, start
from typing import List, Optional
from pathlib import Path
import yaml

@CrewBase
class AirflowCrew(Flow):
    """AirflowCrew for DAG analysis, fixes and generation"""

    def __init__(self):
        super().__init__()
        self.code_llm = LLM(model="qwen/qwen-2.5-coder-32b-instruct", temperature=0.01)
        self.general_llm = LLM(model="qwen/qwq-32b-preview", temperature=0.01)
        self.agents_config = {
            "dag_prognosis": {},
            "lead_author": {},
            "airflow_cli": {},
            "providers_author": {},
            "ruff_formatter": {},
            "python_profiler": {},
            "mock_env": {}
        }

    @agent
    def dag_prognosis(self) -> Agent:
        return Agent(
            config=self.agents_config["dag_prognosis"],
            llm=self.general_llm,
            tools=["static_analysis", "pattern_detection"]
        )

    @agent
    def lead_author(self) -> Agent:
        return Agent(
            config=self.agents_config["lead_author"],
            llm=self.code_llm,
            allow_code_execution=True,
            tools=["code_generation", "code_review"]
        )

    @agent
    def airflow_cli(self) -> Agent:
        return Agent(
            config=self.agents_config["airflow_cli"],
            llm=self.general_llm,
            tools=["cli_operations", "dag_testing"]
        )

    @agent
    def providers_author(self) -> Agent:
        return Agent(
            config=self.agents_config["providers_author"],
            llm=self.code_llm,
            tools=["provider_management", "connection_setup"]
        )

    @agent
    def ruff_formatter(self) -> Agent:
        return Agent(
            config=self.agents_config["ruff_formatter"],
            llm=self.code_llm,
            allow_code_execution=True,
            tools=["code_formatting", "style_checking"]
        )

    @agent
    def python_profiler(self) -> Agent:
        return Agent(
            config=self.agents_config["python_profiler"],
            llm=self.code_llm,
            allow_code_execution=True,
            tools=["performance_analysis", "memory_profiling"]
        )

    @agent
    def mock_env(self) -> Agent:
        return Agent(
            config=self.agents_config["mock_env"],
            llm=self.general_llm,
            tools=["environment_setup", "connection_mocking"]
        )

    @start()
    def analyze_dag(self, dag_path: Path) -> dict:
        # To learn more about structured task outputs, 
        # task dependencies, and task callbacks, check out the documentation:
        # https://docs.crewai.com/concepts/tasks#overview-of-a-task
        crew = Crew(
            agents=[self.dag_prognosis(), self.python_profiler(), self.mock_env()],
            tasks=[
                Task(description="Analyze DAG for issues", agent=self.dag_prognosis()),
                Task(description="Check performance metrics", agent=self.python_profiler()),
                Task(description="Validate runtime environment", agent=self.mock_env())
            ]
        )
        return crew.kickoff()

    @listen(analyze_dag)
    def fix_dag(self, dag_path: Path, analysis_result: dict) -> dict:
        crew = Crew(
            agents=[self.lead_author(), self.providers_author(), self.ruff_formatter()],
            tasks=[
                Task(description="Plan DAG fixes", agent=self.lead_author()),
                Task(description="Apply provider updates", agent=self.providers_author()),
                Task(description="Format and validate code", agent=self.ruff_formatter())
            ]
        )
        return crew.kickoff()

    @listen(fix_dag)
    def validate_fixes(self, dag_path: Path, fix_result: dict) -> dict:
        crew = Crew(
            agents=[self.dag_prognosis(), self.python_profiler()],
            tasks=[
                Task(description="Validate fixes", agent=self.dag_prognosis()),
                Task(description="Verify performance", agent=self.python_profiler())
            ]
        )
        return crew.kickoff()

    @start()
    def generate_dag(self, prompt: str) -> dict:
        crew = Crew(
            agents=[self.lead_author(), self.providers_author(), self.dag_prognosis()],
            tasks=[
                Task(description="Generate DAG structure", agent=self.lead_author()),
                Task(description="Setup providers and connections", agent=self.providers_author()),
                Task(description="Validate and optimize", agent=self.dag_prognosis())
            ]
        )
        return crew.kickoff()
