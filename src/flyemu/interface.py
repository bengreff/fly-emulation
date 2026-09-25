"""Brain-body interface completeness.

Ben's requirement: the interface must be COMPLETE, meaning every channel the
animal has is either implemented or recorded as a known gap with its instance
count. This module registers the whole channel table, so an absent channel
becomes a row in the inventory rather than a silence.

The distinction that matters is three-way, not two-way:

    implemented        a channel exists and carries a signal
    partial            a channel exists but reads or writes the wrong thing
    absent             no channel; the neurons are in the graph and get nothing

and separately, for the absences:

    unknown in the model     nobody has wired it here
    unknown in the animal    nobody has measured it anywhere

The second kind must never be recorded as measured absence. `docs/INTERFACE.md`
holds the sources and the confidence caveats.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .registry import Registry, Status

TABLE = Path(__file__).resolve().parents[2] / "data" / "derived" / "interface_channels.csv"

# Channels whose absence is a gap in fly science, not in this model.
UNKNOWN_IN_THE_ANIMAL = {
    "gut_pharyngeal_sensory",
    "oxygen_sensing",
    "tarsal_adhesion",
}


def load() -> pd.DataFrame:
    return pd.read_csv(TABLE)


def register(reg: Registry) -> pd.DataFrame:
    """Record every interface channel, present or absent."""
    channels = load()

    for _, ch in channels.iterrows():
        name = ch.channel
        # Instance count: prefer neurons actually in the primary graph, fall
        # back to the literature count, and never invent one.
        n = ch.male_cns_count
        if pd.isna(n):
            n = ch.lit_count
        instances = int(n) if not pd.isna(n) else 0

        in_animal = name in UNKNOWN_IN_THE_ANIMAL
        evidence = str(ch.lit_source_note) if not pd.isna(ch.lit_source_note) else None
        note = str(ch.note) if not pd.isna(ch.note) else None

        if ch.implemented == "no":
            reg.provide(
                f"interface:{name}", "channel", None,
                units="dimensionless",
                model_use=f"{ch.direction}: {ch.physical_variable_or_target}",
                status=Status.UNRESOLVED,
                evidence=(
                    f"NO CHANNEL. {'Unknown in the animal: ' if in_animal else ''}"
                    f"{evidence or 'no source recorded'}"
                    + (f". {note}" if note else "")
                ),
                subsystem=f"interface_{ch.direction}",
                instances=instances,
                uncertainty=(
                    "absence of measurement in the literature, not measured "
                    "absence in the animal" if in_animal else
                    "the neurons exist in the primary graph and receive or "
                    "drive nothing"
                ),
            )
        else:
            reg.provide(
                f"interface:{name}", "channel", ch.implemented,
                units="dimensionless",
                model_use=f"{ch.direction}: {ch.physical_variable_or_target}",
                status=Status.ASSUMED,
                evidence=f"{ch.implemented} channel. {note or ''}".strip(),
                subsystem=f"interface_{ch.direction}",
                instances=instances,
                uncertainty=note,
            )

    return channels


def summary(channels: pd.DataFrame) -> str:
    absent = channels[channels.implemented == "no"]
    partial = channels[channels.implemented == "partial"]
    neurons_absent = int(absent.male_cns_count.fillna(0).sum())
    lines = [
        f"interface channels: {len(channels)} total, "
        f"{len(absent)} absent, {len(partial)} partial",
        f"  neurons in the primary graph with no channel: {neurons_absent:,}",
    ]
    for direction in ["efferent", "afferent", "physics"]:
        d = channels[channels.direction == direction]
        lines.append(
            f"  {direction:<9} {len(d):>2} channels, "
            f"{int((d.implemented == 'no').sum()):>2} absent"
        )
    return "\n".join(lines)
