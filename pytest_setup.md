# Setting up Pytest with VS Code

This guide will walk you through configuring your Python project in VS Code to properly discover, run, and debug Pytest test cases.

## Prerequisites

*   **Python Extension for VS Code:** Ensure you have the official Microsoft Python extension installed in VS Code.
*   **Pytest Installed:** Make sure `pytest` is installed in your project's virtual environment (`pip install pytest`).

## Step 1: Configure Pytest to find your `src` directory

If your source code is in a `src` directory (or similar), Pytest might not find your modules. You can fix this by adding your project root to Python's path within Pytest's configuration.

Open or create `pyproject.toml` in your project's root directory and add the following section:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

**Explanation:**
*   `[tool.pytest.ini_options]` is the standard way to configure Pytest within `pyproject.toml`.
*   `pythonpath = ["."]` tells Pytest to add the current directory (your project root) to the Python import path when running tests. This allows imports like `from src.my_module import ...` to resolve correctly.

## Step 2: Configure VS Code's Python Test Settings

VS Code needs to know that you're using Pytest and where your tests are located.

Open or create `.vscode/settings.json` in your project's root directory and add/update the following:

```json
{
    "python.testing.pytestArgs": [
        "tests" // This tells VS Code where your test files are located (e.g., in a 'tests' folder)
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true
}
```

**Explanation:**
*   `"python.testing.pytestArgs": ["tests"]`: Specifies the directory where your tests are located. Adjust `"tests"` if your test files are in a different folder (e.g., `"test"` or `"."` for the project root).
*   `"python.testing.unittestEnabled": false`: Disables the built-in `unittest` discovery.
*   `"python.testing.pytestEnabled": true`: Enables Pytest discovery and execution.

## Step 3: Configure VS Code's Debugging Launch Settings

To enable debugging with the "play" button next to your test functions, you need a `launch.json` file.

Open or create `.vscode/launch.json` in your project's root directory and add the following configuration:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Python: Pytest",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/.venv/bin/pytest", // Adjust this path if your virtual environment is elsewhere
            "args": [
                "${file}" // This will run the tests in the currently open file
            ],
            "console": "integratedTerminal",
            "justMyCode": true,
            "env": {
                "PYTHONPATH": "${workspaceFolder}" // Ensures Python can find your project modules
            }
        }
    ]
}
```

**Explanation:**
*   `"name": "Python: Pytest"`: The name of the debug configuration that will appear in the VS Code debug dropdown.
*   `"type": "python"`: Specifies that this is a Python debugging configuration.
*   `"request": "launch"`: Indicates that this configuration will launch a new process.
*   `"program": "${workspaceFolder}/.venv/bin/pytest"`: The absolute path to your Pytest executable within your virtual environment. **IMPORTANT:** Adjust `.venv/bin/pytest` if your virtual environment is named differently or located elsewhere (e.g., `venv/Scripts/pytest` on Windows).
*   `"args": ["${file}"]`: When you click the "play" button next to a test, this argument tells Pytest to run only the tests in the currently open file.
*   `"console": "integratedTerminal"`: Runs the tests in VS Code's integrated terminal.
*   `"justMyCode": true`: (Optional) If `true`, the debugger will only step through your code and skip stepping into library code. Set to `false` if you need to debug into third-party libraries.
*   `"env": {"PYTHONPATH": "${workspaceFolder}"}`: Sets the `PYTHONPATH` environment variable to your project's root directory. This is crucial for Python to correctly resolve imports from your `src` directory or other project-specific modules.

## Step 4: Activate your Virtual Environment

Before running tests or debugging, ensure your virtual environment is activated in the VS Code terminal. You can select your Python interpreter by pressing `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) and typing "Python: Select Interpreter". Choose the interpreter associated with your project's virtual environment.

## Running and Debugging Tests

1.  **Open a Test File:** Navigate to one of your test files (e.g., `tests/test_augmenters.py`).
2.  **Discover Tests:** VS Code should automatically discover your tests. You can also manually trigger test discovery from the "Testing" view in the Activity Bar (the beaker icon).
3.  **Run/Debug:**
    *   **Run All Tests:** Go to the "Testing" view and click the "Run Tests" button.
    *   **Run/Debug Specific Test:** Hover over a test function or class in your test file. A small "Run Test" (play icon) and "Debug Test" (bug icon) will appear. Click the "Debug Test" icon to run with the debugger attached.
    *   **Set Breakpoints:** Click in the gutter next to a line of code to set a breakpoint. When debugging, execution will pause at this point.
