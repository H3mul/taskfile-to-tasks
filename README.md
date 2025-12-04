# taskfile-to-tasks

Convert your `Taskfile.yml` to `tasks.json` format for VSCode or Zed, keeping your Taskfile as the single source of truth for task definitions while enabling convenient task execution directly from your editor.

## Overview

This tool bridges the gap between [Task](https://taskfile.dev/) (a task runner similar to Make) and editor-specific task systems. Instead of maintaining separate task configurations for your editor, you define all tasks once in `Taskfile.yml` and this script automatically generates the appropriate editor task configuration.

**Supported Editor Tasks:**
- **Zed** `.zed/tasks.json`
- **VSCode** `.vscode/tasks.json`

The generated `tasks.json` files are dummy tasks that share Taskfile task names and call the Go-Task CLI directly

### Basic Usage without Installation

Clone the repository and run the CLI directly:

```bash
git clone https://github.com/H3mul/taskfile-to-tasks.git
cd taskfile-to-tasks
```

Convert your Taskfile.yml to Zed tasks.json (default):
```bash
python taskfile_to_tasks.cli
```

Convert to VSCode tasks.json:
```bash
python taskfile_to_tasks.cli --editor vscode
```

## Installation

### Using pip

```
pip install git+https://github.com/H3mul/taskfile-to-tasks.git
```

### Using AUR (Arch Linux)

```
yay -S taskfile-to-tasks-python-git
```

For more information, visit the [AUR package page](https://aur.archlinux.org/packages/taskfile-to-tasks-python-git).

## Usage


### Command-Line Options

```
usage: taskfile-to-tasks [-h] [--version] [--editor {vscode,zed}] [--source SOURCE] [--output OUTPUT]
                       [--skip-tasks SKIP_TASKS [SKIP_TASKS ...]] [--skip-task-pattern REGEX]
                       [--task-cmd TASK_CMD] [--extra-zed-options YAML] [--extra-vscode-options YAML]
                       [--preview] [--verbose]

Convert Taskfile.yml to tasks.json for VSCode or Zed

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --editor {vscode,zed}
                        Target editor (default: zed)
  --source SOURCE       Path to Taskfile.yml (default: auto-detect from git root or current directory)
  --output OUTPUT       Output directory for tasks.json (default: .zed/ or .vscode/)
  --skip-tasks SKIP_TASKS [SKIP_TASKS ...]
                        Task IDs to skip
  --skip-task-pattern REGEX
                        Regex pattern for task IDs to skip (can be used multiple times).
                        Example: '^test_' to skip all tasks starting with 'test_'
  --task-cmd TASK_CMD   Task command to use in generated tasks.json (e.g., 'task', 'go-task').
                        Useful when the running platform differs from the target platform.
                        Default: auto-detected from system
  --extra-zed-options YAML
                        Extra YAML options for Zed tasks (can be used multiple times). Example: 'use_new_terminal: true'
  --extra-vscode-options YAML
                        Extra YAML options for VSCode presentation (can be used multiple times). Example: 'reveal: silent'
  --preview             Preview tasks without generating tasks.json
  --verbose             Enable verbose output
```

### Examples

**Preview tasks before generating:**
```bash
taskfile-to-tasks --preview
```

**Generate Zed tasks from custom Taskfile location:**
```bash
taskfile-to-tasks --source /path/to/Taskfile.yml --output ./editor-config
```

**Skip specific tasks:**
```bash
taskfile-to-tasks --skip-tasks build test lint
```

**Skip tasks by regex pattern:**
```bash
taskfile-to-tasks --skip-task-pattern '^test_'
```

**Skip multiple regex patterns:**
```bash
taskfile-to-tasks --skip-task-pattern '^test_' --skip-task-pattern '.*:setup$'
```

**Use custom task command for tasks.json:**
```bash
taskfile-to-tasks --task-cmd "go-task"
```

**Combine skip patterns with custom task command:**
```bash
taskfile-to-tasks --task-cmd "go-task" --skip-task-pattern 'debug.*'
```

**Add Zed-specific options:**
```bash
taskfile-to-tasks --extra-zed-options "use_new_terminal: true"
```

**Multiple Zed options:**
```bash
taskfile-to-tasks \
  --extra-zed-options "use_new_terminal: true" \
  --extra-zed-options "cwd: /tmp"
```

**VSCode with custom presentation:**
```bash
taskfile-to-tasks --editor vscode \
  --extra-vscode-options "reveal: silent" \
  --extra-vscode-options "echo: false"
```

## How It Works

### Input: Taskfile.yml Structure

```yaml
tasks:
  build:
    desc: "Build the project"
    cmds:
      - echo "Building..."
      - make build

  test:
    desc: "Run tests"
    cmds:
      - pytest tests/

  deploy:
    desc: "Deploy to production"
    cmds:
      - ./scripts/deploy.sh
```

### Output: Generated tasks.json

**For Zed:**
```json
[
  {
    "label": "build - Build the project",
    "command": "task",
    "args": ["build"],
    "use_new_terminal": true
  },
  {
    "label": "test - Run tests",
    "command": "task",
    "args": ["test"],
    "use_new_terminal": true
  }
]
```

**For VSCode:**
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "build",
      "type": "shell",
      "command": "task",
      "args": ["build"],
      "description": "Build the project",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "group": {
        "kind": "build",
        "isDefault": false
      }
    }
  ]
}
```

## Configuration Details

### Auto-Detection

The script automatically detects your Taskfile.yml in this order:
1. Explicit `--source` path (if provided)
2. Git repository root (via `git rev-parse --show-toplevel`)
3. Current working directory

Output directory defaults:
- **Zed**: `.zed/` directory
- **VSCode**: `.vscode/` directory

### Default Options

**Zed defaults:**
- `use_new_terminal: true` - Each task opens in a new terminal

**VSCode defaults:**
- `echo: true` - Echo commands to output
- `reveal: "always"` - Reveal terminal panel
- `focus: false` - Don't focus the terminal
- `panel: "shared"` - Share terminal panel between tasks

### Custom Options

You can override defaults by passing YAML key-value pairs:

```bash
# Zed: Use same terminal for all tasks
taskfile-to-tasks --extra-zed-options "use_new_terminal: false"

