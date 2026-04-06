"""
net_launcher.py — AEGIS-X Launch Decision Engine
=================================================
Public interface stub. Core implementation is proprietary.

Manages the full launch lifecycle with multi-condition gating:

  IDLE → COMMIT → FIRED → RELOAD → IDLE

Gate conditions for COMMIT:
  • track_quality  ≥ COMMIT_TQ  (0.55)
  • MIN_DIST (0.5m) ≤ dist ≤ MAX_DIST (4.0m)
  • 0 < tgo ≤ MAX_TGO (3.0s)

Stale guard: aborts if target does not close by STALE_CLOSURE (1.5m)
             within STALE_STEPS (120) ticks.

Reload cooldown: RELOAD_STEPS (25) ticks before re-arming.

Author : SentrixLab
Version: 17.0
License: Proprietary — contact for licensing
"""

from enum import Enum, auto
from typing import Optional
import numpy as np


class LaunchDecision(Enum):
    """Per-tick decision returned by NetLauncher.decide()."""
    WAIT   = auto()   # still tracking / aligning — no action
    FIRE   = auto()   # fire now — send LAUNCH to Arduino
    ABORT  = auto()   # stale guard triggered — lost track
    RELOAD = auto()   # in reload cooldown — not available


class LauncherState(Enum):
    """Internal state machine state."""
    IDLE   = auto()
    COMMIT = auto()
    FIRED  = auto()
    RELOAD = auto()


class NetLauncher:
    """
    Multi-condition launch decision engine.

    Decouples launch logic from guidance — receives track quality,
    distance, and time-to-go from the main pipeline; decides FIRE/WAIT.

    Usage
    -----
    launcher = NetLauncher(arduino_bridge=bridge)

    # In main control loop (called every tick):
    decision = launcher.decide(
        target_pos    = tracker.fpos(),
        track_quality = tracker.track_quality(),
        tgo           = tgo_from_guidance,
        dist          = dist_to_target,
    )
    if decision == LaunchDecision.FIRE:
        bridge.send_command("LAUNCH")
    """

    # ── Tunable gate parameters ───────────────────────────────────
    COMMIT_TQ:    float = 0.55   # minimum track quality to enter COMMIT
    MIN_DIST:     float = 0.5    # metres — minimum engagement range
    MAX_DIST:     float = 4.0    # metres — maximum engagement range
    MAX_TGO:      float = 3.0    # seconds — abort if tgo exceeds this
    COMMIT_STEPS: int   = 5      # ticks to hold COMMIT before firing
    STALE_STEPS:  int   = 120    # ticks without closure → ABORT
    STALE_CLOSURE: float = 1.5   # metres — min closure to reset stale counter
    RELOAD_STEPS: int   = 25     # ticks for reload (~2s at 12.5 Hz)

    def __init__(self, arduino_bridge):
        """
        Args:
            arduino_bridge: ArduinoBridge instance for LAUNCH command dispatch
        """
        raise NotImplementedError("Proprietary — contact SentrixLab for licensing")

    @property
    def state(self) -> LauncherState:
        """Current state machine state."""
        raise NotImplementedError

    def decide(
        self,
        target_pos:    np.ndarray,
        track_quality: float,
        tgo:           float,
        dist:          float,
    ) -> LaunchDecision:
        """
        Evaluate all gate conditions and advance state machine.

        Must be called every control tick (even during RELOAD).

        Args:
            target_pos    : current target position [x, y, z]
            track_quality : IMMTracker.track_quality() — 0.0–1.0
            tgo           : time-to-go from guidance solver (seconds)
            dist          : current range to target (metres)

        Returns:
            LaunchDecision enum value
        """
        raise NotImplementedError

    def reset(self) -> None:
        """
        Force state to IDLE. Use for emergency stop or between engagements.
        """
        raise NotImplementedError

    def stats(self) -> dict:
        """
        Return launch statistics dict.

        Returns:
            {
                'launches': int,   # total successful fire events
                'aborts':   int,   # total stale-guard aborts
                'state':    str,   # current state name
            }
        """
        raise NotImplementedError
