from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from airflow_crew.tools.support.docker_manager import AirflowVersionConfig, DockerEnvironmentManager


class CLIOperationsInput(BaseModel):
    """Input schema for CLIOperationsTool."""

    command: str = Field(..., description="Airflow CLI command to execute")
    config: AirflowVersionConfig = Field(..., description="Airflow version configuration")
    dag_path: Path = Field(..., description="Path to DAG file")


class CLIOperationsTool(BaseTool):
    """Airflow CLI operations tool"""

    name: str = "cli_operations"
    description: str = "Execute Airflow CLI commands in Docker environment"
    args_schema: type[BaseModel] = CLIOperationsInput

    def __init__(self):
        super().__init__()
        self.docker_manager = DockerEnvironmentManager()

    def _run(self, command: str, config: AirflowVersionConfig, dag_path: Path) -> dict[str, Any]:
        try:
            # Create container if not exists
            if not self.docker_manager.container:
                self.docker_manager.create_container(config, dag_path)

            # Execute command
            exit_code, output = self.docker_manager.execute_command(command.split())

            return {"success": exit_code == 0, "output": output, "error": None if exit_code == 0 else output}

        except Exception as e:
            return {"success": False, "output": None, "error": str(e)}

    def cleanup(self):
        """Cleanup Docker resources"""
        self.docker_manager.cleanup()


class EnvironmentSetupInput(BaseModel):
    """Input schema for EnvironmentSetupTool."""

    config: dict = Field(..., description="Config for environment setup")


class EnvironmentSetupTool(BaseTool):
    """Test environment setup tool"""

    name: str = "environment_setup"
    description: str = "Setup test environment for Airflow"
    args_schema: type[BaseModel] = EnvironmentSetupInput

    def _run(self, config: dict) -> dict:
        # Implementation goes here
        pass
