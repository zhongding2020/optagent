"""Backend storage abstraction layer.

Registry pattern for swappable storage implementations.
Register new backends with register() to make them available.
"""

from typing import Any, Optional

_registry: dict[str, type] = {}


def register(name: str, backend_cls: type) -> None:
    """Register a storage backend implementation."""
    _registry[name] = backend_cls


def get_backend(name: str = "sqlite") -> type:
    """Get a registered backend class."""
    if name not in _registry:
        raise ValueError(f"Unknown backend: {name}. Available: {list(_registry.keys())}")
    return _registry[name]


def list_backends() -> list[str]:
    """List all registered backends."""
    return list(_registry.keys())


class StorageBackend:
    """Optional base class for storage backends.
    
    Implement at minimum:
        get(key) -> Optional[dict]
        save(key, data) -> None
        delete(key) -> None
        list() -> list[dict]
    """
    pass
