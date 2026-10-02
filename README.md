# winmiddle

> **AI disclaimer:** This project was fully AI-generated under the guidance of a veteran developer with 25 years of tech experience — but it *was* generated fully by AI.

**Windows-faithful middle-click autoscroll for Linux** — hold-to-scroll by default, with optional Windows click-to-toggle and modifier gates.

Primary target: **KDE Plasma (Wayland) on Arch-based distros** (Arch, CachyOS, EndeavourOS, …). The daemon can run elsewhere; overlay placement and per-app filters work best with the bundled KWin script.

## Install

### Arch: build the package straight from GitHub (recommended while the AUR is down)

The AUR is currently unavailable, so `paru`/`yay` can't fetch the packages. The same PKGBUILDs live in this repo; download one and let `makepkg` build and install it — no clone needed:

```bash
mkdir -p /tmp/winmiddle-pkg && cd /tmp/winmiddle-pkg
curl -fL --remote-name-all \
  https://raw.githubusercontent.com/eslachance/winmiddle/main/packaging/aur/winmiddle/PKGBUILD \
  https://raw.githubusercontent.com/eslachance/winmiddle/main/packaging/aur/winmiddle/winmiddle.install
makepkg -si
```

To track git `main` instead of the latest release, use the `winmiddle-git` PKGBUILD:

```bash
mkdir -p /tmp/winmiddle-git-pkg && cd /tmp/winmiddle-git-pkg
curl -fL --remote-name-all \
  https://raw.githubusercontent.com/eslachance/winmiddle/main/packaging/aur/winmiddle-git/PKGBUILD \
  https://raw.githubusercontent.com/eslachance/winmiddle/main/packaging/aur/winmiddle-git/winmiddle.install
makepkg -si
```

These produce the exact packages the AUR ships (`winmiddle` / `winmiddle-git`), so once the AUR is back, `paru -S winmiddle` (or `winmiddle-git`) takes over updates seamlessly. Until then, rerun the commands above to update.

That installs both the daemon (`winmiddle`) and the settings GUI (`winmiddle-ui`, also in the app launcher as **winmiddle**).

Then finish session setup once:

```bash
winmiddle --setup
# or open the GUI and use Setup there:
winmiddle-ui
```

Log out and back in once (KWin only reapplies primary-selection on session start).

### AUR

When the AUR is reachable:

```bash
# Release package
paru -S winmiddle
# or: yay -S winmiddle

# Tracking git main
paru -S winmiddle-git
```

### From source (any distro, user-local)

No clone required — grab the `main` tarball and run the installer from it:

```bash
curl -fL https://github.com/eslachance/winmiddle/archive/refs/heads/main.tar.gz | tar xz -C /tmp
/tmp/winmiddle-main/install.sh
```

Or from a checkout:

```bash
git clone https://github.com/eslachance/winmiddle.git
cd winmiddle
./install.sh
```

`install.sh` installs `winmiddle`, `winmiddle-ui`, the desktop entry, and the icon under `~/.local`, then runs `winmiddle --setup`. The extracted folder can be deleted afterwards.

Uninstall from-source installs with `./uninstall.sh` (from the tarball folder or checkout). Packaged installs: `sudo pacman -R winmiddle` (or `winmiddle-git`).

## Settings UI

```bash
winmiddle-ui
# or: winmiddle --ui
```

Opens a Plasma-friendly PyQt6 app (also in the app launcher as **winmiddle**) to:

- Start / stop / restart the user daemon and enable it at login
- Configure activation, scroll speed, app lists, and mouse device
- Re-run setup steps (paste-kill, KWin script, mouse udev)

Closing the window keeps a system-tray icon; use **Quit** from the tray menu to exit the UI. The daemon keeps running as a systemd user service.

## Activation (config)

Prefer the settings UI above. The same options live in `~/.config/winmiddle/config.toml`:

```toml
[activation]
hold = true              # hold middle + move → scroll; release → stop; tap → native middle-click
toggle = false           # Windows click-to-toggle (click enter, click exit)
modifier = "none"        # none | ctrl | alt | shift | super
modifier_for = "both"    # which gestures need the modifier: toggle | hold | both
```

