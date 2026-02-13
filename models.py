"""
Data models for drug information.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List


@dataclass
class DrugInfo:
    name: str
    generic_name: Optional[str] = None
    url: str = ""
    description: Optional[str] = None
    drug_class: Optional[str] = None
    rating: Optional[float] = None
    side_effects: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_csv_row(self) -> dict:
        """Flatten side_effects list to semicolon-separated string for CSV."""
        d = self.to_dict()
        d['side_effects'] = '; '.join(d['side_effects']) if d['side_effects'] else ''
        return d
