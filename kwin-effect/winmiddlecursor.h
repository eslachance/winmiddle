/*
    winmiddle cursor — hide the real pointer while winmiddle pins it.

    During autoscroll winmiddle stops forwarding motion (the real pointer stays
    on the origin so the pane under it keeps the wheel) and draws a ghost
    pointer instead. Only KWin can hide the real cursor; scripts can't, so
    this tiny effect exposes it on D-Bus:

        org.kde.KWin /WinmiddleCursor local.winmiddle.Cursor.Hide(int timeoutMs)
        org.kde.KWin /WinmiddleCursor local.winmiddle.Cursor.Show()

    Fail-safe: the cursor comes back when the timeout lapses without a renewed
    Hide, when the caller drops off the bus, or when the effect unloads.
*/

#pragma once

#include "effect/effect.h"

#include <QDBusContext>
#include <QDBusServiceWatcher>
#include <QTimer>

namespace KWin
{

class WinmiddleCursorEffect : public Effect, protected QDBusContext
{
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface", "local.winmiddle.Cursor")

public:
    WinmiddleCursorEffect();
    ~WinmiddleCursorEffect() override;

    bool isActive() const override;

public Q_SLOTS:
    Q_SCRIPTABLE void Hide(int timeoutMs);
    Q_SCRIPTABLE void Show();

private:
    void showCursor();

    bool m_hidden = false;
    QTimer m_failsafe;
    QDBusServiceWatcher m_callerWatcher;
};

} // namespace KWin
