"""ModifierTracker must drop vanished keyboards instead of spinning select()."""

from __future__ import annotations

from winmiddle.modifiers import ModifierTracker


class _DeadDevice:
    path = "/dev/input/event4"
    fd = 99

    def read(self):
        raise OSError(19, "No such device")

    def close(self):
        pass


def testDrainDropsDeadDevice():
    dead = _DeadDevice()
    tracker = ModifierTracker(devices=[dead])
    tracker._down.add(1)
    tracker.drain(dead)
    assert tracker.devices == []
    assert tracker.fds == []
    assert not tracker._down


if __name__ == "__main__":
    testDrainDropsDeadDevice()
    print("ok")
