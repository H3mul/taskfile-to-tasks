"""Command-line interface for TaskfileToTasks."""

import argparse
import sys
from typing import Optional

import yaml

from taskfile_to_tasks.converter import TaskfileToTasks


def create_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser.

    Returns:
        ArgumentParser configured with all CLI options
    """
    parser = argparse.ArgumentParser(
        prog="TaskfileToTasks",
        description="Convert Taskfile.yml to tasks.json for VSCode or Zed",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert to Zed (default)
  TaskfileToTasks.py

  # Convert to VSCode
  TaskfileToTasks.py --editor vscode

  # Use custom Taskfile location
  TaskfileToTasks.py --source /path/to/Taskfile.yml

  # Output to custom directory
  TaskfileToTasks.py --output /path/to/output

  # Skip specific tasks
  TaskfileToTasks.py --skip-tasks build test lint

  # Add Zed-specific options
  TaskfileToTasks.py --extra-zed-options "use_new_terminal: true"

  # Add multiple Zed options
  TaskfileToTasks.py \\
    --extra-zed-options "use_new_terminal: true" \\
    --extra-zed-options "cwd: /tmp"

  # Add VSCode options
  TaskfileToTasks.py --editor vscode \\
    --extra-vscode-options "reveal: silent"

  # Preview tasks without generating
  TaskfileToTasks.py --preview

  # Verbose output
  TaskfileToTasks.py --verbose
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    parser.add_argument(
        "--editor",
        choices=["vscode", "zed"],
        default="zed",
        help="Target editor (default: %(default)s)",
    )

    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Path to Taskfile.yml (default: auto-detect from git root or current directory)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory for tasks.json (default: .zed/ or .vscode/)",
    )

    parser.add_argument(
        "--skip-tasks",
        type=str,
        nargs="+",
        default=[],
        help="Task IDs to skip",
    )

    parser.add_argument(
        "--extra-zed-options",
        type=str,
        action="append",
        default=[],
        metavar="YAML",
        help="Extra YAML options for Zed tasks (can be used multiple times). "
        "Example: 'use_new_terminal: true'",
    )

    parser.add_argument(
        "--extra-vscode-options",
        type=str,
        action="append",
        default=[],
        metavar="YAML",
        help="Extra YAML options for VSCode presentation (can be used multiple times). "
        "Example: 'reveal: silent'",
    )

    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview tasks without generating tasks.json",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    return parser


def main(argv: Optional[list] = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        converter = TaskfileToTasks(
            source_file=args.source,
            output_dir=args.output,
            editor=args.editor,
            skip_tasks=args.skip_tasks,
            extra_zed_options=args.extra_zed_options,
            extra_vscode_options=args.extra_vscode_options,
            verbose=args.verbose,
        )

        if args.preview:
            converter.print_tasks_summary()
        else:
            converter.convert()

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())