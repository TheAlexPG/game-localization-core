"""Version tracking and change detection system"""

import json
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime


class VersionTracker:
    """Track changes between project versions"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.versions_dir = project_dir / ".versions"
        self.versions_dir.mkdir(exist_ok=True)

    def save_snapshot(self, entries: Dict[str, 'TranslationEntry'], version: str):
        """Save current state snapshot"""
        snapshot = {
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "entries": {
                key: {
                    "source_text": entry.source_text,
                    "source_hash": entry.source_hash,
                    "translated_text": entry.translated_text,
                    "status": entry.status.value
                }
                for key, entry in entries.items()
            }
        }

        snapshot_file = self.versions_dir / f"v{version}.json"
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)

    def load_snapshot(self, version: str) -> Dict:
        """Load specific version snapshot"""
        snapshot_file = self.versions_dir / f"v{version}.json"
        if not snapshot_file.exists():
            raise FileNotFoundError(f"Version {version} not found")

        with open(snapshot_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_changes(self, old_version: str, new_version: str) -> Dict[str, List[str]]:
        """Compare two versions and return changes"""
        changes = {
            "added": [],
            "removed": [],
            "modified": [],
            "needs_retranslation": []
        }

        try:
            old_snapshot = self.load_snapshot(old_version)
            new_snapshot = self.load_snapshot(new_version)
        except FileNotFoundError as e:
            return {"error": str(e)}

        old_keys = set(old_snapshot["entries"].keys())
        new_keys = set(new_snapshot["entries"].keys())

        # Find added and removed keys
        changes["added"] = list(new_keys - old_keys)
        changes["removed"] = list(old_keys - new_keys)

        # Find modified entries
        for key in old_keys & new_keys:
            old_entry = old_snapshot["entries"][key]
            new_entry = new_snapshot["entries"][key]

            # Source text changed
            if old_entry["source_hash"] != new_entry["source_hash"]:
                changes["modified"].append(key)
                # If was translated, needs retranslation
                if old_entry.get("translated_text"):
                    changes["needs_retranslation"].append(key)

        return changes

    def list_versions(self) -> List[str]:
        """List all available versions"""
        versions = []
        for file in sorted(self.versions_dir.glob("v*.json")):
            version = file.stem[1:]  # Remove 'v' prefix
            versions.append(version)
        return versions

    def get_latest_version(self) -> str:
        """Get latest version number"""
        versions = self.list_versions()
        if not versions:
            return "1.0.0"
        return versions[-1]

    def increment_version(self, version: str, bump_type: str = "patch") -> str:
        """Increment version number"""
        major, minor, patch = map(int, version.split('.'))

        if bump_type == "major":
            return f"{major + 1}.0.0"
        elif bump_type == "minor":
            return f"{major}.{minor + 1}.0"
        else:  # patch
            return f"{major}.{minor}.{patch + 1}"