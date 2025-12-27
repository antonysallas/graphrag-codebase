"""Playbook extractor for detailed playbook structure extraction."""

import json
from typing import Any

from loguru import logger

from ...graph import Node, NodeType, Relationship, RelationshipType
from ...parsers import ParseResult, YAMLParser


class PlaybookExtractor:
    """Extractor for Ansible playbooks."""

    def __init__(self, graph_builder: Any):
        """Initialize playbook extractor.

        Args:
            graph_builder: GraphBuilder or NodeCollector instance
        """
        self.graph_builder = graph_builder
        self.yaml_parser = YAMLParser()

    def extract(self, parse_result: ParseResult, file_node: Node) -> None:
        """Extract playbook structure into graph.

        Args:
            parse_result: Parsed YAML result
            file_node: File node for the playbook
        """
        logger.debug(f"Extracting playbook: {parse_result.file_path}")

        # Extract playbook structure
        plays = self.yaml_parser.extract_playbook_structure(parse_result)

        if not plays:
            return

        # Create Playbook node
        playbook_node = Node(
            node_type=NodeType.PLAYBOOK,
            properties={
                "name": parse_result.file_path,
                "path": parse_result.file_path,
                "description": plays[0].get("name", "") if plays else "",
            },
        )
        self.graph_builder.add_node(playbook_node)

        # Link playbook to file
        file_rel = Relationship(
            rel_type=RelationshipType.IN_FILE,
            from_node=playbook_node,
            to_node=file_node,
        )
        self.graph_builder.add_relationship(file_rel)

        # Extract each play
        for play_index, play_data in enumerate(plays):
            self._extract_play(play_data, play_index, playbook_node, file_node)

    def _extract_play(
        self, play_data: dict[str, Any], play_index: int, playbook_node: Node, file_node: Node
    ) -> None:
        """Extract a single play.

        Args:
            play_data: Play data dictionary
            play_index: Index of play in playbook
            playbook_node: Playbook node
            file_node: File node
        """
        # Create Play node
        play_node = Node(
            node_type=NodeType.PLAY,
            properties={
                "name": play_data.get("name", f"<unnamed play {play_index}>"),
                "playbook_path": playbook_node.properties["path"],
                "hosts": play_data.get("hosts", "all"),
                "become": play_data.get("become", False),
                "gather_facts": play_data.get("gather_facts", True),
                "order": play_index,
            },
        )
        self.graph_builder.add_node(play_node)

        # Link play to playbook
        play_rel = Relationship(
            rel_type=RelationshipType.HAS_PLAY,
            from_node=playbook_node,
            to_node=play_node,
            properties={"play_index": play_index},
        )
        self.graph_builder.add_relationship(play_rel)

        # Link play to file
        file_rel = Relationship(
            rel_type=RelationshipType.IN_FILE,
            from_node=play_node,
            to_node=file_node,
        )
        self.graph_builder.add_relationship(file_rel)

        # Extract tasks
        for task_type in ["tasks", "pre_tasks", "post_tasks"]:
            if task_type in play_data:
                tasks = play_data[task_type]
                for task_index, task_data in enumerate(tasks):
                    self._extract_task(task_data, task_index, play_node, file_node)

        # Extract handlers
        if "handlers" in play_data:
            for handler_index, handler_data in enumerate(play_data["handlers"]):
                self._extract_handler(handler_data, handler_index, playbook_node, file_node)

        # Extract roles
        if "roles" in play_data:
            for role_data in play_data["roles"]:
                self._link_role(role_data, play_node)

        # Extract vars_files
        if "vars_files" in play_data:
            for vars_file in play_data["vars_files"]:
                self._link_vars_file(vars_file, play_node, file_node)

    def _extract_task(
        self, task_data: dict[str, Any], task_index: int, play_node: Node, file_node: Node
    ) -> None:
        """Extract a task.

        Args:
            task_data: Task data dictionary
            task_index: Index of task
            play_node: Play node
            file_node: File node
        """
        # Create Task node
        # Serialize complex fields to JSON
        when_value = task_data.get("when")
        when_str = json.dumps(when_value) if when_value is not None else None

        loop_value = task_data.get("loop")
        loop_str = json.dumps(loop_value) if loop_value is not None else None

        task_node = Node(
            node_type=NodeType.TASK,
            properties={
                "name": task_data.get("name", f"<unnamed task {task_index}>"),
                "file_path": file_node.properties["path"],
                "module": task_data.get("module", "unknown"),
                "args": json.dumps(task_data.get("args", {})),
                "when": when_str,
                "loop": loop_str,
                "register": task_data.get("register"),
                "become": task_data.get("become"),
                "order": task_index,
                "line_number": task_index,  # Approximate
            },
        )
        self.graph_builder.add_node(task_node)

        # Link task to play
        task_rel = Relationship(
            rel_type=RelationshipType.HAS_TASK,
            from_node=play_node,
            to_node=task_node,
            properties={"task_index": task_index},
        )
        self.graph_builder.add_relationship(task_rel)

        # Link task to file
        file_rel = Relationship(
            rel_type=RelationshipType.IN_FILE,
            from_node=task_node,
            to_node=file_node,
        )
        self.graph_builder.add_relationship(file_rel)

        # Handle notify (task -> handler relationship)
        if task_data.get("notify"):
            notify = task_data["notify"]
            if isinstance(notify, str):
                notify = [notify]

            for handler_name in notify:
                handler_node = Node(
                    node_type=NodeType.HANDLER,
                    properties={
                        "name": handler_name,
                        "file_path": file_node.properties["path"],
                        "module": "unknown",
                        "line_number": 0,
                    },
                )
                # We create a placeholder handler node; it will be merged with actual handler later
                self.graph_builder.add_node(handler_node)

                notify_rel = Relationship(
                    rel_type=RelationshipType.NOTIFIES,
                    from_node=task_node,
                    to_node=handler_node,
                    properties={"notification_name": handler_name},
                )
                self.graph_builder.add_relationship(notify_rel)

        # Handle variable registration
        if task_data.get("register"):
            var_name = task_data["register"]
            var_node = Node(
                node_type=NodeType.VARIABLE,
                properties={
                    "name": var_name,
                    "scope": "play",
                    "file_path": file_node.properties["path"],
                },
            )
            self.graph_builder.add_node(var_node)

            var_rel = Relationship(
                rel_type=RelationshipType.DEFINES_VAR,
                from_node=task_node,
                to_node=var_node,
            )
            self.graph_builder.add_relationship(var_rel)

        # Handle template usage
        if task_data.get("module") in ["template", "copy"]:
            args = task_data.get("args", {})
            if isinstance(args, dict):
                template_path = args.get("src") or args.get("template")
                if template_path and template_path.endswith(".j2"):
                    template_node = Node(
                        node_type=NodeType.TEMPLATE,
                        properties={"path": template_path, "variables_used": []},
                    )
                    self.graph_builder.add_node(template_node)

                    template_rel = Relationship(
                        rel_type=RelationshipType.USES_TEMPLATE,
                        from_node=task_node,
                        to_node=template_node,
                        properties={"parameter_name": "src"},
                    )
                    self.graph_builder.add_relationship(template_rel)

    def _extract_handler(
        self, handler_data: dict[str, Any], handler_index: int, playbook_node: Node, file_node: Node
    ) -> None:
        """Extract a handler.

        Args:
            handler_data: Handler data dictionary
            handler_index: Index of handler
            playbook_node: Playbook node
            file_node: File node
        """
        # Create Handler node
        handler_node = Node(
            node_type=NodeType.HANDLER,
            properties={
                "name": handler_data.get("name", f"<unnamed handler {handler_index}>"),
                "file_path": file_node.properties["path"],
                "module": handler_data.get("module", "unknown"),
                "args": json.dumps(handler_data.get("args", {})),
                "line_number": handler_index,
            },
        )
        self.graph_builder.add_node(handler_node)

        # Link handler to playbook
        handler_rel = Relationship(
            rel_type=RelationshipType.HAS_HANDLER,
            from_node=playbook_node,
            to_node=handler_node,
        )
        self.graph_builder.add_relationship(handler_rel)

        # Link handler to file
        file_rel = Relationship(
            rel_type=RelationshipType.IN_FILE,
            from_node=handler_node,
            to_node=file_node,
        )
        self.graph_builder.add_relationship(file_rel)

    def _link_role(self, role_data: dict[str, Any], play_node: Node) -> None:
        """Link a role to a play.

        Args:
            role_data: Role data dictionary
            play_node: Play node
        """
        role_name = role_data.get("name")
        if not role_name:
            return

        # Create or reference Role node
        role_node = Node(
            node_type=NodeType.ROLE,
            properties={"name": role_name, "source": "playbook"},
        )
        self.graph_builder.add_node(role_node)

        # Link play to role
        role_rel = Relationship(
            rel_type=RelationshipType.USES_ROLE,
            from_node=play_node,
            to_node=role_node,
            properties={"role_params": str(role_data.get("params", {}))},
        )
        self.graph_builder.add_relationship(role_rel)

    def _link_vars_file(self, vars_file: str, play_node: Node, file_node: Node) -> None:
        """Link a vars file to a play.

        Args:
            vars_file: Path to vars file
            play_node: Play node
            file_node: Source file node
        """
        # Create VarsFile node
        vars_node = Node(
            node_type=NodeType.VARS_FILE,
            properties={"path": vars_file, "scope": "play"},
        )
        self.graph_builder.add_node(vars_node)

        # Link play to vars file
        vars_rel = Relationship(
            rel_type=RelationshipType.LOADS_VARS,
            from_node=play_node,
            to_node=vars_node,
        )
        self.graph_builder.add_relationship(vars_rel)
