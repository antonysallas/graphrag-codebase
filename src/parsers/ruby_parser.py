"""Ruby parser for Vagrantfiles."""

from typing import Any

from .base_parser import BaseParser, ParseResult


class RubyParser(BaseParser):
    """Parser for Ruby files (mainly Vagrantfiles)."""

    def __init__(self):
        """Initialize Ruby parser."""
        super().__init__("ruby")

    def extract_metadata(self, parse_result: ParseResult) -> dict[str, Any]:
        """Extract metadata from Ruby file.

        Args:
            parse_result: Parse result

        Returns:
            Dictionary with Ruby file metadata
        """
        metadata = {
            "is_vagrantfile": False,
            "vagrant_config": {},
            "vms": [],
            "provisioners": [],
        }

        if not parse_result.root_node:
            return metadata

        # Check if it's a Vagrantfile
        content = parse_result.content
        if "Vagrant.configure" in content:
            metadata["is_vagrantfile"] = True
            metadata["vagrant_config"] = self._extract_vagrant_config(content)
            metadata["vms"] = self._extract_vm_configs(content)
            metadata["provisioners"] = self._extract_provisioners(content)

        return metadata

    def _extract_vagrant_config(self, content: str) -> dict[str, Any]:
        """Extract Vagrant configuration from Vagrantfile.

        Args:
            content: Vagrantfile content

        Returns:
            Dictionary with Vagrant config
        """
        import re

        config = {}

        # Extract API version
        api_version_match = re.search(r'VAGRANTFILE_API_VERSION\s*=\s*"(\d+)"', content)
        if api_version_match:
            config["api_version"] = api_version_match.group(1)

        # Extract box
        box_match = re.search(r'config\.vm\.box\s*=\s*["\']([^"\']+)["\']', content)
        if box_match:
            config["box"] = box_match.group(1)

        # Extract hostname
        hostname_match = re.search(r'config\.vm\.hostname\s*=\s*["\']([^"\']+)["\']', content)
        if hostname_match:
            config["hostname"] = hostname_match.group(1)

        # Extract network config
        network_matches = re.finditer(
            r'config\.vm\.network\s+["\'](\w+)["\'],?\s*ip:\s*["\']([^"\']+)["\']', content
        )
        networks = []
        for match in network_matches:
            networks.append({"type": match.group(1), "ip": match.group(2)})
        if networks:
            config["networks"] = networks

        return config

    def _extract_vm_configs(self, content: str) -> list[dict[str, Any]]:
        """Extract VM configurations from Vagrantfile.

        Args:
            content: Vagrantfile content

        Returns:
            List of VM configurations
        """
        import re

        vms = []

        # Match config.vm.define blocks
        vm_define_pattern = r'config\.vm\.define\s+["\'](\w+)["\']'
        for match in re.finditer(vm_define_pattern, content):
            vms.append({"name": match.group(1)})

        return vms

    def _extract_provisioners(self, content: str) -> list[dict[str, Any]]:
        """Extract provisioner configurations.

        Args:
            content: Vagrantfile content

        Returns:
            List of provisioners
        """
        import re

        provisioners = []

        # Match Ansible provisioner
        ansible_pattern = r'config\.vm\.provision\s+["\']ansible["\']\s+do\s+\|\w+\|'
        if re.search(ansible_pattern, content):
            playbook_match = re.search(r'ansible\.playbook\s*=\s*["\']([^"\']+)["\']', content)
            if playbook_match:
                provisioners.append({"type": "ansible", "playbook": playbook_match.group(1)})

        # Match shell provisioner
        shell_pattern = r'config\.vm\.provision\s+["\']shell["\']\s*,?\s*inline:'
        if re.search(shell_pattern, content):
            provisioners.append({"type": "shell", "inline": True})

        return provisioners
