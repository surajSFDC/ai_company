"""File operations for agents."""
import os
from pathlib import Path


class FileOperations:
    """Handle file operations safely."""

    def __init__(self, workspace_dir: str = "./workspace") -> None:
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)

    def write_file(self, filename: str, content: str, subdir: str = "") -> str:
        """Write content to a file."""
        if subdir:
            target_dir = self.workspace_dir / subdir
        else:
            target_dir = self.workspace_dir

        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(file_path)

    def read_file(self, filepath: str) -> str:
        """Read content from a file."""
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def list_files(self, subdir: str = "") -> list:
        """List all files in workspace or subdirectory."""
        if subdir:
            target_dir = self.workspace_dir / subdir
        else:
            target_dir = self.workspace_dir

        if not target_dir.exists():
            return []

        return [
            str(p.relative_to(self.workspace_dir))
            for p in target_dir.rglob("*")
            if p.is_file()
        ]

    def get_workspace_path(self) -> Path:
        """Get the workspace directory path."""
        return self.workspace_dir

