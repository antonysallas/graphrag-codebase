"""Configuration management for GraphRAG pipeline."""

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Neo4jConfig(BaseSettings):
    """Neo4j database configuration."""

    uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    user: str = Field(default="neo4j", description="Neo4j username")
    password: str = Field(default="neo4j", description="Neo4j password")
    database: str = Field(default="neo4j", description="Neo4j database name")
    query_timeout: float = Field(default=10.0, description="Query timeout in seconds")
    connection_timeout: float = Field(
        default=5.0, description="Connection acquisition timeout in seconds"
    )

    model_config = SettingsConfigDict(
        env_prefix="NEO4J_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class PipelineConfig(BaseSettings):
    """Pipeline execution configuration."""

    codebase_path: Optional[str] = Field(
        default=None, description="Path to Ansible codebase to analyze"
    )
    repository_id: Optional[str] = Field(
        default=None, description="Repository identifier for multi-repo mode"
    )
    batch_size: int = Field(default=100, description="Batch size for graph operations")
    max_workers: int = Field(default=4, description="Max parallel workers for parsing")
    log_level: str = Field(default="INFO", description="Logging level")

    # Git configuration
    git_repo_url: str = Field(default="", description="Git repository URL to clone")
    git_branch: str = Field(default="main", description="Git branch to checkout")
    git_token: str = Field(default="", description="Git authentication token")
    workspace_dir: Path = Field(
        default=Path("/workspace"), description="Directory for cloned repos"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class LLMConfig(BaseSettings):
    """LLM configuration."""

    provider: str = Field(default="vllm", validation_alias="LLM_PROVIDER")
    api_base: str = Field(default="http://localhost:11434/v1", validation_alias="API_BASE")
    api_key: str = Field(default="fake", validation_alias="LLM_API_KEY")
    model_name: str = Field(default="Qwen/Qwen2.5-Coder-7B-Instruct", validation_alias="MODEL_NAME")
    temperature: float = Field(default=0.0, validation_alias="TEMPERATURE")
    max_tokens: int = Field(default=2048, validation_alias="MAX_TOKENS")
    top_p: float = Field(default=0.95, validation_alias="TOP_P")
    prompt_template: str = Field(default="default", validation_alias="LLM_PROMPT_TEMPLATE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class MCPConfig(BaseSettings):
    """MCP Server configuration."""

    server_host: str = "127.0.0.1"
    server_port: int = 5003
    require_auth: bool = False
    debug: bool = False
    rate_limit_per_minute: int = 100
    rate_limit_burst: int = 10

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class LangfuseConfig(BaseSettings):
    """Langfuse observability configuration."""

    enabled: bool = Field(default=False, validation_alias="LANGFUSE_ENABLED")
    secret_key: str = Field(default="", validation_alias="LANGFUSE_SECRET_KEY")
    public_key: str = Field(default="", validation_alias="LANGFUSE_PUBLIC_KEY")
    host: str = Field(default="https://cloud.langfuse.com", validation_alias="LANGFUSE_HOST")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Config:
    """Main configuration aggregator."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration.

        Args:
            config_dir: Optional path to config directory. Defaults to ./config
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "config"

        self.config_dir = Path(config_dir)
        self.neo4j = Neo4jConfig()
        self.pipeline = PipelineConfig()
        self.llm = LLMConfig()
        self.mcp = MCPConfig()
        self.langfuse = LangfuseConfig()
        self.schema = self._load_schema()

    def _load_schema(self) -> dict[str, Any]:
        """Load graph schema from YAML file.

        Returns:
            Dictionary containing schema definition
        """
        schema_path = self.config_dir / "schema.yaml"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(schema_path, "r") as f:
            return yaml.safe_load(f)  # type: ignore[no-any-return]

    def get_node_types(self) -> list[str]:
        """Get list of all node types defined in schema.

        Returns:
            List of node type names
        """
        return list(self.schema.get("nodes", {}).keys())

    def get_relationship_types(self) -> list[str]:
        """Get list of all relationship types defined in schema.

        Returns:
            List of relationship type names
        """
        return list(self.schema.get("relationships", {}).keys())

    def get_node_properties(self, node_type: str) -> list[dict[str, Any]]:
        """Get properties for a specific node type.

        Args:
            node_type: Name of the node type

        Returns:
            List of property definitions
        """
        return self.schema.get("nodes", {}).get(node_type, {}).get("properties", [])  # type: ignore[no-any-return]

    def get_relationship_properties(self, rel_type: str) -> list[dict[str, Any]]:
        """Get properties for a specific relationship type.

        Args:
            rel_type: Name of the relationship type

        Returns:
            List of property definitions
        """
        return self.schema.get("relationships", {}).get(rel_type, {}).get("properties", [])  # type: ignore[no-any-return]


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance.

    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def init_config(config_dir: Optional[Path] = None) -> Config:
    """Initialize configuration with custom config directory.

    Args:
        config_dir: Optional path to config directory

    Returns:
        Config instance
    """
    global _config
    _config = Config(config_dir=config_dir)
    return _config
