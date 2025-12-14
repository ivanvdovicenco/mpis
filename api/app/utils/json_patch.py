"""
MPIS Genesis API - JSON Patch Utilities

Utilities for applying JSON Patch-like edit operations to persona core.
"""
import re
from typing import Any, List, Optional
from copy import deepcopy

from app.schemas.genesis import EditOperation


class JsonPatchError(Exception):
    """Error during JSON patch operation."""
    pass


def parse_path(path: str) -> list:
    """
    Parse a JSON path string into path components.
    
    Supports dot notation and array indexing.
    
    Examples:
        >>> parse_path("credo.statements[1]")
        ['credo', 'statements', 1]
        >>> parse_path("ethos.virtues")
        ['ethos', 'virtues']
        >>> parse_path("topics.primary[0]")
        ['topics', 'primary', 0]
    """
    if not path:
        return []
    
    components = []
    # Split by dots, but handle array indices
    parts = re.split(r'\.', path)
    
    for part in parts:
        # Check for array index
        match = re.match(r'^(\w+)\[(\d+)\]$', part)
        if match:
            components.append(match.group(1))
            components.append(int(match.group(2)))
        elif re.match(r'^\[\d+\]$', part):
            # Just an index
            components.append(int(part[1:-1]))
        else:
            components.append(part)
    
    return components


def get_at_path(obj: Any, path_components: list) -> Any:
    """
    Get value at the specified path in an object.
    
    Args:
        obj: Object to traverse
        path_components: List of path components
        
    Returns:
        Value at the path
        
    Raises:
        JsonPatchError: If path is invalid
    """
    current = obj
    
    for i, component in enumerate(path_components):
        try:
            if isinstance(component, int):
                if not isinstance(current, list):
                    raise JsonPatchError(
                        f"Expected list at path component {i}, got {type(current).__name__}"
                    )
                current = current[component]
            else:
                if isinstance(current, dict):
                    current = current[component]
                elif hasattr(current, component):
                    current = getattr(current, component)
                else:
                    raise JsonPatchError(
                        f"Cannot access '{component}' on {type(current).__name__}"
                    )
        except (IndexError, KeyError) as e:
            raise JsonPatchError(f"Path not found: {'.'.join(str(c) for c in path_components[:i+1])}")
    
    return current


def set_at_path(obj: dict, path_components: list, value: Any) -> None:
    """
    Set value at the specified path in an object.
    
    Args:
        obj: Object to modify (in place)
        path_components: List of path components
        value: Value to set
        
    Raises:
        JsonPatchError: If path is invalid
    """
    if not path_components:
        raise JsonPatchError("Empty path")
    
    # Navigate to parent
    parent = obj
    for component in path_components[:-1]:
        try:
            if isinstance(component, int):
                parent = parent[component]
            elif isinstance(parent, dict):
                parent = parent[component]
            else:
                raise JsonPatchError(f"Cannot navigate to '{component}'")
        except (IndexError, KeyError):
            raise JsonPatchError(f"Parent path not found")
    
    # Set the value
    last_component = path_components[-1]
    try:
        if isinstance(last_component, int):
            if not isinstance(parent, list):
                raise JsonPatchError(f"Expected list for index {last_component}")
            parent[last_component] = value
        elif isinstance(parent, dict):
            parent[last_component] = value
        else:
            raise JsonPatchError(f"Cannot set '{last_component}' on {type(parent).__name__}")
    except IndexError:
        raise JsonPatchError(f"Index {last_component} out of range")


def add_at_path(obj: dict, path_components: list, value: Any) -> None:
    """
    Add value at the specified path in an object.
    
    For arrays, appends to the array at the parent path.
    For dicts, sets the key.
    
    Args:
        obj: Object to modify (in place)
        path_components: List of path components
        value: Value to add
    """
    if not path_components:
        raise JsonPatchError("Empty path")
    
    # Navigate to parent
    parent = obj
    for component in path_components[:-1]:
        try:
            if isinstance(component, int):
                parent = parent[component]
            elif isinstance(parent, dict):
                parent = parent[component]
            else:
                raise JsonPatchError(f"Cannot navigate to '{component}'")
        except (IndexError, KeyError):
            raise JsonPatchError(f"Parent path not found")
    
    last_component = path_components[-1]
    
    # If the target is a list, append
    if isinstance(last_component, str) and isinstance(parent, dict):
        target = parent.get(last_component)
        if isinstance(target, list):
            target.append(value)
            return
    
    # Otherwise, set the value (create or overwrite)
    if isinstance(parent, dict):
        parent[last_component] = value
    elif isinstance(parent, list) and isinstance(last_component, int):
        if last_component >= len(parent):
            parent.append(value)
        else:
            parent.insert(last_component, value)
    else:
        raise JsonPatchError(f"Cannot add at path")


def remove_at_path(obj: dict, path_components: list) -> None:
    """
    Remove value at the specified path in an object.
    
    Args:
        obj: Object to modify (in place)
        path_components: List of path components
    """
    if not path_components:
        raise JsonPatchError("Empty path")
    
    # Navigate to parent
    parent = obj
    for component in path_components[:-1]:
        try:
            if isinstance(component, int):
                parent = parent[component]
            elif isinstance(parent, dict):
                parent = parent[component]
            else:
                raise JsonPatchError(f"Cannot navigate to '{component}'")
        except (IndexError, KeyError):
            raise JsonPatchError(f"Parent path not found")
    
    last_component = path_components[-1]
    
    try:
        if isinstance(last_component, int):
            if isinstance(parent, list):
                del parent[last_component]
            else:
                raise JsonPatchError(f"Expected list for index {last_component}")
        elif isinstance(parent, dict):
            del parent[last_component]
        else:
            raise JsonPatchError(f"Cannot remove '{last_component}'")
    except (IndexError, KeyError):
        raise JsonPatchError(f"Path not found for removal")


def apply_json_patch(obj: dict, edits: List[EditOperation]) -> dict:
    """
    Apply a list of JSON Patch-like edit operations to an object.
    
    Supports operations: add, replace, remove
    
    Args:
        obj: Object to modify
        edits: List of edit operations
        
    Returns:
        Modified copy of the object
        
    Raises:
        JsonPatchError: If any operation fails
        
    Examples:
        >>> obj = {"credo": {"statements": ["a", "b"]}}
        >>> edits = [EditOperation(path="credo.statements[1]", op="replace", value="c")]
        >>> result = apply_json_patch(obj, edits)
        >>> result["credo"]["statements"]
        ['a', 'c']
    """
    # Work on a deep copy
    result = deepcopy(obj)
    
    for edit in edits:
        path_components = parse_path(edit.path)
        
        if edit.op == "replace":
            if edit.value is None:
                raise JsonPatchError(f"Replace operation requires a value")
            set_at_path(result, path_components, edit.value)
        
        elif edit.op == "add":
            if edit.value is None:
                raise JsonPatchError(f"Add operation requires a value")
            add_at_path(result, path_components, edit.value)
        
        elif edit.op == "remove":
            remove_at_path(result, path_components)
        
        else:
            raise JsonPatchError(f"Unknown operation: {edit.op}")
    
    return result
