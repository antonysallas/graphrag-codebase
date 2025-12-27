"""Extractors for converting parsed AST data into graph structures."""

from .ansible.ansible_extractor import AnsibleExtractor
from .ansible.playbook_extractor import PlaybookExtractor
from .ansible.role_extractor import RoleExtractor
from .ansible.variable_extractor import VariableExtractor
from .base_extractor import BaseExtractor
from .registry import ExtractorRegistry, detect_repo_type

# Import Python and Generic extractors here when available, or let registry handle it via import
# We should probably export them if they are public.
# But for now, just Ansible is moved.

__all__ = [
    "BaseExtractor",
    "ExtractorRegistry",
    "detect_repo_type",
    "AnsibleExtractor",
    "PlaybookExtractor",
    "RoleExtractor",
    "VariableExtractor",
]
