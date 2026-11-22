#!/usr/bin/env bash
# Verify that the published image contains and can launch the actual LEOS
# first-session selector before spending time generating its installer ISO.
set -euo pipefail

if [[ "$#" -ne 1 || -z "$1" ]]; then
    echo "Usage: $0 <verified-image-reference>" >&2
    exit 2
fi

image_ref="$1"
if [[ ! "$image_ref" =~ ^[A-Za-z0-9./:_@-]+$ ]]; then
    echo "Invalid container image reference." >&2
    exit 2
fi

auth_file="${CONTAINERS_AUTH_FILE:-/root/.docker/config.json}"
if [[ ! -s "$auth_file" ]]; then
    echo "Container registry authentication is missing: $auth_file" >&2
    exit 1
fi

sudo podman pull --authfile "$auth_file" "$image_ref"

sudo podman run --rm --pull=never --network=none \
    --env QT_QPA_PLATFORM=offscreen \
    --env QT_QUICK_BACKEND=software \
    --entrypoint /usr/bin/bash \
    "$image_ref" -euc '
        set -euo pipefail

        autostart="/usr/etc/xdg/autostart/leos-session.desktop"
        wrapper="/usr/libexec/leos-session-selector"
        launcher="/usr/share/leos/launcher/main.py"
        selector_qml="/usr/share/leos/launcher/qml/ModeSelector.qml"

        for required in "$autostart" "$wrapper" "$launcher" "$selector_qml"; do
            if [[ ! -s "$required" ]]; then
                echo "Required LEOS first-session asset is missing: $required" >&2
                exit 1
            fi
        done

        # The first-run Desktop profile must be complete in the immutable image,
        # not merely present in the source tree.
        desktop_assets=(
            "/usr/share/leos/branding/wallpapers/desktop-leos.svg"
            "/usr/share/leos/branding/wallpapers/gaming-leos.svg"
            "/usr/share/plasma/desktoptheme/leos/metadata.json"
            "/usr/share/plasma/look-and-feel/org.leos.desktop/manifest.json"
            "/usr/share/plasma/look-and-feel/org.leos.desktop/contents/splash/Splash.qml"
            "/usr/share/icons/leos/index.theme"
            "/usr/share/aurorae/themes/leos/metadata.desktop"
            "/usr/share/aurorae/themes/leos/leosrc"
            "/usr/share/sddm/themes/leos/Main.qml"
            "/usr/share/sddm/themes/leos/theme.conf"
            "/usr/share/plymouth/themes/leos/leos.plymouth"
        )
        for required in "${desktop_assets[@]}"; do
            if [[ ! -s "$required" ]]; then
                echo "Required LEOS Desktop appearance asset is missing: $required" >&2
                exit 1
            fi
        done

        for executable in busctl plasma-apply-colorscheme plasma-apply-desktoptheme kreadconfig6 kwriteconfig6; do
            if ! command -v "$executable" >/dev/null 2>&1; then
                echo "Required KDE Desktop profile tool is missing: $executable" >&2
                exit 1
            fi
        done
        if ! command -v plasma-changeicons >/dev/null 2>&1 \
            && [[ ! -x /usr/libexec/plasma-changeicons ]] \
            && [[ ! -x /usr/lib64/libexec/plasma-changeicons ]]; then
            echo "Required KDE icon-theme tool is missing: plasma-changeicons" >&2
            exit 1
        fi

        export PYTHONPATH="/usr/share/leos${PYTHONPATH:+:$PYTHONPATH}"
        /usr/bin/python3 - <<PY
        from desktop.icon_theme import PlasmaIconThemeManager
        from desktop.kde_colors import KdeColorSchemeManager
        from desktop.plasma_style import PlasmaStyleManager
        from desktop.visual_chrome import PlasmaVisualChromeManager
        import shutil

        style = PlasmaStyleManager()
        icons = PlasmaIconThemeManager()
        colors = KdeColorSchemeManager()
        chrome = PlasmaVisualChromeManager()
        checks = {
            "busctl": shutil.which("busctl") is not None,
            "Plasma color-scheme tool": colors.tool_available(),
            "LEOS Plasma Style": style.tool_available() and style.style_installed("leos"),
            "LEOS icon theme": icons.tool_available() and icons.theme_installed("leos"),
            "LEOS splash theme": chrome.tool_available() and chrome.splash_theme_installed("org.leos.desktop"),
            "LEOS Aurorae window decoration": chrome.aurorae_theme_installed("leos"),
        }
        for name, available in checks.items():
            status = "OK" if available else "MISSING"
            print(f"Desktop profile prerequisite: {name}: {status}")
        missing = [name for name, available in checks.items() if not available]
        if missing:
            raise SystemExit("Desktop profile prerequisites are missing: " + ", ".join(missing))
        PY

        expected_exec="Exec=/usr/bin/bash /usr/libexec/leos-session-selector"
        if ! grep -Fxq "$expected_exec" "$autostart"; then
            echo "The system XDG autostart entry does not invoke the diagnostic selector wrapper." >&2
            cat "$autostart" >&2
            exit 1
        fi

        if ! grep -Fq "/usr/share/leos/launcher/main.py" "$wrapper"; then
            echo "The diagnostic selector wrapper does not point to the packaged launcher." >&2
            exit 1
        fi

        /usr/bin/bash -n "$wrapper"
        /usr/bin/python3 -c "from PySide6.QtGui import QGuiApplication; from PySide6.QtQml import QQmlApplicationEngine"

        umask 077
        test_home="$(/usr/bin/mktemp -d /tmp/leos-first-session-home.XXXXXX)"
        runtime_dir="$(/usr/bin/mktemp -d /tmp/leos-first-session-runtime.XXXXXX)"
        chmod 700 "$test_home" "$runtime_dir"
        export HOME="$test_home"
        export XDG_STATE_HOME="$test_home/.local/state"
        export XDG_CONFIG_HOME="$test_home/.config"
        export XDG_CACHE_HOME="$test_home/.cache"
        export XDG_RUNTIME_DIR="$runtime_dir"
        mkdir -p "$XDG_STATE_HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME"
        chmod 700 "$XDG_STATE_HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME"

        log_file="$XDG_STATE_HOME/leos/session-selector.log"
        set +e
        /usr/bin/timeout --signal=TERM --kill-after=5s 30s \
            /usr/bin/bash "$wrapper"
        selector_status=$?
        set -e

        if [[ -s "$log_file" ]]; then
            cat "$log_file"
        else
            echo "The selector did not create its diagnostic log." >&2
            exit 1
        fi

        # A successful GUI startup remains in its Qt event loop until timeout
        # terminates it. Early exit (including QML load failure) is a failure.
        if [[ "$selector_status" -ne 124 ]]; then
            echo "The LEOS selector exited before remaining in its GUI event loop (status: $selector_status)." >&2
            exit 1
        fi

        if ! grep -Fq "LEOS mode selector QML loaded successfully" "$log_file"; then
            echo "The LEOS selector did not confirm that its QML window loaded." >&2
            exit 1
        fi

        echo "LEOS first-session selector QML smoke test passed."

        gaming_log="$XDG_STATE_HOME/leos/gaming-smoke.log"
        set +e
        /usr/bin/timeout --signal=TERM --kill-after=5s 60s \
            /usr/bin/python3 /usr/share/leos/gaming/main.py > "$gaming_log" 2>&1
        gaming_status=$?
        set -e

        if [[ -s "$gaming_log" ]]; then
            cat "$gaming_log"
        else
            echo "The Gaming application did not produce startup diagnostics." >&2
            exit 1
        fi

        if [[ "$gaming_status" -ne 124 ]]; then
            echo "The LEOS Gaming interface exited before remaining in its Qt event loop (status: $gaming_status)." >&2
            exit 1
        fi

        if ! grep -Fq "LEOS Gaming QML loaded successfully" "$gaming_log"; then
            echo "The LEOS Gaming interface did not confirm that its QML window loaded." >&2
            exit 1
        fi

        echo "LEOS first-session and Gaming QML smoke tests passed."
    '
