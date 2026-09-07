"""Unit tests for GitHub Composite Action definition in action.yml."""

from pathlib import Path


def test_action_yml_structure() -> None:
    """Verify action.yml exists and contains expected metadata, inputs, and composite steps."""
    action_path = Path("action.yml")
    assert action_path.exists(), "action.yml should exist in root directory"

    content = action_path.read_text(encoding="utf-8")

    # Basic metadata checks
    assert "name: 'XIAO-RP2040 Firmware Flasher'" in content
    assert "using: 'composite'" in content

    # Inputs checks
    assert "firmware:" in content
    assert "required: true" in content
    assert "port:" in content
    assert "mount:" in content
    assert "timeout:" in content
    assert "use-picotool:" in content
    assert "json-output:" in content

    # Execution steps checks
    assert "actions/setup-python@v5" in content
    assert "pip install -e" in content
    assert "xiao-flash" in content
