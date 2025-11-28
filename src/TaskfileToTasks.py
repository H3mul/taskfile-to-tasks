#!/usr/bin/env python3
"""Command-line interface for TaskfileToTasks.

This script serves as the entry point for running TaskfileToTasks from the command line.
"""

import sys

from taskfile_to_tasks.cli import main

if __name__ == "__main__":
    sys.exit(main())