Examples:
- **Default (recommended):** hold only — tap closes tabs; hold+move scrolls.
- **Classic Windows:** `hold = false`, `toggle = true`
- **Ctrl+middle hold to scroll:** `hold = true`, `modifier = "ctrl"`, `modifier_for = "hold"`

## Architecture

```
Physical mouse ──grab──► winmiddled ──uinput──► virtual mouse ──► KWin/apps
                              │
                              ├─ hold+move → HOLD_AUTOSCROLL (default)
                              ├─ tap (toggle on) → AUTOSCROLL + overlay
                              ├─ drag when hold gated off → middle-drag passthrough
                              └─ browsers (hold): tap = native middle; hold = scroll

KWin script ──DBus──► focus + cursor position (for overlay + app filters)
Paste-kill: KDE EnablePrimarySelection=false, GTK, Firefox prefs, Chrome flag
```

## Status / tuning

```bash
winmiddle-ui
systemctl --user status winmiddle
journalctl --user -u winmiddle -f
winmiddle --list-devices
```

Config: `~/.config/winmiddle/config.toml` (also edited by the settings UI)

```toml
[scroll]
drag_threshold_px = 50  # held move beyond this → hold-scroll (or Blender-style drag if hold off)
deadzone_px = 12
lock_cursor = true      # pin the real cursor while scrolling (see below)

[apps]
native_middle = ["firefox", "google-chrome", ...]  # tap=native; hold=scroll
passthrough = ["steam_app", "blender", ...]        # never intercept
require_scrollable = true                          # AT-SPI gate (skipped for native_middle)
```

### Cursor lock

While autoscrolling, the real cursor stays pinned where scrolling started, so the
pane under it keeps receiving the wheel. Without the lock, drifting onto Discord's
chat box or a menu used to stop or redirect the scroll. A ghost copy of your
themed pointer follows the mouse instead. On release, the real cursor jumps to
where you brought the ghost. The jump uses a small absolute uinput device
(`winmiddle warp pointer`), so pointer acceleration can't make it miss. Set
`lock_cursor = false` (or untick it in the UI) to get the old free-moving cursor.

Only KWin can hide the real cursor, so the pinned one stays visible next to the ghost
unless the small bundled KWin effect `winmiddlecursor` (`kwin-effect/`) is installed.
The AUR packages and `install.sh` build and install it. KWin only loads it if it was
built for the exact running KWin version. After a KWin upgrade, rebuild (reinstall
the AUR package or rerun `./install.sh`); until then the cursor is simply visible again.
Manual build:

```bash
cmake -S kwin-effect -B kwin-effect/build -DCMAKE_INSTALL_PREFIX=/usr
cmake --build kwin-effect/build && sudo cmake --install kwin-effect/build
```

## Requirements

- Python 3.11+ with `python-evdev` and `python-pyqt6`
- `layer-shell-qt` (origin glyph on Wayland)
- Permission to read your mouse + `/dev/uinput` (`winmiddle --setup` installs a generic `ID_INPUT_MOUSE` + uinput `uaccess`/`seat` rule so hot-plugged mice work without re-pinning VID/PID)
- KDE Plasma recommended (ships a KWin script for focus/cursor). Other DEs: daemon still autoscrolls, but overlay placement / per-app filters degrade without a focus provider.

Optional: `python-gobject` + `at-spi2-core` for scrollable-under-cursor probing.

## Honest limits

- **True** Windows link/tab hit-testing only exists inside apps. With hold mode, browser taps synthesize a real middle-click (close tab / open link); hold+move uses winmiddle scroll (Chromium’s own Wayland autoscroll is unreliable after tab switches).
- AT-SPI “scrollable” is best-effort and is skipped for `native_middle` apps; some UI (tabs, custom widgets) may still need the hold/tap split.
- Fullscreen games should stay on the passthrough list so camera-orbit binds keep working.

## Releasing a new version

Maintainers only. Goal: ship a tagged GitHub release **and** update both AUR packages so `paru -S winmiddle` gets the daemon **and** the settings GUI.

### What must ship with the GUI

An install is incomplete unless all of these are present:

