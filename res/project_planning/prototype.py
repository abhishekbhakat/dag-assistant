from crewai import Agent, Task, Crew, Process
from textwrap import dedent

# Agents
dag_prognosis = Agent(
    role="DAG Analyzer",
    goal="Analyze DAG code for issues and improvements",
    backstory=dedent(
        """
        Expert in Apache Airflow DAG analysis.
        Focuses on code quality, patterns and anti-patterns.
    """
    ),
    tools=["static_analysis", "pattern_detection"],
)

lead_author = Agent(
    role="Lead DAG Author",
    goal="Coordinate DAG modifications and generation",
    backstory=dedent(
        """
        Senior Airflow developer who coordinates all DAG changes.
        Ensures best practices and consistency.
    """
    ),
    tools=["code_generation", "code_review"],
)

mock_env = Agent(
    role="Environment Manager",
    goal="Manage test Airflow environment",
    backstory=dedent(
        """
        DevOps expert who manages isolated Airflow environments.
        Handles connections, variables and runtime validation.
    """
    ),
    tools=["docker", "airflow_api"],
)

# Tasks
analyze_task = Task(
    description="Analyze DAG for issues",
    agent=dag_prognosis,
    expected_output="List of issues and recommendations",
)

fix_task = Task(
    description="Fix identified issues",
    agent=lead_author,
    expected_output="Updated DAG code",
)

validate_task = Task(
    description="Validate changes in test environment",
    agent=mock_env,
    expected_output="Validation report",
)

# Crew
dag_crew = Crew(
    agents=[dag_prognosis, lead_author, mock_env],
    tasks=[analyze_task, fix_task, validate_task],
    process=Process.sequential,
)

# Example Usage
if __name__ == "__main__":
    result = dag_crew.kickoff()
    print(result)