# VSCode: Silently execute tasks
taskfile-to-tasks --editor vscode --extra-vscode-options "reveal: silent"
```

## Workflow Integration

### Recommended Setup

1. **Commit configuration**: Add the generated tasks.json to version control:
   ```bash
   git add .zed/tasks.json  # or .vscode/tasks.json
   git commit -m "Add editor tasks from Taskfile.yml"
   ```

2. **Update CI/CD**: Add a step to regenerate tasks.json when Taskfile.yml changes:
   ```yaml
   # Example GitHub Actions
   - name: Sync Taskfile to tasks.json
     run: taskfile-to-tasks
   ```

3. **Local development**: Run the script when you modify Taskfile.yml:
   ```bash
   taskfile-to-tasks
   ```

## Advanced Features

### Skip Tasks by Pattern

The `--skip-task-pattern` flag allows you to skip tasks using regex patterns. This is useful for filtering out categories of tasks without listing each one individually.

**Examples:**
```bash
# Skip all tasks starting with 'test_'
taskfile-to-tasks --skip-task-pattern '^test_'

# Skip all tasks ending with ':setup'
taskfile-to-tasks --skip-task-pattern '.*:setup$'

# Skip multiple patterns
taskfile-to-tasks --skip-task-pattern '^debug_' --skip-task-pattern '.*:cleanup$'

# Combine with exact task skip
taskfile-to-tasks --skip-tasks build deploy --skip-task-pattern 'experimental_.*'
```

**Pattern Syntax:**
Patterns use standard Python regex syntax. Some common examples:
- `^prefix_` - Tasks starting with "prefix_"
- `.*suffix$` - Tasks ending with "suffix"
- `.*cleanup.*` - Tasks containing "cleanup"
- `(test|debug)_.*` - Tasks matching either "test_" or "debug_"

### Cross-Platform Task Commands

The `--task-cmd` flag allows you to specify a custom task command for the generated `tasks.json`. This is particularly useful when:

1. **Your development environment differs from your target environment**: For example, you might run the build script on Linux but target macOS with `go-task`.
2. **Using different task runner installations**: Specify `task`, `go-task`, or any other task command.
3. **Team consistency**: Ensure all team members use the same task command in their editors, regardless of their local setup.

**How it works:**
- The script **auto-detects** the task command on your current system (used to load/parse Taskfile.yml)
- The `--task-cmd` flag **overrides** only the command used in the generated tasks.json
- This separation allows cross-platform task generation

**Examples:**
```bash
# Use 'go-task' in tasks.json (running on Linux, targeting macOS)
taskfile-to-tasks --task-cmd "go-task"

# VSCode with custom task command
taskfile-to-tasks --editor vscode --task-cmd "go-task"

# Zed with go-task and custom options
taskfile-to-tasks --editor zed --task-cmd "go-task" --extra-zed-options "use_new_terminal: false"
```

**Generated Output Difference:**

Without `--task-cmd`:
```json
{
  "label": "build",
  "command": "task",
  "args": ["build"]
}
```

With `--task-cmd "go-task"`:
```json
{
  "label": "build",
  "command": "go-task",
  "args": ["build"]
}
```

## Troubleshooting

### Taskfile.yml not found
**Error:** `FileNotFoundError: Taskfile.yml not found...`

**Solution:** Ensure Taskfile.yml exists in your git root or current directory, or use `--source` to specify the path.

### Invalid YAML in options
**Error:** `Invalid YAML option: ...`

**Solution:** Ensure option strings are valid YAML key-value pairs:
```bash
# ✓ Correct
--extra-zed-options "use_new_terminal: true"

# ✗ Incorrect
--extra-zed-options "use_new_terminal true"
```

### Invalid regex pattern
**Error:** `Invalid regex pattern '...' ...`

**Solution:** Ensure your `--skip-task-pattern` uses valid regex syntax. Test your pattern:
```bash
# ✓ Correct regex
taskfile-to-tasks --skip-task-pattern '^test_'

# ✗ Incorrect regex (unmatched bracket)
taskfile-to-tasks --skip-task-pattern '[incomplete'
```

### Task command not found
**Error:** `Neither 'task' nor 'go-task' command found...`

**Solution:** Install the task runner or use `--task-cmd` to specify a custom command path:
```bash
# Install go-task
brew install go-task  # macOS
apt install go-task   # Linux

# Or specify explicit path
taskfile-to-tasks --task-cmd "/usr/local/bin/task"
```
