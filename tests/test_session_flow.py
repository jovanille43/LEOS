"""Tests for the LEOS startup and mode-selection contract."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SessionFlowTests(unittest.TestCase):
    def test_mode_selector_uses_jpeg_branding_sources_and_graceful_fallback(self):
        source = (ROOT / "launcher/qml/ModeSelector.qml").read_text(encoding="utf-8")
        self.assertIn("source: leosTheme.desktopLogoUrl", source)
        self.assertIn("source: leosTheme.gamingLogoUrl", source)
        assets = (ROOT / "desktop/branding_assets.py").read_text(encoding="utf-8")
        self.assertIn('"desktop-logo.jpeg"', assets)
        self.assertIn('"gaming-logo.jpeg"', assets)
        self.assertIn("desktop-logo.png", assets)
        self.assertIn("gaming-logo.png", assets)
        self.assertIn("visible: status === Image.Ready", source)
        self.assertEqual(source.count("asynchronous: true"), 2)
        self.assertEqual(source.count("smooth: true"), 2)

    def test_gaming_header_uses_official_gaming_emblem_with_text_fallback(self):
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("source: leosTheme.gamingLogoUrl", qml)
        self.assertIn("gaming-logo.jpeg", (ROOT / "desktop/branding_assets.py").read_text(encoding="utf-8"))
        self.assertIn("asynchronous: true", qml)
        self.assertIn("visible: gamingHeaderLogo.status !== Image.Ready", qml)

    def test_mode_selector_plays_the_mode_specific_intro_with_fallback(self):
        qml = (ROOT / "launcher/qml/ModeSelector.qml").read_text(encoding="utf-8")
        controller = (ROOT / "launcher/controller.py").read_text(encoding="utf-8")
        self.assertIn("import QtMultimedia", qml)
        self.assertIn("leosTheme.gamingIntroUrl", qml)
        self.assertIn("leosTheme.desktopIntroUrl", qml)
        branding = (ROOT / "desktop/branding_assets.py").read_text(encoding="utf-8")
        self.assertIn('"gaming-intro.mp4"', branding)
        self.assertIn('"desktop-intro.mov"', branding)
        self.assertIn("source_asset_urls", branding)
        self.assertIn("MediaPlayer.EndOfMedia", qml)
        self.assertIn("MediaPlayer.InvalidMedia", qml)
        self.assertIn("onErrorOccurred", qml)
        self.assertIn("interval: 9000", qml)
        self.assertIn("introAudioOutput.muted = !modeSelectorController.soundsEnabled", qml)
        self.assertIn("def animationsEnabled(self)", controller)
        self.assertIn("def soundsEnabled(self)", controller)
        self.assertIn("window.requestModeWithIntro(\"gaming\")", qml)
        self.assertIn("window.requestModeWithIntro(\"desktop\")", qml)

    def test_selector_ignores_keyboard_input_during_mode_intro(self):
        qml = (ROOT / "launcher/qml/ModeSelector.qml").read_text(encoding="utf-8")
        start = qml.index("Keys.onPressed: function(event)")
        end = qml.index("\n    }", start)
        handler = qml[start:end]
        self.assertIn("if (window.transitionInProgress)", handler)
        self.assertIn("event.accepted = true", handler)
        self.assertLess(
            handler.index("if (window.transitionInProgress)"),
            handler.index("if (event.key === Qt.Key_G)"),
        )

    def test_desktop_wallpaper_is_valid_4k_svg_and_reuses_the_official_emblem(self):
        import xml.etree.ElementTree as ET

        wallpaper = ROOT / "branding/wallpapers/desktop-leos.svg"
        self.assertTrue(wallpaper.is_file())
        root = ET.parse(wallpaper).getroot()
        self.assertEqual(root.attrib.get("viewBox"), "0 0 3840 2160")
        image = root.find("{http://www.w3.org/2000/svg}image")
        self.assertIsNotNone(image)
        self.assertEqual(image.attrib.get("href"), "../desktop-logo.jpeg")
        self.assertEqual(
            image.attrib.get("{http://www.w3.org/1999/xlink}href"),
            "../desktop-logo.jpeg",
        )
        self.assertTrue((wallpaper.parent.parent / "desktop-logo.jpeg").is_file())

    def test_gaming_wallpaper_is_valid_4k_svg_and_reuses_the_official_emblem(self):
        import xml.etree.ElementTree as ET

        wallpaper = ROOT / "branding/wallpapers/gaming-leos.svg"
        self.assertTrue(wallpaper.is_file())
        root = ET.parse(wallpaper).getroot()
        self.assertEqual(root.attrib.get("viewBox"), "0 0 3840 2160")
        image = root.find("{http://www.w3.org/2000/svg}image")
        self.assertIsNotNone(image)
        self.assertEqual(image.attrib.get("href"), "../gaming-logo.jpeg")
        self.assertEqual(
            image.attrib.get("{http://www.w3.org/1999/xlink}href"),
            "../gaming-logo.jpeg",
        )
        self.assertTrue((wallpaper.parent.parent / "gaming-logo.jpeg").is_file())
    def test_branding_animation_files_exist_at_runtime_paths(self):
        branding = ROOT / "branding"
        self.assertTrue((branding / "desktop-logo.jpeg").is_file())
        self.assertTrue((branding / "gaming-logo.jpeg").is_file())
        self.assertTrue((branding / "animations" / "desktop-intro.mov").is_file())
        self.assertTrue((branding / "animations" / "gaming-intro.mp4").is_file())
        self.assertTrue((branding / "animations" / "gaming-roar-reference.mp4").is_file())

    def test_desktop_intro_uses_mov_extension_in_both_transitions(self):
        selector = (ROOT / "launcher" / "qml" / "ModeSelector.qml").read_text(encoding="utf-8")
        gaming = (ROOT / "gaming" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("leosTheme.desktopIntroUrl", selector)
        self.assertIn("leosTheme.desktopIntroUrl", gaming)
        branding = (ROOT / "desktop/branding_assets.py").read_text(encoding="utf-8")
        self.assertIn('"desktop-intro.mov"', branding)
        self.assertNotIn("desktop-intro.mp4", branding)

    def test_gaming_return_finishes_on_invalid_media_and_timeout(self):
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("MediaPlayer.InvalidMedia", qml)
        self.assertIn("onErrorOccurred", qml)
        self.assertIn("interval: 9000", qml)
        self.assertIn("onTriggered: window.finishDesktopReturn()", qml)
        self.assertIn("if (returningToDesktop)", qml)
        self.assertIn("returningToDesktop = true", qml)

    def test_gaming_window_routes_keyboard_events_through_focused_content(self):
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        self.assertIn("id: gamingContent", qml)
        self.assertIn("focus: true", qml)
        self.assertIn("Keys.onPressed: function(event)", qml)
        self.assertIn('window.handleGamepadAction("confirm")', qml)
        window_header = qml.split("ApplicationWindow {", 1)[1].split("id: gamingContent", 1)[0]
        self.assertNotIn("focus: true", window_header)

    def test_gaming_return_plays_desktop_intro_before_closing(self):
        qml = (ROOT / "gaming/qml/Main.qml").read_text(encoding="utf-8")
        controller = (ROOT / "gaming/backend/controller.py").read_text(encoding="utf-8")
        self.assertIn("import QtMultimedia", qml)
        self.assertIn("leosTheme.desktopIntroUrl", qml)
        self.assertIn("desktop-intro.mov", (ROOT / "desktop/branding_assets.py").read_text(encoding="utf-8"))
        self.assertIn("function requestDesktopReturn()", qml)
        self.assertIn("function finishDesktopReturn()", qml)
        self.assertIn("window.requestDesktopReturn()", qml)
        self.assertIn("MediaPlayer.EndOfMedia", qml)
        self.assertIn("onErrorOccurred", qml)
        self.assertIn("desktopIntroAudio.muted = !leos.soundsEnabled", qml)
        self.assertIn("def animationsEnabled(self)", controller)
        self.assertIn("def soundsEnabled(self)", controller)

    def test_kde_autostart_opens_the_mode_selector(self):
        entry = (ROOT / "desktop" / "autostart" / "leos-session.desktop").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "Exec=/usr/bin/python3 /usr/share/leos/launcher/main.py --select",
            entry,
        )

    def test_mode_selector_routes_keyboard_events_through_focused_content(self):
        qml = (ROOT / "launcher/qml/ModeSelector.qml").read_text(encoding="utf-8")
        self.assertIn("id: modeSelectorContent", qml)
        self.assertIn("focus: true", qml)
        self.assertIn("modeSelectorContent", qml)
        self.assertIn("Keys.onPressed: function(event)", qml)
        self.assertNotIn("    focus: true", qml.split("ApplicationWindow {", 1)[1].split("id: modeSelectorContent", 1)[0])

    def test_selector_shows_clock_date_and_remembered_mode(self):
        qml = (ROOT / "launcher" / "qml" / "ModeSelector.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("property date currentDate: new Date()", qml)
        self.assertIn('toLocaleTimeString(Qt.locale("fr_FR"), "HH:mm")', qml)
        self.assertIn('toLocaleDateString(Qt.locale("fr_FR"), "dddd d MMMM yyyy")', qml)
        self.assertIn("modeManager.lastMode", qml)
        self.assertIn("LEOS DESKTOP", qml)
        self.assertIn("LEOS GAMING", qml)

    def test_official_mode_emblems_have_separate_paths(self):
        qml = (ROOT / "launcher" / "qml" / "ModeSelector.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("source: leosTheme.desktopLogoUrl", qml)
        self.assertIn("source: leosTheme.gamingLogoUrl", qml)
        assets = (ROOT / "desktop/branding_assets.py").read_text(encoding="utf-8")
        self.assertIn('"desktop-logo.jpeg"', assets)
        self.assertIn('"gaming-logo.jpeg"', assets)

    def test_selector_accepts_read_only_controller_navigation(self):
        root = ROOT
        controller = (root / "launcher" / "controller.py").read_text(encoding="utf-8")
        main = (root / "launcher" / "main.py").read_text(encoding="utf-8")
        qml = (root / "launcher" / "qml" / "ModeSelector.qml").read_text(encoding="utf-8")
        self.assertIn("GamepadBackend()", controller)
        self.assertIn("mapper_from_preferences", controller)
        self.assertIn('setContextProperty("modeSelectorController", selector_controller)', main)
        self.assertIn("function onGamepadAction(action)", qml)
        self.assertIn("window.handleGamepadAction(action)", qml)

    def test_failed_gaming_qml_startup_releases_controller_resources(self):
        main = (ROOT / "gaming" / "main.py").read_text(encoding="utf-8")
        controller = (ROOT / "gaming" / "backend" / "controller.py").read_text(encoding="utf-8")
        self.assertLess(
            main.index("if not engine.rootObjects():"),
            main.index("controller.shutdown()"),
        )
        self.assertIn("self.monitor.stop()", controller)
        self.assertIn("self._gamepad_poll_timer.stop()", controller)
        self.assertIn("self._gamepad_refresh_timer.stop()", controller)
        self.assertIn("self._gamepad.close()", controller)

    def test_mode_selector_documentation_matches_integrated_assets_and_transitions(self):
        readme = (ROOT / "components/mode-selector/README.md").read_text(encoding="utf-8")
        design = (ROOT / "components/mode-selector/DESIGN.md").read_text(encoding="utf-8")
        for content in (readme, design):
            self.assertIn("desktop-intro.mov", content)
            self.assertIn("gaming-intro.mp4", content)
            self.assertIn("gaming-roar-reference.mp4", content)
            self.assertIn("applications ouvertes", content)
            self.assertIn("arrière-plan", content)
        self.assertNotIn("ne sont pas encore présents dans le dépôt", readme)
        self.assertNotIn("seront ajoutés dans", readme)

    def test_mode_choice_does_not_add_automatic_application_closing(self):
        qml = (ROOT / "launcher" / "qml" / "ModeSelector.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("resteront en arrière-plan", qml)
        self.assertNotIn("killall", qml)
        self.assertNotIn("pkill", qml)

    def test_entering_and_leaving_gaming_requires_confirmation(self):
        selector = (ROOT / "launcher" / "qml" / "ModeSelector.qml").read_text(
            encoding="utf-8"
        )
        gaming = (ROOT / "gaming" / "qml" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn('onClicked: transitionDialog.open()', selector)
        self.assertIn('window.requestModeWithIntro("gaming")', selector)
        self.assertIn('id: returnDialog', gaming)
        self.assertIn('title: "Retourner à Desktop Mode ?"', gaming)
        self.assertIn('returnDialog.open()', gaming)
        self.assertIn('window.requestDesktopReturn()', gaming)
        self.assertIn('text: "CONFIRMER LE RETOUR AU DESKTOP"', gaming)

    def test_gaming_mode_is_not_remembered_before_qml_load(self):
        main = (ROOT / "gaming" / "main.py").read_text(encoding="utf-8")
        controller = (ROOT / "gaming" / "backend" / "controller.py").read_text(encoding="utf-8")
        self.assertLess(
            main.index("if not engine.rootObjects():"),
            main.index('controller.settings.set("last_mode", "gaming")'),
        )
        self.assertNotIn('self.settings.set("last_mode", "gaming")', controller)


    def test_mode_selector_tries_later_controllers_when_first_open_fails(self):
        controller = (ROOT / "launcher" / "controller.py").read_text(encoding="utf-8")
        gamepad = (ROOT / "gaming" / "backend" / "gamepad.py").read_text(encoding="utf-8")
        self.assertIn("open_first_available_gamepad", controller)
        self.assertIn(
            "device, _open_error = open_first_available_gamepad(self._backend, devices)",
            controller,
        )
        self.assertIn("if device is None:", controller)
        self.assertNotIn("device = devices[0]", controller)
        self.assertIn("except (OSError, ValueError, RuntimeError)", gamepad)


if __name__ == "__main__":
    unittest.main()
