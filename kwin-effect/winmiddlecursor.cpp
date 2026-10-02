#include "winmiddlecursor.h"

#include "effect/effecthandler.h"

#include <QDBusConnection>
#include <QDBusMessage>

namespace KWin
{

static const QString s_path = QStringLiteral("/WinmiddleCursor");

WinmiddleCursorEffect::WinmiddleCursorEffect()
{
    m_failsafe.setSingleShot(true);
    connect(&m_failsafe, &QTimer::timeout, this, &WinmiddleCursorEffect::showCursor);

    m_callerWatcher.setConnection(QDBusConnection::sessionBus());
    m_callerWatcher.setWatchMode(QDBusServiceWatcher::WatchForUnregistration);
    connect(&m_callerWatcher, &QDBusServiceWatcher::serviceUnregistered, this, &WinmiddleCursorEffect::showCursor);

    QDBusConnection::sessionBus().registerObject(s_path, this, QDBusConnection::ExportScriptableSlots);
}

WinmiddleCursorEffect::~WinmiddleCursorEffect()
{
    QDBusConnection::sessionBus().unregisterObject(s_path);
    showCursor();
}

bool WinmiddleCursorEffect::isActive() const
{
    return false;
}

void WinmiddleCursorEffect::Hide(int timeoutMs)
{
    if (calledFromDBus()) {
        m_callerWatcher.setWatchedServices({message().service()});
    }
    m_failsafe.start(qBound(100, timeoutMs, 10000));
    if (!m_hidden) {
        effects->hideCursor();
        m_hidden = true;
    }
}

void WinmiddleCursorEffect::Show()
{
    showCursor();
}

void WinmiddleCursorEffect::showCursor()
{
    m_failsafe.stop();
    m_callerWatcher.setWatchedServices({});
    if (m_hidden) {
        effects->showCursor();
        m_hidden = false;
    }
}

} // namespace KWin

#include "moc_winmiddlecursor.cpp"
