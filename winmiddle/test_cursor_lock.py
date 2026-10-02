"""Cursor lock: real pointer stays on the origin; warp to the ghost on release."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from evdev import InputEvent, ecodes

from winmiddle.autoscroll import Mode
from winmiddle.config import Config
from winmiddle.daemon import MiddleDaemon
from winmiddle.devices import WARP_ABS_MAX, desktopToWarpAbs
from winmiddle.focus import FocusState

DESKTOP = (0, 0, 4480, 1440)


def _daemon(*, lockCursor: bool = True, warp: bool = True) -> MiddleDaemon:
    cfg = Config()
    cfg.lockCursor = lockCursor
    hub = MagicMock()
    hub.snapshot.return_value = FocusState(
        resourceClass="discord",
        cursorX=1000,
        cursorY=500,
        workArea=(0, 0, 2560, 1400),
        desktop=DESKTOP,
    )
    daemon = MiddleDaemon(cfg, hub, overlay=MagicMock())
    daemon.warp = MagicMock() if warp else None
    return daemon


def _rel(code: int, value: int) -> InputEvent:
    return InputEvent(0, 0, ecodes.EV_REL, code, value)


def _middleUp() -> InputEvent:
    return InputEvent(0, 0, ecodes.EV_KEY, ecodes.BTN_MIDDLE, 0)


def testLockedMotionIsNotForwarded() -> None:
    daemon = _daemon()
    ui = MagicMock()
    daemon._enterAutoscroll(Mode.HOLD_AUTOSCROLL)
    assert daemon._cursorLocked
    with patch("winmiddle.daemon.injectRelative") as inject:
        daemon._handleEvent(ui, _rel(ecodes.REL_Y, 120), passthroughMiddle=False)
        daemon._handleEvent(ui, _rel(ecodes.REL_X, -30), passthroughMiddle=False)
    inject.assert_not_called()
    assert daemon._autoscrollVector() == (-30.0, 120.0)
    daemon.overlay.requestGhost.assert_called_with(970.0, 620.0)


def testReleaseWarpsToBroughtPosition() -> None:
    daemon = _daemon()
    ui = MagicMock()
    with patch("winmiddle.daemon.warpPointer") as warp:
        daemon._enterAutoscroll(Mode.HOLD_AUTOSCROLL)
        # Lock-in pins the real cursor on the (possibly lagging) origin.
        warp.assert_called_once_with(daemon.warp, 1000.0, 500.0, DESKTOP)
        daemon._handleEvent(ui, _rel(ecodes.REL_Y, 3000), passthroughMiddle=False)  # clamped
        daemon._handleEvent(ui, _middleUp(), passthroughMiddle=False)
    warp.assert_called_with(daemon.warp, 1000.0, 1399.0, DESKTOP)
    assert warp.call_count == 2
    assert daemon.mode == Mode.IDLE
    assert not daemon._cursorLocked


def testUnlockedForwardsMotionAndNeverWarps() -> None:
    daemon = _daemon(lockCursor=False)
    ui = MagicMock()
    daemon._enterAutoscroll(Mode.HOLD_AUTOSCROLL)
    assert not daemon._cursorLocked
    with patch("winmiddle.daemon.injectRelative") as inject, patch("winmiddle.daemon.warpPointer") as warp:
        daemon._handleEvent(ui, _rel(ecodes.REL_Y, 40), passthroughMiddle=False)
        daemon._handleEvent(ui, _middleUp(), passthroughMiddle=False)
    inject.assert_called_once_with(ui, ecodes.REL_Y, 40)
    warp.assert_not_called()


def testNoWarpDeviceFallsBackToUnlocked() -> None:
    daemon = _daemon(warp=False)
    daemon._enterAutoscroll(Mode.HOLD_AUTOSCROLL)
    assert not daemon._cursorLocked


def testRealCursorHiddenWhileLocked() -> None:
    daemon = _daemon()
    daemon.cursorHider = MagicMock()
    ui = MagicMock()
    with patch("winmiddle.daemon.warpPointer"):
        daemon._enterAutoscroll(Mode.HOLD_AUTOSCROLL)
        daemon.cursorHider.hide.assert_called_once()
        daemon.cursorHider.show.assert_not_called()
        daemon._handleEvent(ui, _middleUp(), passthroughMiddle=False)
    daemon.cursorHider.show.assert_called_once()


def testDesktopToWarpAbs() -> None:
    assert desktopToWarpAbs(0, 0, DESKTOP) == (0, 0)
    assert desktopToWarpAbs(1000, 500, DESKTOP) == (round(1000 * WARP_ABS_MAX / 4480), round(500 * WARP_ABS_MAX / 1440))
    # Offscreen targets clamp to the last pixel, never past the range.
    x, y = desktopToWarpAbs(99999, -50, DESKTOP)
    assert x < WARP_ABS_MAX and y == 0


if __name__ == "__main__":
    testLockedMotionIsNotForwarded()
    testReleaseWarpsToBroughtPosition()
    testUnlockedForwardsMotionAndNeverWarps()
    testNoWarpDeviceFallsBackToUnlocked()
    testRealCursorHiddenWhileLocked()
    testDesktopToWarpAbs()
    print("ok")
