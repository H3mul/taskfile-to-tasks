"""
Core converter module for TaskfileToTasks.

This module contains the main TaskfileToTasks class for converting
Taskfile.yml files to tasks.json format for various editors.
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    raise ImportError("PyYAML is required. Install it with: pip install PyYAML")


def parse_yaml_option(option_str: str) -> Dict[str, Any]:
    """Parse a YAML option string into a dictionary.

    Examples:
        "use_new_terminal: true" -> {"use_new_terminal": True}
        "cwd: /tmp" -> {"cwd": "/tmp"}

    Args:
        option_str: A YAML key-value pair as a string

    Returns:
        A dictionary with the parsed key-value pair

    Raises:
        ValueError: If the option string is not valid YAML or is not a key-value pair
    """
    try:
        # Wrap in braces to make it valid YAML
        data = yaml.safe_load("{" + option_str + "}")
        if not isinstance(data, dict):
            raise ValueError(f"Option must be a valid key-value pair: {option_str}")
        return data
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML option: {option_str}\n{e}")


def merge_options(base: Dict[str, Any], extra: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge extra options into the base options dictionary.

    Later options override earlier ones.

    Args:
        base: The base options dictionary
        extra: List of dictionaries to merge in order

    Returns:
        A merged dictionary with all options
    """
    result = base.copy()
    for extra_dict in extra:
        result.update(extra_dict)
    return result


