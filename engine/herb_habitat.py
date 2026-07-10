"""Herb habitat tags; wild territory vs Thunderpath vs Twoleg compounds."""

from __future__ import annotations

from herbs import HERBS


def herb_habitat(meta: dict) -> tuple[str, ...]:
    return tuple(meta.get("habitat", ("wild",)))




def herbs_for_verge(site: str) -> list[str]:
    return [
        key
        for key, meta in HERBS.items()
        if site in herb_habitat(meta)
        and meta.get("rarity") != "restricted"
        and not meta.get("poison")
    ]
