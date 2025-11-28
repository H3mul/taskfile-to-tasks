"""TaskfileToTasks - Convert Taskfile.yml to tasks.json for VSCode or Zed."""

__version__ = "1.0.0"
__author__ = "H3mul"
__license__ = "MIT"

from .converter import TaskfileToTasks, parse_yaml_option, merge_options

__all__ = [
    "TaskfileToTasks",
    "parse_yaml_option",
    "merge_options",
]