"""Repository type detection and extractor registry."""

from pathlib import Path
from typing import Any, Callable, Literal, NamedTuple, Type

from loguru import logger

RepoType = Literal["ansible", "python", "generic"]


class DetectionResult(NamedTuple):
    """Result of repository type detection."""

    repo_type: RepoType
    confidence: float  # 0.0 to 1.0
    indicators: list[str]  # Files/patterns that matched


def detect_repo_type(path: Path) -> DetectionResult:
    """Detect repository type based on file patterns.

    Args:
        path: Path to the repository root.

    Returns:
        DetectionResult with type, confidence, and matched indicators.
    """
    path = Path(path)

    # Ansible detection (highest priority for this project)
    ansible_indicators = [
        path / "ansible.cfg",
        path / "playbooks",
        path / "roles",
        path / "inventory",
        path / "group_vars",
        path / "host_vars",
        path / ".ansible",  # Ansible config directory
    ]
    ansible_matches = [str(p) for p in ansible_indicators if p.exists()]

    # Also check for playbook files (YAML with hosts/tasks patterns)
    playbook_files = list(path.rglob("**/playbook*.yml")) + list(path.rglob("**/playbook*.yaml"))
    playbook_files += list(path.rglob("**/site.yml")) + list(path.rglob("**/main.yml"))

    # Check for tasks directories (strong Ansible indicator)
    tasks_dirs = list(path.rglob("**/tasks"))
    handlers_dirs = list(path.rglob("**/handlers"))

    if playbook_files:
        ansible_matches.append(f"playbook files ({len(playbook_files)} found)")
    if tasks_dirs:
        ansible_matches.append(f"tasks directories ({len(tasks_dirs)} found)")
    if handlers_dirs:
        ansible_matches.append(f"handlers directories ({len(handlers_dirs)} found)")

    if ansible_matches:
        # More matches = higher confidence
        confidence = min(1.0, len(ansible_matches) / 3)
        logger.info(f"Detected Ansible repo (confidence: {confidence:.2f}): {ansible_matches}")
        return DetectionResult("ansible", confidence, ansible_matches)

    # Python detection
    python_indicators = [
        path / "pyproject.toml",
        path / "setup.py",
        path / "setup.cfg",
        path / "requirements.txt",
    ]
    python_matches = [str(p) for p in python_indicators if p.exists()]

    # Also check for __init__.py in src/ or top-level
    if (path / "src").is_dir():
        init_files = list((path / "src").rglob("__init__.py"))
        if init_files:
            python_matches.append(f"src/**/__init__.py ({len(init_files)} files)")

    if python_matches:
        confidence = min(1.0, len(python_matches) / 2)
        logger.info(f"Detected Python repo (confidence: {confidence:.2f})")
        return DetectionResult("python", confidence, python_matches)

    # Generic fallback
    logger.info("No specific repo type detected, using generic")
    return DetectionResult("generic", 0.5, ["fallback"])


class ExtractorRegistry:
    """Registry for repository extractors."""

    _extractors: dict[RepoType, Type[Any]] = {}

    @classmethod
    def register(cls, repo_type: RepoType) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register an extractor for a repo type."""

        def decorator(extractor_cls: Type[Any]) -> Type[Any]:
            cls._extractors[repo_type] = extractor_cls
            logger.debug(f"Registered {extractor_cls.__name__} for {repo_type}")
            return extractor_cls

        return decorator

    @classmethod
    def get_extractor(cls, repo_type: RepoType) -> Type[Any]:
        """Get extractor class for the given repo type."""
        if repo_type not in cls._extractors:
            raise ValueError(f"No extractor registered for {repo_type}")
        return cls._extractors[repo_type]

    @classmethod
    def detect_and_get(cls, path: Path) -> tuple[Type[Any], DetectionResult]:
        """Auto-detect repo type and return appropriate extractor."""
        result = detect_repo_type(path)
        return cls.get_extractor(result.repo_type), result
