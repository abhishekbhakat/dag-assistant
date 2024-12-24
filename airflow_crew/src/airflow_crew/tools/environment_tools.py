from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from airflow_crew.tools.support.docker_manager import AirflowVersionConfig, DockerEnvironmentManager


class EnvironmentSetupInput(BaseModel):
    """Input schema for EnvironmentSetupTool"""

    config: AirflowVersionConfig = Field(..., description="Airflow version configuration")
    dag_path: Path | None = Field(None, description="Optional DAG file path")


class EnvironmentSetupTool(BaseTool):
    """Tool for setting up Airflow Docker environments"""

    name: str = "environment_setup"
    description: str = "Setup Docker environment for Airflow testing and profiling"
    args_schema: type[BaseModel] = EnvironmentSetupInput

    def __init__(self):
        super().__init__()
        self.docker_manager = DockerEnvironmentManager()

    def _run(self, config: AirflowVersionConfig, dag_path: Path | None = None) -> dict[str, Any]:
        """Setup Docker environment with specified configuration"""
        try:
            # Create container
            container = self.docker_manager.create_container(config, dag_path)

            # Verify Airflow installation
            exit_code, version_output = self.docker_manager.execute_command(["airflow", "version"])

            if exit_code != 0:
                return {"success": False, "error": f"Failed to verify Airflow installation: {version_output}"}

            # Verify providers installation if specified
            provider_status = {}
            for provider in config.providers:
                exit_code, provider_output = self.docker_manager.execute_command(["pip", "show", f"apache-airflow-providers-{provider}"])
                provider_status[provider] = {"installed": exit_code == 0, "details": provider_output if exit_code == 0 else None, "error": provider_output if exit_code != 0 else None}

            return {"success": True, "container_id": container.id, "airflow_version": version_output.strip(), "providers": provider_status}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def cleanup(self):
        """Cleanup Docker resources"""
        self.docker_manager.cleanup()
