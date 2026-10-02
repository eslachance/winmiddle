"""Hide the real pointer while it is pinned (optional KWin effect `winmiddlecursor`).

Only KWin can hide the cursor on Wayland. The bundled effect (kwin-effect/)
exposes Hide/Show on KWin's bus name; without it these calls fail silently and
the pinned real cursor simply stays visible next to the ghost pointer.
"""

from __future__ import annotations

import logging
import time

from PyQt6.QtDBus import QDBusConnection, QDBusMessage

log = logging.getLogger("winmiddle.kwincursor")

EFFECT_ID = "winmiddlecursor"
_SERVICE = "org.kde.KWin"
_PATH = "/WinmiddleCursor"
_INTERFACE = "local.winmiddle.Cursor"
# KWin re-shows the cursor if no Hide arrives within this window (crash/hang guard).
FAILSAFE_MS = 3000
RENEW_SEC = 1.0


class KwinCursorHider:
    def __init__(self) -> None:
        self._bus = QDBusConnection.sessionBus()
        self._hidden = False
        self._lastHideTs = 0.0
        self.available = False

    def ensureLoaded(self) -> bool:
        """Load the effect if installed; returns whether hiding is available."""
        if not self._bus.isConnected():
            return False
        for method in ("isEffectLoaded", "loadEffect"):
            msg = QDBusMessage.createMethodCall(_SERVICE, "/Effects", "org.kde.kwin.Effects", method)
            msg.setArguments([EFFECT_ID])
            reply = self._bus.call(msg, timeout=2000)
            if reply.type() == QDBusMessage.MessageType.ReplyMessage and reply.arguments() and reply.arguments()[0]:
                self.available = True
                break
        if self.available:
            log.info("KWin effect %s loaded — real cursor hidden while pinned", EFFECT_ID)
        else:
            log.info("KWin effect %s not installed — pinned cursor stays visible", EFFECT_ID)
        return self.available

    def _send(self, method: str, *args) -> None:
        msg = QDBusMessage.createMethodCall(_SERVICE, _PATH, _INTERFACE, method)
        if args:
            msg.setArguments(list(args))
        self._bus.send(msg)

    def hide(self) -> None:
        if not self.available:
            return
        self._hidden = True
        self._lastHideTs = time.monotonic()
        self._send("Hide", FAILSAFE_MS)

    def renew(self) -> None:
        """Call regularly while hidden so the KWin fail-safe never fires mid-scroll."""
        if self._hidden and time.monotonic() - self._lastHideTs >= RENEW_SEC:
            self.hide()

    def show(self) -> None:
        if not self._hidden:
            return
        self._hidden = False
        self._send("Show")