| Piece | Where |
|---|---|
| CLI entry `winmiddle-ui` | `pyproject.toml` → `[project.scripts]` (`winmiddle.ui.app:main`) |
| UI package | `winmiddle/ui/` (included by hatch `packages = ["winmiddle"]`) |
| App launcher | `share/winmiddle.desktop` (`Exec=winmiddle-ui`, `Icon=winmiddle`) |
| Icon | `share/icons/hicolor/scalable/apps/winmiddle.svg` |
| Data install | `packaging/install-data.sh` copies desktop + icon into `/usr/share/...` |
| From-source | `install.sh` writes `~/.local/bin/winmiddle-ui` + desktop/icon |

Before tagging, sanity-check locally:

```bash
# After a DESTDIR-style / AUR-like install, or from source:
command -v winmiddle-ui
winmiddle-ui --help   # or just launch it
test -f /usr/share/applications/winmiddle.desktop \
  -o -f ~/.local/share/applications/winmiddle.desktop
```

### 1. Bump version in the repo

Pick the next semver (example: `0.2.0`). Update **both**:

- `pyproject.toml` → `version = "0.2.0"`
- `winmiddle/__init__.py` → `__version__ = "0.2.0"`
- `packaging/aur/winmiddle/PKGBUILD` → `pkgver=0.2.0` (and reset `pkgrel=1`)

Commit and push to `main` on GitHub (`eslachance/winscroll`).

### 2. Tag + GitHub Release

```bash
git tag -a v0.2.0 -m "winmiddle 0.2.0"
git push origin main --tags
gh release create v0.2.0 --title "winmiddle 0.2.0" --notes-file - <<'EOF'
- …
EOF
```

Confirm the source tarball exists:

`https://github.com/eslachance/winscroll/archive/refs/tags/v0.2.0.tar.gz`

(extracts as `winscroll-0.2.0/`).

### 3. Update AUR `winmiddle` (versioned)

```bash
# once per machine
# ~/.ssh/config → Host aur.archlinux.org / User aur / IdentityFile ~/.ssh/aur

git clone ssh://aur@aur.archlinux.org/winmiddle.git
cd winmiddle
# copy from this repo (or edit in place):
#   PKGBUILD, winmiddle.install, .SRCINFO

# set pkgver to the new version, then:
updpkgsums
makepkg --printsrcinfo > .SRCINFO

# optional local build smoke-test:
# makepkg -si

git checkout -B master
git add PKGBUILD winmiddle.install .SRCINFO
git commit -m "Update to 0.2.0"
git push origin master
```

Also copy the updated `PKGBUILD` / `.SRCINFO` / `winmiddle.install` back into `packaging/aur/winmiddle/` in this repo so they stay in sync.

### 4. Update AUR `winmiddle-git` (tracks main)

Usually only needed when packaging metadata changes (depends, install script, desktop files). The `pkgver()` function picks the version from git tags automatically.

```bash
git clone ssh://aur@aur.archlinux.org/winmiddle-git.git
cd winmiddle-git
# sync PKGBUILD / winmiddle.install from packaging/aur/winmiddle-git/
makepkg --printsrcinfo > .SRCINFO
git checkout -B master
git add PKGBUILD winmiddle.install .SRCINFO
git commit -m "Update packaging"
git push origin master
```

Testers on `-git` rebuild with `paru -S winmiddle-git` (or `--rebuild`).

### 5. Verify the install includes the GUI

```bash
paru -S winmiddle          # or winmiddle-git
pacman -Ql winmiddle | grep -E 'winmiddle-ui|applications/winmiddle.desktop|icons/.*/winmiddle'
winmiddle-ui
```

Expected: `/usr/bin/winmiddle-ui`, `/usr/share/applications/winmiddle.desktop`, icon under `/usr/share/icons/...`, and the app appears in the Plasma launcher.

### One-time AUR SSH setup

```bash
ssh-keygen -t ed25519 -f ~/.ssh/aur -C "aur"
# paste ~/.ssh/aur.pub into https://aur.archlinux.org → My Account → SSH Public Key

cat >> ~/.ssh/config <<'EOF'
Host aur.archlinux.org
  User aur
  IdentityFile ~/.ssh/aur
  IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config
ssh -T aur@aur.archlinux.org   # expect: Welcome to AUR, <user>!
```

## License

MIT
