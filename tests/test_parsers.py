"""Tests for parsers."""

from src.parsers import JinjaParser, PythonParser, YAMLParser


class TestYAMLParser:
    """Tests for YAML parser."""

    def test_parse_playbook(self):
        """Test parsing a simple playbook."""
        parser = YAMLParser()

        playbook_content = """
---
- hosts: all
  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present
"""

        result = parser.parse_string(playbook_content, "test.yml")

        assert result.is_success
        assert result.metadata.get("is_playbook") is True
        assert result.metadata.get("has_tasks") is True

    def test_parse_vars_file(self):
        """Test parsing a vars file."""
        parser = YAMLParser()

        vars_content = """
---
mysql_root_password: secret
mysql_database: myapp
mysql_user: appuser
"""

        result = parser.parse_string(vars_content, "vars.yml")

        assert result.is_success
        assert result.metadata.get("is_vars_file") is True
        assert result.metadata.get("var_count") == 3


class TestJinjaParser:
    """Tests for Jinja2 parser."""

    def test_extract_variables(self):
        """Test extracting variables from template."""
        parser = JinjaParser()

        template_content = """
server {
    listen {{ nginx_port }};
    server_name {{ server_name }};

    location / {
        proxy_pass {{ backend_url }};
    }
}
"""

        result = parser.parse_string(template_content, "nginx.conf.j2")

        assert result.is_success
        variables = result.metadata.get("variables_used", [])
        assert "nginx_port" in variables
        assert "server_name" in variables
        assert "backend_url" in variables


class TestPythonParser:
    """Tests for Python parser."""

    def test_parse_functions(self):
        """Test parsing Python functions."""
        parser = PythonParser()

        python_content = """
def get_inventory():
    return {"all": {"hosts": ["host1", "host2"]}}

def parse_cli_args():
    return {}
"""

        result = parser.parse_string(python_content, "inventory.py")

        assert result.is_success
        functions = result.metadata.get("functions", [])
        assert len(functions) == 2
        assert result.metadata.get("is_inventory_script") is True
