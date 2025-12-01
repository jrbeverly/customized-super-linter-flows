"""The immutable inspection shared by all framework stages."""

import json
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class Inspection:
    """Repository facts frozen at construction so consumers cannot modify them.

    Accepts plain dicts and replaces them with read-only views, so every
    path a consumer can reach through the inspection is immutable.
    """

    features: MappingProxyType
    configs: MappingProxyType

    def __post_init__(self):
        object.__setattr__(self, "features", MappingProxyType(dict(self.features)))
        configs = {
            name: MappingProxyType(dict(cfg)) for name, cfg in self.configs.items()
        }
        object.__setattr__(self, "configs", MappingProxyType(configs))

    def to_json(self):
        payload = {
            "features": dict(self.features),
            "configs": {name: dict(cfg) for name, cfg in self.configs.items()},
        }
        return json.dumps(payload, sort_keys=True, indent=2) + "\n"
