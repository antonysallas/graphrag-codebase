"""Main Ansible codebase extractor."""

import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Generator, Optional

from loguru import logger

from ...graph import Node, NodeType, Relationship, RelationshipType
from ...parsers import JinjaParser, PythonParser, RubyParser, YAMLParser
from ..base_extractor import BaseExtractor
from ..collector import NodeCollector
from ..registry import ExtractorRegistry
from .playbook_extractor import PlaybookExtractor
from .role_extractor import RoleExtractor
from .variable_extractor import VariableExtractor


@ExtractorRegistry.register("ansible")
class AnsibleExtractor(BaseExtractor):
    """Main extractor for Ansible codebase."""

    schema_profile = "ansible"

    def __init__(self, graph_builder: Any = None, max_workers: int = 4):
        """Initialize Ansible extractor.

        Args:
            graph_builder: Deprecated. Ignored.
            max_workers: Maximum parallel workers for file processing
        """
        self.max_workers = max_workers

        # Initialize parsers
        self.yaml_parser = YAMLParser()
        self.python_parser = PythonParser()
        self.jinja_parser = JinjaParser()
        self.ruby_parser = RubyParser()

        # Track processed files
        self.processed_files: set[str] = set()
        self._repository_id: Optional[str] = None

    def extract(
        self, codebase_path: Path, repository_id: Optional[str] = None
    ) -> Generator[dict[str, Any], None, None]:
        """Extract entities from codebase (Nodes)."""
        logger.info(f"Starting codebase extraction (nodes) from: {codebase_path}")
        self._repository_id = repository_id
        yield from self._run_extraction(codebase_path, yield_nodes=True)

    def extract_relationships(
        self, codebase_path: Path, repository_id: Optional[str] = None
    ) -> Generator[dict[str, Any], None, None]:
        """Extract relationships from codebase."""
        logger.info(f"Starting codebase extraction (relationships) from: {codebase_path}")
        self._repository_id = repository_id
        yield from self._run_extraction(codebase_path, yield_nodes=False)

    def _run_extraction(
        self, codebase_path: Path, yield_nodes: bool
    ) -> Generator[dict[str, Any], None, None]:
        """Run extraction and yield either nodes or relationships."""
        codebase_path = Path(codebase_path)
        files_to_process = self._collect_files(codebase_path)

        # Reset processed files for this run
        self.processed_files.clear()

        # Process files in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._process_file, file_path, codebase_path): file_path
                for file_path in files_to_process
            }

            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    nodes, rels = future.result()
                    if yield_nodes:
                        for node in nodes:
                            yield {"type": node.node_type.value, "properties": node.properties}
                    else:
                        for rel in rels:
                            yield {
                                "type": rel.rel_type.value,
                                "source": {
                                    "type": rel.from_node.node_type.value,
                                    "properties": rel.from_node.properties,
                                },
                                "target": {
                                    "type": rel.to_node.node_type.value,
                                    "properties": rel.to_node.properties,
                                },
                                "properties": rel.properties,
                            }
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")

    def _collect_files(self, codebase_path: Path) -> list[Path]:
        """Collect all relevant files from codebase.

        Args:
            codebase_path: Root path

        Returns:
            List of file paths to process
        """
        files = []

        # YAML files (playbooks, vars, etc.)
        files.extend(codebase_path.rglob("*.yml"))
        files.extend(codebase_path.rglob("*.yaml"))

        # Python files (inventory scripts)
        files.extend(codebase_path.rglob("*.py"))

        # Jinja2 templates
        files.extend(codebase_path.rglob("*.j2"))

        # Vagrantfiles
        files.extend(codebase_path.rglob("Vagrantfile"))

        # Filter out hidden directories and common exclusions
        files = [
            f
            for f in files
            if not any(part.startswith(".") for part in f.parts)
            and "node_modules" not in f.parts
            and "__pycache__" not in f.parts
        ]

        return files

    def _process_file(
        self, file_path: Path, codebase_root: Path
    ) -> tuple[list[Node], list[Relationship]]:
        """Process a single file.

        Returns:
            Tuple of (nodes, relationships)
        """
        collector = NodeCollector(repository_id=self._repository_id)

        # Initialize sub-extractors with this collector
        playbook_extractor = PlaybookExtractor(collector)
        role_extractor = RoleExtractor(collector)
        variable_extractor = VariableExtractor(collector)

        logger.debug(f"Processing file: {file_path}")

        # Get relative path
        rel_path = str(file_path.relative_to(codebase_root))

        # Create File node
        file_node = self._create_file_node(file_path, rel_path)
        collector.add_node(file_node)

        # Determine file type and parse accordingly
        if file_path.suffix in [".yml", ".yaml"]:
            self._process_yaml_file(
                file_path,
                rel_path,
                file_node,
                collector,
                playbook_extractor,
                role_extractor,
                variable_extractor,
            )
        elif file_path.suffix == ".py":
            self._process_python_file(file_path, rel_path, file_node, collector)
        elif file_path.suffix == ".j2":
            self._process_jinja_file(file_path, rel_path, file_node, collector)
        elif file_path.name == "Vagrantfile":
            self._process_ruby_file(file_path, rel_path, file_node, collector)

        return collector.nodes, collector.rels

    def _create_file_node(self, file_path: Path, rel_path: str) -> Node:
        """Create File node for a file."""
        # Calculate content hash
        with open(file_path, "rb") as f:
            content_hash = hashlib.sha256(f.read()).hexdigest()

        # Get file stats
        stat = file_path.stat()

        return Node(
            node_type=NodeType.FILE,
            properties={
                "path": rel_path,
                "absolute_path": str(file_path.absolute()),
                "file_type": file_path.suffix[1:] if file_path.suffix else "none",
                "content_hash": content_hash,
                "size": stat.st_size,
                "last_modified": int(stat.st_mtime),
            },
        )

    def _process_yaml_file(
        self,
        file_path: Path,
        rel_path: str,
        file_node: Node,
        collector: NodeCollector,
        playbook_extractor: PlaybookExtractor,
        role_extractor: RoleExtractor,
        variable_extractor: VariableExtractor,
    ) -> None:
        """Process YAML file."""
        parse_result = self.yaml_parser.parse_file(file_path)

        if not parse_result.is_success:
            logger.warning(f"Failed to parse YAML file {rel_path}: {parse_result.errors}")
            return

        metadata = parse_result.metadata

        # Determine file type and extract accordingly
        if metadata.get("is_playbook"):
            playbook_extractor.extract(parse_result, file_node)
        elif metadata.get("is_requirements"):
            role_extractor.extract_requirements(parse_result, file_node)
        elif metadata.get("is_vars_file"):
            variable_extractor.extract_vars_file(parse_result, file_node)

    def _process_python_file(
        self, file_path: Path, rel_path: str, file_node: Node, collector: NodeCollector
    ) -> None:
        """Process Python file."""
        parse_result = self.python_parser.parse_file(file_path)

        if not parse_result.is_success:
            logger.warning(f"Failed to parse Python file {rel_path}: {parse_result.errors}")
            return

        metadata = parse_result.metadata

        # If it's a dynamic inventory script, create Inventory node
        if metadata.get("is_inventory_script"):
            inventory_node = Node(
                node_type=NodeType.INVENTORY,
                properties={
                    "path": rel_path,
                    "type": "dynamic",
                },
            )
            collector.add_node(inventory_node)

            # Link to file
            rel = Relationship(
                rel_type=RelationshipType.IN_FILE,
                from_node=inventory_node,
                to_node=file_node,
            )
            collector.add_relationship(rel)

    def _process_jinja_file(
        self, file_path: Path, rel_path: str, file_node: Node, collector: NodeCollector
    ) -> None:
        """Process Jinja2 template file."""
        parse_result = self.jinja_parser.parse_file(file_path)

        if not parse_result.is_success:
            logger.warning(f"Failed to parse Jinja2 file {rel_path}: {parse_result.errors}")
            return

        metadata = parse_result.metadata

        # Create Template node
        template_node = Node(
            node_type=NodeType.TEMPLATE,
            properties={
                "path": rel_path,
                "variables_used": metadata.get("variables_used", []),
            },
        )
        collector.add_node(template_node)

        # Link to file
        rel = Relationship(
            rel_type=RelationshipType.IN_FILE,
            from_node=template_node,
            to_node=file_node,
        )
        collector.add_relationship(rel)

        # Create variable usage relationships
        for var_name in metadata.get("variables_used", []):
            var_node = Node(
                node_type=NodeType.VARIABLE,
                properties={
                    "name": var_name,
                    "scope": "template",
                    "file_path": rel_path,
                },
            )
            collector.add_node(var_node)

            var_rel = Relationship(
                rel_type=RelationshipType.USES_VAR,
                from_node=template_node,
                to_node=var_node,
            )
            collector.add_relationship(var_rel)

    def _process_ruby_file(
        self, file_path: Path, rel_path: str, file_node: Node, collector: NodeCollector
    ) -> None:
        """Process Ruby file (Vagrantfile)."""
        parse_result = self.ruby_parser.parse_file(file_path)

        if not parse_result.is_success:
            logger.warning(f"Failed to parse Ruby file {rel_path}: {parse_result.errors}")
            return
