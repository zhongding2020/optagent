from pathlib import Path
from typing import Optional
from .types import SkillMeta


class SkillRegistry:
    """Wraps deepagents SkillsMiddleware source configuration."""

    def __init__(self):
        self._sources: list[str] = []
        self._skills: dict[str, SkillMeta] = {}

    @property
    def sources(self) -> list[str]:
        return self._sources

    def register(self, path: str) -> list[SkillMeta]:
        """Add a skill directory and scan for skills."""
        if path not in self._sources:
            self._sources.append(path)
        return self._scan(path)

    def unregister(self, name: str) -> bool:
        """Remove a skill by name."""
        if name in self._skills:
            del self._skills[name]
            return True
        return False

    def reload(self) -> list[SkillMeta]:
        """Re-scan all sources and return all skills."""
        self._skills.clear()
        for src in self._sources:
            self._scan(src)
        return self.get_all()

    def get_all(self) -> list[SkillMeta]:
        return list(self._skills.values())

    def get(self, name: str) -> Optional[SkillMeta]:
        return self._skills.get(name)

    def _scan(self, source_path: str) -> list[SkillMeta]:
        found: list[SkillMeta] = []
        base = Path(source_path)
        if not base.exists():
            return found

        for skill_dir in base.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            meta = self._parse_skill_meta(skill_file)
            if meta:
                self._skills[meta.name] = meta
                found.append(meta)
        return found

    def _parse_skill_meta(self, path: Path) -> Optional[SkillMeta]:
        import yaml
        content = path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return None
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None
        try:
            meta = yaml.safe_load(parts[1])
        except Exception:
            return None
        if not meta or "name" not in meta or "description" not in meta:
            return None
        return SkillMeta(
            name=meta["name"],
            description=meta["description"],
            path=str(path),
            license=meta.get("license"),
        )