class TaskfileToTasks:
    """Convert Taskfile.yml to tasks.json format for various editors."""

    def __init__(
        self,
        source_file: Optional[str] = None,
        output_dir: Optional[str] = None,
        editor: str = "zed",
        skip_tasks: Optional[List[str]] = None,
        extra_zed_options: Optional[List[str]] = None,
        extra_vscode_options: Optional[List[str]] = None,
        verbose: bool = False,
    ):
        """Initialize the converter.

        Args:
            source_file: Path to Taskfile.yml (defaults to git root)
            output_dir: Output directory for tasks.json (defaults to editor config dir)
            editor: Target editor - "vscode" or "zed"
            skip_tasks: List of task IDs to skip
            extra_zed_options: List of YAML option strings to merge with Zed tasks
            extra_vscode_options: List of YAML option strings to merge with VSCode presentation
            verbose: Enable verbose output

        Raises:
            ValueError: If editor is not "vscode" or "zed"
            FileNotFoundError: If Taskfile.yml cannot be found
        """
        self.editor = editor.lower()
        if self.editor not in ("vscode", "zed"):
            raise ValueError("Editor must be 'vscode' or 'zed'")

        self.skip_tasks = skip_tasks or []
        self.verbose = verbose
        self.source_file = self._resolve_source_file(source_file)
        self.output_dir = self._resolve_output_dir(output_dir)
        self.task_command = self._find_task_command()

        # Parse extra options
        self.extra_zed_options = self._parse_extra_options(extra_zed_options or [])
        self.extra_vscode_options = self._parse_extra_options(
            extra_vscode_options or []
        )

    def _log(self, message: str) -> None:
        """Log a message if verbose mode is enabled.

        Args:
            message: The message to log
        """
        if self.verbose:
            print(message)

    def _find_task_command(self) -> str:
        """Find the available task command.

        Tries to find either 'task' or 'go-task' in the system PATH.

        Returns:
            The command name ('task' or 'go-task')

        Raises:
            RuntimeError: If neither command is found
        """
        for cmd in ["task", "go-task"]:
            try:
                subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    check=True,
                    timeout=5,
                )
                self._log(f"Found task command: {cmd}")
                return cmd
            except (
                subprocess.CalledProcessError,
                FileNotFoundError,
                PermissionError,
                subprocess.TimeoutExpired,
            ):
                continue

        raise RuntimeError(
            "Neither 'task' nor 'go-task' command found. "
            "Please install go-task: https://taskfile.dev/installation"
        )

    def _parse_extra_options(self, options: List[str]) -> List[Dict[str, Any]]:
        """Parse a list of YAML option strings.

        Args:
            options: List of YAML option strings

        Returns:
            List of parsed option dictionaries

        Raises:
            ValueError: If any option string is invalid
        """
        parsed = []
        for option in options:
            try:
                parsed.append(parse_yaml_option(option))
            except ValueError as e:
                raise ValueError(f"Failed to parse extra option: {e}")
        return parsed

    def _resolve_source_file(self, source_file: Optional[str]) -> Path:
        """Resolve the Taskfile.yml path.

        Searches in this order:
        1. Provided source_file path
        2. Git repository root
        3. Current directory

        Args:
            source_file: Optional explicit path to Taskfile.yml

        Returns:
            Resolved Path to Taskfile.yml

        Raises:
            FileNotFoundError: If Taskfile.yml cannot be found
        """
        if source_file:
            path = Path(source_file)
            if path.exists():
                return path.resolve()
            raise FileNotFoundError(f"Taskfile not found: {source_file}")

        # Try to find Taskfile.yml in git root
        try:
            git_root = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            taskfile = Path(git_root) / "Taskfile.yml"
            if taskfile.exists():
                self._log(f"Found Taskfile.yml in git root: {taskfile}")
                return taskfile.resolve()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Try current directory
        taskfile = Path("Taskfile.yml")
        if taskfile.exists():
            self._log(f"Found Taskfile.yml in current directory: {taskfile}")
            return taskfile.resolve()

        raise FileNotFoundError(
            "Taskfile.yml not found. Provide explicit path with --source or "
            "ensure it exists in git root or current directory."
        )

    def _resolve_output_dir(self, output_dir: Optional[str]) -> Path:
        """Resolve the output directory path.

        Args:
            output_dir: Optional explicit output directory

        Returns:
            Resolved Path to output directory (created if necessary)
        """
        if output_dir:
            path = Path(output_dir)
            path.mkdir(parents=True, exist_ok=True)
            self._log(f"Using custom output directory: {path}")
            return path.resolve()

        if self.editor == "zed":
            path = Path(".zed")
        else:
            path = Path(".vscode")

        path.mkdir(parents=True, exist_ok=True)
        self._log(f"Using default output directory: {path}")
        return path.resolve()

    def _load_taskfile(self) -> List[Dict[str, Any]]:
        """Load all tasks using 'task --list-all --json' or 'go-task --list-all --json'.

        Runs the task command in the Taskfile's directory to get all tasks
        including those from included Taskfiles.

        Returns:
            List of task dictionaries from task command output

        Raises:
            RuntimeError: If task command fails
            ValueError: If output is not valid JSON
        """
        try:
            # Run task command in the Taskfile's directory
            taskfile_dir = self.source_file.parent
            result = subprocess.run(
                [self.task_command, "--list-all", "--json"],
                cwd=taskfile_dir,
                capture_output=True,
                text=True,
                check=True,
            )

            tasks_data = json.loads(result.stdout)
            if not isinstance(tasks_data, dict) or "tasks" not in tasks_data:
                raise ValueError(
                    "Expected task output to be a dictionary with 'tasks' key"
                )
            tasks_data = tasks_data["tasks"]
            if not isinstance(tasks_data, list):
                raise ValueError("Expected task output to be a list of tasks")

            self._log(f"Loaded {len(tasks_data)} task(s) from task command")
            return tasks_data
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to run '{self.task_command} --list-all --json': {e.stderr}"
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from task command: {e}")

    def _extract_tasks(self, tasks_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract tasks from task command output.

        Args:
            tasks_data: List of task dictionaries from 'task --list-all --json'

        Returns:
            List of extracted task dictionaries

        Raises:
            ValueError: If tasks_data is not a list
        """
        if not isinstance(tasks_data, list):
            raise ValueError("Expected tasks_data to be a list")

        extracted = []
        for task in tasks_data:
            if not isinstance(task, dict):
                continue

            task_id = task.get("task", "")
            if not task_id or task_id in self.skip_tasks:
                if task_id in self.skip_tasks:
                    self._log(f"Skipping task: {task_id}")
                continue

            # Extract description and command from task
            name = task.get("name", task_id)
            desc = task.get("desc", "")

            extracted.append(
                {
                    "id": task_id,
                    "label": task_id,
                    "description": desc,
                }
            )

        return extracted

    def _generate_vscode_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate VSCode tasks.json format.

        Args:
            tasks: List of extracted task dictionaries

        Returns:
            Dictionary in VSCode tasks.json format
        """
        vscode_tasks = []

        # Default VSCode presentation options
        default_options = {
            "echo": True,
            "reveal": "always",
            "focus": False,
            "panel": "shared",
        }

        # Merge with extra options
        presentation = merge_options(default_options, self.extra_vscode_options)

        for task in tasks:
            vscode_task = {
                "label": task["label"],
                "type": "shell",
                "command": self.task_command,
                "args": [task["id"]],
                "presentation": presentation,
                "group": {"kind": "build", "isDefault": False},
            }
            if task["description"]:
                vscode_task["description"] = task["description"]

            vscode_tasks.append(vscode_task)

        return {
            "version": "2.0.0",
            "tasks": vscode_tasks,
        }

    def _generate_zed_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate Zed tasks.json format.

        Args:
            tasks: List of extracted task dictionaries

        Returns:
            List of task dictionaries in Zed format
        """
        zed_tasks = []

        # Default Zed task options
        default_options = {"use_new_terminal": True}

        # Merge with extra options
        extra_merged = merge_options(default_options, self.extra_zed_options)

        for task in tasks:
            task_label = (
                f"{task['id']} - {task['description']}"
                if task["description"]
                else task["id"]
            )
            zed_task = {
                "label": task_label,
                "command": self.task_command,
                "args": [task["id"]],
            }

            # Merge extra options into each task
            zed_task.update(extra_merged)

            zed_tasks.append(zed_task)

        return zed_tasks

    def convert(self) -> Optional[Path]:
        """Convert Taskfile.yml to tasks.json and write to disk.

        Returns:
            Path to the generated tasks.json file, or None if no tasks found

        Raises:
            RuntimeError: If task command fails
            ValueError: If task output is invalid
        """
        print(f"Reading tasks from: {self.source_file}")
        tasks_data = self._load_taskfile()

        print("Extracting tasks...")
        tasks = self._extract_tasks(tasks_data)

        if not tasks:
            print("Warning: No tasks found")
            return None

        print(f"Found {len(tasks)} task(s)")

        if self.editor == "vscode":
            output_data = self._generate_vscode_tasks(tasks)
        else:
            output_data = self._generate_zed_tasks(tasks)

        output_file = self.output_dir / "tasks.json"

        # Write tasks.json
        print(f"Writing tasks to: {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

        print(f"✓ Successfully generated {self.editor.upper()} tasks.json")
        return output_file

    def get_tasks_summary(self) -> List[Dict[str, str]]:
        """Get a summary of extracted tasks without writing to disk.

        Returns:
            List of dictionaries with 'id' and 'description' keys
        """
        taskfile = self._load_taskfile()
        tasks = self._extract_tasks(taskfile)
        return [
            {"id": task["id"], "description": task["description"]} for task in tasks
        ]

    def print_tasks_summary(self) -> None:
        """Print a formatted summary of the extracted tasks."""
        tasks = self.get_tasks_summary()

        if not tasks:
            print("No tasks found")
            return

        print(f"\n{'Task ID':<20} {'Description':<50}")
        print("-" * 70)
        for task in tasks:
            desc = task["description"]
            if len(desc) > 50:
                desc = desc[:47] + "..."
            print(f"{task['id']:<20} {desc:<50}")
        print()
