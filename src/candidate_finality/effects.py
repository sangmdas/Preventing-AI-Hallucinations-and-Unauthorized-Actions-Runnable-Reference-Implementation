from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class DefiniteEffectFailure(Exception):
    pass


class UnknownEffectResult(Exception):
    pass


class EffectAdapter(Protocol):
    def effect(self, consequence_type: str, output: str, execution_material: str, handle_id: str) -> str: ...


@dataclass
class SimulatedEffectSink:
    effects: list[tuple[str, str, str]]

    def __init__(self) -> None:
        self.effects = []

    def effect(self, consequence_type: str, output: str, execution_material: str, handle_id: str) -> str:
        if not execution_material:
            raise DefiniteEffectFailure("missing execution material")
        effect_id = f"effect-{consequence_type.lower()}-{len(self.effects) + 1}"
        self.effects.append((handle_id, consequence_type, output))
        return effect_id

