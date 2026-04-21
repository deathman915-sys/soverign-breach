import ast
import os
import re
import pytest

def get_exposed_python_functions(file_path):
    """Extracts all function names decorated with @eel.expose in a Python file."""
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    
    exposed = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                # Check for @eel.expose or @eel.expose()
                if (isinstance(decorator, ast.Attribute) and 
                    decorator.attr == "expose" and 
                    isinstance(decorator.value, ast.Name) and 
                    decorator.value.id == "eel"):
                    exposed.add(node.name)
                elif (isinstance(decorator, ast.Call) and 
                      isinstance(decorator.func, ast.Attribute) and 
                      decorator.func.attr == "expose"):
                    exposed.add(node.name)
    return exposed

def get_called_js_functions(directory):
    """Extracts all eel.func_name calls from JS files in a directory."""
    called = set()
    # Pattern for eel.function_name(...)
    # Excludes eel.expose and eel.init/start
    pattern = re.compile(r"eel\.([a-zA-Z0-9_]+)\(")
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".js"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    matches = pattern.findall(content)
                    for m in matches:
                        if m not in ("expose", "init", "start"):
                            called.add(m)
    return called

def test_eel_bridge_parity():
    """Verify that all Eel functions called by the frontend are exposed by the backend."""
    python_file = "web_main.py"
    js_dir = "web/js"
    
    assert os.path.exists(python_file), f"{python_file} not found"
    assert os.path.exists(js_dir), f"{js_dir} directory not found"
    
    exposed_in_python = get_exposed_python_functions(python_file)
    called_in_js = get_called_js_functions(js_dir)
    
    # We also allow functions exposed via call_app_func pattern if they are handled dynamically
    # But for now, we want explicit exposure for core functions
    
    missing_in_python = called_in_js - exposed_in_python
    
    # Optional: Some functions might be exposed in JS but called from Python
    # These are handled via eel.func_name in Python.
    
    assert not missing_in_python, f"Frontend calls Eel functions that are NOT exposed in web_main.py: {missing_in_python}"

def test_essential_bridges_exist():
    """Ensure core high-fidelity bridges are present."""
    python_file = "web_main.py"
    exposed = get_exposed_python_functions(python_file)
    
    essential = {
        "get_game_state", "get_remote_state", "execute_hack", 
        "attempt_connect", "disconnect", "get_hardware_status",
        "get_messages", "get_news", "get_missions"
    }
    
    missing = essential - exposed
    assert not missing, f"Essential Eel bridges missing from web_main.py: {missing}"

def test_event_connections():
    """Verify that web_main.py connects core events to Eel pushes."""
    with open("web_main.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for event connections
    assert "engine.events.connect(\"tick_completed\", on_tick)" in content
    assert "engine.events.connect(\"game_over\", on_game_over)" in content
    assert "engine.events.connect(\"task_progress\", on_tasks_changed)" in content
    assert "engine.events.connect(\"task_completed\", on_tasks_changed)" in content
    
    # Check for eel.update_hud call
    assert "eel.update_hud(data)()" in content
    # Check for eel.update_tasks call
    assert "eel.update_tasks(data)()" in content
