#!/usr/bin/env bash
# Remove a from-source (user-local) install. Packaged installs: pacman -R winmiddle
set -euo pipefail

SITE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/winmiddle"
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
KWIN_SCRIPT_DST="${XDG_DATA_HOME:-$HOME/.local/share}/kwin/scripts/winmiddle-focus"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"

log() { printf '==> %s\n' "$*"; }

log "Stopping winmiddle"
systemctl --user disable --now winmiddle.service 2>/dev/null || true
rm -f "$UNIT_DIR/winmiddle.service"
systemctl --user daemon-reload 2>/dev/null || true

log "Removing KWin script"
if command -v kwriteconfig6 >/dev/null; then
  kwriteconfig6 --file kwinrc --group Plugins --key winmiddle-focusEnabled false
  qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript winmiddle-focus 2>/dev/null || true
  qdbus6 org.kde.KWin /KWin reconfigure 2>/dev/null || true
fi
rm -rf "$KWIN_SCRIPT_DST"

KWIN_EFFECT_SO="/usr/lib/qt6/plugins/kwin/effects/plugins/winmiddlecursor.so"
if [[ -f "$KWIN_EFFECT_SO" ]] && ! pacman -Qqo "$KWIN_EFFECT_SO" >/dev/null 2>&1; then
  log "Removing KWin cursor effect"
  qdbus6 org.kde.KWin /Effects org.kde.kwin.Effects.unloadEffect winmiddlecursor 2>/dev/null || true
  sudo rm -f "$KWIN_EFFECT_SO" || log "Could not remove $KWIN_EFFECT_SO"
fi

log "Removing launcher + package + desktop entries"
rm -f "$BIN_DIR/winmiddle" "$BIN_DIR/winmiddle-ui"
rm -f "$APP_DIR/winmiddle-overlay.desktop" "$APP_DIR/winmiddle.desktop"
rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps/winmiddle.svg"
rm -rf "$SITE_DIR"

log "Re-enabling KDE primary selection (middle-click paste)"
if command -v kwriteconfig6 >/dev/null; then
  kwriteconfig6 --file kwinrc --group Wayland --key EnablePrimarySelection --type bool true
fi

cat <<EOF
Uninstalled from-source winmiddle.
Config kept at ~/.config/winmiddle/ (remove manually if desired).
Optional mouse/uinput udev rule:
  sudo rm -f /etc/udev/rules.d/99-winmiddle.rules
  sudo rm -f /etc/udev/rules.d/99-winmiddle-mouse.rules
  sudo udevadm control --reload-rules
Log out/in for KWin primary-selection change.
EOF
