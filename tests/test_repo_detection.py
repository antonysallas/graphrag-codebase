from src.extractors.registry import detect_repo_type


def test_detect_ansible_repo(tmp_path):
    """Test Ansible repo detection."""
    (tmp_path / "ansible.cfg").touch()
    (tmp_path / "playbooks").mkdir()
    result = detect_repo_type(tmp_path)
    assert result.repo_type == "ansible"
    assert result.confidence >= 0.6


def test_detect_python_repo(tmp_path):
    """Test Python repo detection."""
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").touch()
    result = detect_repo_type(tmp_path)
    assert result.repo_type == "python"
    assert result.confidence >= 0.5


def test_detect_generic_fallback(tmp_path):
    """Test generic fallback for unknown repos."""
    (tmp_path / "README.md").touch()
    result = detect_repo_type(tmp_path)
    assert result.repo_type == "generic"
