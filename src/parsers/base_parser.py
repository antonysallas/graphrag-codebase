"""Base parser class for tree-sitter parsers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from tree_sitter import Language, Parser
from tree_sitter import Node as TSNode

# Import individual language grammars
try:
    import tree_sitter_python
except ImportError:
    tree_sitter_python = None

try:
    import tree_sitter_yaml
except ImportError:
    tree_sitter_yaml = None

try:
    import tree_sitter_ruby
except ImportError:
    tree_sitter_ruby = None

try:
    import tree_sitter_jinja
except ImportError:
    tree_sitter_jinja = None


@dataclass
class ParseResult:
    """Result of parsing a file."""

    file_path: str
    language: str
    tree: Optional[Any] = None  # Tree-sitter tree
    root_node: Optional[TSNode] = None
    content: str = ""
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if parsing was successful.

        Returns:
            True if parsing succeeded
        """
        return len(self.errors) == 0 and self.tree is not None


class BaseParser(ABC):
    """Base class for all language parsers."""

    def __init__(self, language: str):
        """Initialize parser with specific language.

        Args:
            language: Language name (e.g., 'python', 'yaml', 'ruby')
        """
        self.language = language
        self.parser = Parser()

        # Map language names to their grammar modules
        language_map = {
            "python": tree_sitter_python,
            "yaml": tree_sitter_yaml,
            "ruby": tree_sitter_ruby,
            "jinja2": tree_sitter_jinja,
        }

        try:
            # Get the language module
            lang_module = language_map.get(language)
            if lang_module is None:
                raise ValueError(f"No grammar available for language: {language}")

            # Get the language from the module
            # Each module has a language() function that returns the Language
            lang = Language(lang_module.language())
            self.parser.language = lang

        except Exception as e:
            raise ValueError(f"Failed to load tree-sitter grammar for {language}: {e}")

    def parse_file(self, file_path: Path) -> ParseResult:
        """Parse a file and return the AST.

        Args:
            file_path: Path to file to parse

        Returns:
            ParseResult containing the AST and metadata
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return self.parse_string(content, str(file_path))

        except Exception as e:
            return ParseResult(
                file_path=str(file_path),
                language=self.language,
                errors=[f"Failed to read file: {e}"],
            )

    def parse_string(self, content: str, file_path: str = "<string>") -> ParseResult:
        """Parse a string and return the AST.

        Args:
            content: Content to parse
            file_path: Optional file path for error reporting

        Returns:
            ParseResult containing the AST and metadata
        """
        try:
            # Parse with tree-sitter
            tree = self.parser.parse(bytes(content, "utf8"))
            root_node = tree.root_node

            # Check for syntax errors
            errors = self._find_syntax_errors(root_node)

            result = ParseResult(
                file_path=file_path,
                language=self.language,
                tree=tree,
                root_node=root_node,
                content=content,
                errors=errors,
            )

            # Extract language-specific metadata
            result.metadata = self.extract_metadata(result)

            return result

        except Exception as e:
            return ParseResult(
                file_path=file_path,
                language=self.language,
                content=content,
                errors=[f"Parsing failed: {e}"],
            )

    def _find_syntax_errors(self, node: TSNode) -> list[str]:
        """Recursively find syntax errors in the parse tree.

        Args:
            node: Tree-sitter node to check

        Returns:
            List of error messages
        """
        errors = []

        if node.type == "ERROR" or node.is_missing:
            errors.append(
                f"Syntax error at line {node.start_point[0] + 1}, column {node.start_point[1] + 1}"
            )

        for child in node.children:
            errors.extend(self._find_syntax_errors(child))

        return errors

    @abstractmethod
    def extract_metadata(self, parse_result: ParseResult) -> dict[str, Any]:
        """Extract language-specific metadata from parse result.

        Args:
            parse_result: Parse result to extract metadata from

        Returns:
            Dictionary of metadata
        """
        pass

    def get_node_text(self, node: TSNode, content: str) -> str:
        """Get text content of a node.

        Args:
            node: Tree-sitter node
            content: Source code content

        Returns:
            Text content of the node
        """
        return content[node.start_byte : node.end_byte]

    def traverse_tree(self, node: TSNode, callback: callable, depth: int = 0) -> None:
        """Traverse the AST and call callback on each node.

        Args:
            node: Current node
            callback: Function to call on each node (receives node and depth)
            depth: Current traversal depth
        """
        callback(node, depth)

        for child in node.children:
            self.traverse_tree(child, callback, depth + 1)

    def find_nodes_by_type(self, root: TSNode, node_type: str) -> list[TSNode]:
        """Find all nodes of a specific type in the tree.

        Args:
            root: Root node to start search
            node_type: Node type to find

        Returns:
            List of matching nodes
        """
        results = []

        def collect_nodes(node: TSNode, depth: int) -> None:
            if node.type == node_type:
                results.append(node)

        self.traverse_tree(root, collect_nodes)
        return results

    def get_node_position(self, node: TSNode) -> dict[str, int]:
        """Get position information for a node.

        Args:
            node: Tree-sitter node

        Returns:
            Dictionary with line and column information
        """
        return {
            "start_line": node.start_point[0] + 1,
            "start_column": node.start_point[1] + 1,
            "end_line": node.end_point[0] + 1,
            "end_column": node.end_point[1] + 1,
            "start_byte": node.start_byte,
            "end_byte": node.end_byte,
        }
