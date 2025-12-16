#!/usr/bin/env python3
"""
n8n Workflow Validator

Validates the structure and integrity of n8n workflow JSON files.
"""

import json
import sys
from pathlib import Path


def validate_workflow(workflow_path: Path) -> bool:
    """Validate an n8n workflow JSON file."""
    print(f"Validating: {workflow_path.name}")
    print("=" * 60)
    
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return False
    
    # Check required top-level fields
    required_fields = ["name", "nodes", "connections"]
    for field in required_fields:
        if field not in workflow:
            print(f"✗ Missing required field: {field}")
            return False
        print(f"✓ Has field: {field}")
    
    # Validate nodes
    nodes = workflow.get("nodes", [])
    if not isinstance(nodes, list):
        print(f"✗ 'nodes' must be a list")
        return False
    
    print(f"✓ Total nodes: {len(nodes)}")
    
    node_names = set()
    node_ids = set()
    
    for i, node in enumerate(nodes):
        # Check required node fields
        required_node_fields = ["id", "name", "type", "parameters"]
        for field in required_node_fields:
            if field not in node:
                print(f"✗ Node {i} missing field: {field}")
                return False
        
        # Check for duplicate IDs/names
        node_id = node["id"]
        node_name = node["name"]
        
        if node_id in node_ids:
            print(f"✗ Duplicate node ID: {node_id}")
            return False
        node_ids.add(node_id)
        
        if node_name in node_names:
            print(f"✗ Duplicate node name: {node_name}")
            return False
        node_names.add(node_name)
    
    print(f"✓ All nodes have unique IDs and names")
    
    # Validate connections
    connections = workflow.get("connections", {})
    if not isinstance(connections, dict):
        print(f"✗ 'connections' must be a dictionary")
        return False
    
    print(f"✓ Total connections: {len(connections)}")
    
    # Verify all connection references exist
    for source_name, targets in connections.items():
        if source_name not in node_names:
            print(f"✗ Connection references non-existent node: {source_name}")
            return False
        
        if "main" in targets:
            for target_group in targets["main"]:
                for target in target_group:
                    target_name = target.get("node")
                    if target_name not in node_names:
                        print(f"✗ Connection from '{source_name}' references non-existent target: {target_name}")
                        return False
    
    print(f"✓ All connections reference existing nodes")
    
    # List all nodes for reference
    print("\nNode List:")
    for node in nodes:
        node_type = node.get("type", "unknown")
        print(f"  - {node['name']} ({node_type})")
    
    # Show connection graph
    print("\nConnection Graph:")
    for source_name, targets in connections.items():
        if "main" in targets:
            for target_group in targets["main"]:
                for target in target_group:
                    print(f"  {source_name} → {target['node']}")
    
    print("\n" + "=" * 60)
    print("✓ Workflow is valid!")
    return True


def main():
    """Main entry point."""
    workflows_dir = Path(__file__).parent
    
    # Find all JSON files
    workflow_files = list(workflows_dir.glob("*.json"))
    
    if not workflow_files:
        print("No workflow JSON files found")
        return 1
    
    all_valid = True
    for workflow_file in sorted(workflow_files):
        if not validate_workflow(workflow_file):
            all_valid = False
        print()
    
    if all_valid:
        print(f"✓ All {len(workflow_files)} workflows are valid!")
        return 0
    else:
        print("✗ Some workflows have errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
