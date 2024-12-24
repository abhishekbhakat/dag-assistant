from pathlib import Path
from typing import Any

import docker
from docker.models.containers import Container
from pydantic import BaseModel


class AirflowVersionConfig(BaseModel):
    """Configuration for Airflow version setup"""

    python_version: str
    airflow_version: str
    providers: dict[str, str]  # provider_name: version


class DockerEnvironmentManager:
    """Manages Docker environment for Airflow testing and profiling"""

    def __init__(self):
        self.client = docker.from_client()
        self.container: Container | None = None

    def build_dockerfile(self, config: AirflowVersionConfig) -> str:
        """Generate Dockerfile content based on configuration"""
        providers_install = "\n".join([f"RUN pip install apache-airflow-providers-{provider}=={version}" for provider, version in config.providers.items()])

        return f"""
FROM python:{config.python_version}-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    linux-perf \
    && rm -rf /var/lib/apt/lists/*

# Install Airflow with specified version
RUN pip install apache-airflow=={config.airflow_version}

# Install providers
{providers_install}

# Install py-spy for profiling
RUN pip install py-spy

# Setup Airflow home
ENV AIRFLOW_HOME=/opt/airflow
RUN mkdir -p /opt/airflow/dags

# Initialize Airflow DB
RUN airflow db init

# Create admin user
RUN airflow users create \
    --username admin \
    --password admin \
    --firstname Anonymous \
    --lastname Admin \
    --role Admin \
    --email admin@example.com

WORKDIR /opt/airflow
"""

    def create_container(self, config: AirflowVersionConfig, dag_path: Path) -> Container:
        """Create and start container with Airflow environment"""
        # Build custom image
        dockerfile_content = self.build_dockerfile(config)
        image_tag = f"airflow-test:{config.airflow_version}-{config.python_version}"

        # Write temporary Dockerfile
        temp_dir = Path("/tmp/airflow-test")
        temp_dir.mkdir(exist_ok=True)

        with open(temp_dir / "Dockerfile", "w") as f:
            f.write(dockerfile_content)

        # Build image
        self.client.images.build(path=str(temp_dir), tag=image_tag, rm=True)

        # Create container
        self.container = self.client.containers.run(
            image_tag,
            detach=True,
            volumes={str(dag_path): {"bind": "/opt/airflow/dags/dag.py", "mode": "ro"}},
            cap_add=["SYS_PTRACE"],
            command="tail -f /dev/null",  # Keep container running
        )

        return self.container

    def execute_command(self, command: list[str]) -> tuple[str, str]:
        """Execute command in container"""
        if not self.container:
            raise RuntimeError("Container not initialized")

        exit_code, output = self.container.exec_run(command)
        return exit_code, output.decode()

    def run_py_spy(self, pid: int, duration: int = 60) -> str:
        """Run py-spy on specified process"""
        if not self.container:
            raise RuntimeError("Container not initialized")

        cmd = ["py-spy", "record", "--pid", str(pid), "--output", "/tmp/profile.svg", "--duration", str(duration), "--rate", "1000"]

        self.execute_command(cmd)

        # Copy profile data from container
        bits, stat = self.container.get_archive("/tmp/profile.svg")
        # TODO: Save profile data to file
        return "/tmp/profile.svg"

    def get_performance_metrics(self, pid: int, duration: int = 60) -> dict[str, Any]:
        """Collect comprehensive performance metrics for analysis.

        This expands on py-spy by collecting:
        - CPU utilization per function/task
        - Memory allocation patterns
        - I/O operations and wait times
        - Database query patterns and timing
        - Task scheduling overhead
        - XCom operation timing
        - Lock contention points

        Returns structured metrics suitable for LLM analysis.
        """
        metrics = {
            "cpu": self._get_cpu_metrics(pid),
            "memory": self._get_memory_metrics(pid),
            "io": self._get_io_metrics(pid),
            "db": self._get_db_metrics(pid),
            "scheduling": self._get_scheduling_metrics(pid),
            "profiling": self._get_profiling_data(pid, duration),
            "summary": {"bottlenecks": [], "recommendations": []},
        }

        return metrics

    def _get_cpu_metrics(self, pid: int) -> dict[str, Any]:
        """Collect CPU utilization metrics per function/task."""
        cmd = ["ps", "-p", str(pid), "-o", "%cpu,cputime"]
        # TODO: Leave as is for now - these are placeholder methods that will need the variables when fully implemented. We'll fix these unused variables when implementing the actual metrics collection logic.
        exit_code, output = self.execute_command(cmd)

        # Parse ps output
        cpu_metrics = {"utilization_percent": 0.0, "execution_time": "", "hotspots": []}

        # Add CPU profiling data
        cmd = ["perf", "stat", "-p", str(pid)]
        self.execute_command(cmd)

        return cpu_metrics

    def _get_memory_metrics(self, pid: int) -> dict[str, Any]:
        """Analyze memory usage patterns."""
        cmd = ["ps", "-p", str(pid), "-o", "rss,vsz"]
        exit_code, output = self.execute_command(cmd)

        memory_metrics = {"rss_mb": 0, "virtual_mb": 0, "allocations": [], "leaks": [], "large_objects": []}

        # Add memory profiling data
        cmd = ["gdb", "--pid", str(pid), "-batch", "-ex", "info malloc"]
        self.execute_command(cmd)

        return memory_metrics

    def _get_io_metrics(self, pid: int) -> dict[str, Any]:
        """Collect I/O operation metrics."""
        cmd = ["iotop", "-p", str(pid), "-b", "-n", "1"]
        exit_code, output = self.execute_command(cmd)

        io_metrics = {"read_bytes": 0, "write_bytes": 0, "io_wait": 0.0, "patterns": {"sequential_reads": 0, "random_reads": 0, "write_patterns": []}}

        return io_metrics

    def _get_db_metrics(self, pid: int) -> dict[str, Any]:
        """Analyze database operations."""
        db_metrics = {"queries": [], "connection_patterns": [], "transaction_time": [], "slow_queries": []}

        # Parse SQLite query log if enabled
        cmd = ["sqlite3", ".airflow/airflow.db", ".expert"]
        self.execute_command(cmd)

        return db_metrics

    def _get_scheduling_metrics(self, pid: int) -> dict[str, Any]:
        """Analyze task scheduling patterns."""
        scheduling_metrics = {"dag_file_parse_time": 0.0, "task_instances": [], "queue_metrics": {"waiting_time": [], "execution_time": [], "overlaps": []}}

        return scheduling_metrics

    def _get_profiling_data(self, pid: int, duration: int) -> dict[str, Any]:
        """Get detailed profiling data from py-spy."""
        profile_path = self.run_py_spy(pid, duration)

        profiling_data = {"flame_graph": profile_path, "call_patterns": [], "execution_paths": [], "bottlenecks": []}

        return profiling_data

    def cleanup(self):
        """Stop and remove container"""
        if self.container:
            self.container.stop()
            self.container.remove()
            self.container = None
