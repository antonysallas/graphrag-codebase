import pytest

from src.mcp.utils import PathSanitizationError, sanitize_path


def test_blocks_traversal():
    with pytest.raises(PathSanitizationError, match="Path traversal detected"):
        sanitize_path("../../../etc/passwd")


def test_blocks_null_byte():
    with pytest.raises(PathSanitizationError, match="Null byte in path"):
        sanitize_path("file.yml\x00.txt")


def test_allows_relative():
    result = sanitize_path("playbooks/deploy.yml")
    assert result == "playbooks/deploy.yml"


def test_validates_within_base():
    result = sanitize_path("roles/common/tasks/main.yml", allowed_base="/home/user/ansible")
    # The result will be an absolute path when allowed_base is provided
    assert "/home/user/ansible/roles/common/tasks/main.yml" in result


def test_blocks_absolute_by_default():
    with pytest.raises(PathSanitizationError, match="Absolute paths not allowed"):
        sanitize_path("/etc/passwd")


def test_allows_absolute_when_configured():
    # Only if it's within the allowed base if one is set
    with pytest.raises(PathSanitizationError, match="Path escapes allowed directory"):
        sanitize_path("/etc/passwd", allowed_base="/home/user/ansible", allow_absolute=True)


def test_allows_absolute_within_base():
    result = sanitize_path(
        "/home/user/ansible/roles/main.yml", allowed_base="/home/user/ansible", allow_absolute=True
    )
    assert result == "/home/user/ansible/roles/main.yml"
