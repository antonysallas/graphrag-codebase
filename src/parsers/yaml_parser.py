"""YAML parser with Ansible-specific extensions."""

from typing import Any

import yaml

from .base_parser import BaseParser, ParseResult


class YAMLParser(BaseParser):
    """Parser for YAML files, with special handling for Ansible structures."""

    def __init__(self):
        """Initialize YAML parser."""
        super().__init__("yaml")

    def extract_metadata(self, parse_result: ParseResult) -> dict[str, Any]:
        """Extract metadata from YAML file.

        Args:
            parse_result: Parse result

        Returns:
            Dictionary with metadata including Ansible-specific info
        """
        metadata = {
            "is_playbook": False,
            "is_vars_file": False,
            "is_requirements": False,
            "is_inventory": False,
            "has_tasks": False,
            "has_handlers": False,
            "has_roles": False,
        }

        if not parse_result.root_node:
            return metadata

        # Also parse with PyYAML to get structured data
        try:
            yaml_data = yaml.safe_load(parse_result.content)
            metadata.update(self._analyze_yaml_structure(yaml_data))
        except Exception:
            pass  # Tree-sitter parsing already succeeded, YAML errors are non-critical

        return metadata

    def _analyze_yaml_structure(self, data: Any) -> dict[str, Any]:
        """Analyze YAML structure to determine file type and contents.

        Args:
            data: Parsed YAML data

        Returns:
            Dictionary with structure metadata
        """
        metadata = {}

        if not data:
            return metadata

        # Check if it's a playbook (list of plays)
        if isinstance(data, list):
            # Check first item
            if len(data) > 0 and isinstance(data[0], dict):
                first_item = data[0]

                # Playbook indicators
                if any(key in first_item for key in ["hosts", "tasks", "roles", "plays"]):
                    metadata["is_playbook"] = True
                    metadata["play_count"] = len(data)

                    # Count tasks and roles across all plays
                    total_tasks = 0
                    total_handlers = 0
                    roles = []

                    for play in data:
                        if not isinstance(play, dict):
                            continue

                        if "tasks" in play and isinstance(play["tasks"], list):
                            total_tasks += len(play["tasks"])
                            metadata["has_tasks"] = True

                        if "handlers" in play and isinstance(play["handlers"], list):
                            total_handlers += len(play["handlers"])
                            metadata["has_handlers"] = True

                        if "roles" in play:
                            metadata["has_roles"] = True
                            roles.extend(self._extract_role_names(play["roles"]))

                    metadata["task_count"] = total_tasks
                    metadata["handler_count"] = total_handlers
                    metadata["role_names"] = list(set(roles))

        # Check if it's a vars file, requirements file, or other structure
        elif isinstance(data, dict):
            # requirements.yml (Galaxy roles)
            if "roles" in data or (isinstance(data, dict) and "name" in data and "src" in data):
                metadata["is_requirements"] = True

            # vars file
            else:
                metadata["is_vars_file"] = True
                metadata["var_count"] = len(data.keys())
                metadata["var_names"] = list(data.keys())

        return metadata

    def _extract_role_names(self, roles: Any) -> list[str]:
        """Extract role names from roles section.

        Args:
            roles: Roles data (can be list of strings or dicts)

        Returns:
            List of role names
        """
        role_names = []

        if not isinstance(roles, list):
            return role_names

        for role in roles:
            if isinstance(role, str):
                role_names.append(role)
            elif isinstance(role, dict):
                if "role" in role:
                    role_names.append(role["role"])
                elif "name" in role:
                    role_names.append(role["name"])

        return role_names

    def extract_playbook_structure(self, parse_result: ParseResult) -> list[dict[str, Any]]:
        """Extract detailed playbook structure.

        Args:
            parse_result: Parsed YAML result

        Returns:
            List of plays with their structure
        """
        try:
            yaml_data = yaml.safe_load(parse_result.content)

            if not isinstance(yaml_data, list):
                return []

            plays = []
            for play_data in yaml_data:
                if not isinstance(play_data, dict):
                    continue

                play = {
                    "name": play_data.get("name", "<unnamed>"),
                    "hosts": play_data.get("hosts", "all"),
                    "become": play_data.get("become", False),
                    "gather_facts": play_data.get("gather_facts", True),
                    "vars": play_data.get("vars", {}),
                    "vars_files": play_data.get("vars_files", []),
                    "tasks": [],
                    "handlers": [],
                    "roles": [],
                }

                # Extract tasks
                if "tasks" in play_data and isinstance(play_data["tasks"], list):
                    play["tasks"] = self._extract_tasks(play_data["tasks"])

                # Extract pre_tasks
                if "pre_tasks" in play_data and isinstance(play_data["pre_tasks"], list):
                    play["pre_tasks"] = self._extract_tasks(play_data["pre_tasks"])

                # Extract post_tasks
                if "post_tasks" in play_data and isinstance(play_data["post_tasks"], list):
                    play["post_tasks"] = self._extract_tasks(play_data["post_tasks"])

                # Extract handlers
                if "handlers" in play_data and isinstance(play_data["handlers"], list):
                    play["handlers"] = self._extract_tasks(play_data["handlers"])

                # Extract roles
                if "roles" in play_data:
                    play["roles"] = self._extract_roles(play_data["roles"])

                plays.append(play)

            return plays

        except Exception:
            return []

    def _extract_tasks(self, tasks_data: list) -> list[dict[str, Any]]:
        """Extract task information from tasks list.

        Args:
            tasks_data: List of task dictionaries

        Returns:
            List of extracted task information
        """
        tasks = []

        for task_data in tasks_data:
            if not isinstance(task_data, dict):
                continue

            # Find the module name (the key that's not a standard Ansible keyword)
            module_name = None
            module_args = None

            ansible_keywords = {
                "name",
                "when",
                "with_items",
                "loop",
                "register",
                "notify",
                "tags",
                "become",
                "become_user",
                "changed_when",
                "failed_when",
                "ignore_errors",
                "delegate_to",
                "vars",
            }

            for key, value in task_data.items():
                if key not in ansible_keywords:
                    module_name = key
                    module_args = value
                    break

            task = {
                "name": task_data.get("name", f"<unnamed {module_name}>"),
                "module": module_name,
                "args": module_args,
                "when": task_data.get("when"),
                "loop": task_data.get("loop")
                or task_data.get("with_items")
                or task_data.get("with_dict"),
                "register": task_data.get("register"),
                "notify": task_data.get("notify"),
                "tags": task_data.get("tags"),
                "become": task_data.get("become"),
            }

            tasks.append(task)

        return tasks

    def _extract_roles(self, roles_data: Any) -> list[dict[str, Any]]:
        """Extract role information.

        Args:
            roles_data: Roles data from playbook

        Returns:
            List of role information
        """
        roles = []

        if not isinstance(roles_data, list):
            return roles

        for role_data in roles_data:
            if isinstance(role_data, str):
                roles.append({"name": role_data, "params": {}})
            elif isinstance(role_data, dict):
                role_name = role_data.get("role") or role_data.get("name")
                if role_name:
                    roles.append({"name": role_name, "params": role_data})

        return roles

    def extract_variables(self, parse_result: ParseResult) -> dict[str, Any]:
        """Extract variable definitions from YAML file.

        Args:
            parse_result: Parsed YAML result

        Returns:
            Dictionary of variables
        """
        try:
            yaml_data = yaml.safe_load(parse_result.content)

            if isinstance(yaml_data, dict):
                return yaml_data
            else:
                return {}

        except Exception:
            return {}

    def extract_requirements(self, parse_result: ParseResult) -> list[dict[str, Any]]:
        """Extract Galaxy role requirements.

        Args:
            parse_result: Parsed YAML result

        Returns:
            List of role requirements
        """
        try:
            yaml_data = yaml.safe_load(parse_result.content)

            if not isinstance(yaml_data, dict):
                return []

            roles = yaml_data.get("roles", [])

            requirements = []
            for role in roles:
                if isinstance(role, dict):
                    requirements.append(
                        {
                            "name": role.get("name"),
                            "src": role.get("src"),
                            "version": role.get("version"),
                            "scm": role.get("scm"),
                        }
                    )

            return requirements

        except Exception:
            return []
