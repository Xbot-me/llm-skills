"""Sandbox environments for eval execution."""

class MockFilesystem:
    """An in-memory dictionary of path -> file content."""

    def __init__(self, fixtures: dict[str, str]):
        self.files = dict(fixtures)
        self.call_log: list[dict] = []

    def read_file(self, path: str) -> str:
        """Read a file from the mock filesystem. If not found, returns 'FILE NOT FOUND'."""
        self.call_log.append({"tool": "read_file", "path": path, "order": len(self.call_log)})
        if path in self.files:
            return self.files[path]
        return "FILE NOT FOUND"
