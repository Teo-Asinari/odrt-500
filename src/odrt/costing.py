"""WP6 economics: BOM from cited prices only, plus explicit retail scenarios.

Unpriced lines stay unpriced and are counted, never filled in. Currencies are
not converted (no FX assumption); only USD lines are summed.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from odrt.config import ConfigError

COLUMNS = ("item", "qty", "unit_price", "currency", "price_basis", "source_url", "accessed", "notes")


@dataclass(frozen=True)
class Line:
    item: str
    qty: int
    unit_price: Optional[float]
    currency: str
    price_basis: str
    source_url: str
    accessed: str
    notes: str

    @property
    def total(self) -> Optional[float]:
        return None if self.unit_price is None else self.qty * self.unit_price


def load_bom(path: Path) -> list:
    with Path(path).open(newline="") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ConfigError(f"{path}: columns must be exactly {list(COLUMNS)}")
        rows = list(reader)
    lines = []
    for i, r in enumerate(rows, start=2):
        w = f"{path}: line {i}"
        try:
            qty = int(r["qty"])
        except ValueError:
            raise ConfigError(f"{w}.qty: not an integer") from None
        if qty < 1:
            raise ConfigError(f"{w}.qty: must be >= 1")
        price = None
        if r["unit_price"].strip():
            try:
                price = float(r["unit_price"])
            except ValueError:
                raise ConfigError(f"{w}.unit_price: not a number") from None
            if price <= 0:
                raise ConfigError(f"{w}.unit_price: must be > 0")
            if not r["currency"] or not r["source_url"].startswith("https://") or \
                    not re.match(r"^\d{4}-\d{2}-\d{2}$", r["accessed"]):
                raise ConfigError(f"{w}: a price needs a currency, https source_url and YYYY-MM-DD accessed date")
        lines.append(Line(r["item"].strip(), qty, price, r["currency"].strip(), r["price_basis"].strip(),
                          r["source_url"].strip(), r["accessed"].strip(), r["notes"].strip()))
    if not lines:
        raise ConfigError(f"{path}: empty BOM")
    return lines


def summary(lines) -> dict:
    usd = sum(l.total for l in lines if l.total is not None and l.currency == "USD")
    other = {}
    for l in lines:
        if l.total is not None and l.currency != "USD":
            other[l.currency] = other.get(l.currency, 0.0) + l.total
    return {"known_usd": usd, "known_other": other,
            "unpriced_lines": sum(1 for l in lines if l.unit_price is None), "lines": len(lines)}


def retail_from_bom(bom_usd: float, multiplier: float) -> float:
    return bom_usd * multiplier


def max_bom_for_retail(retail_usd: float, multiplier: float) -> float:
    return retail_usd / multiplier
