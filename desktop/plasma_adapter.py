"""Generate safe Plasma scripting commands for LEOS-owned panels.

The returned JavaScript is not executed by this module. It uses KDE's
documented Plasma scripting API and only updates panels carrying the
LEOS-specific ownership marker. Existing user panels and their applets are
never adopted, moved, or removed.
"""
from __future__ import annotations

import json
from typing import Any

from desktop.layouts import validate_layout

LEOS_PANEL_MARKER = "leos-panel-v1"
LEOS_PANEL_CONFIG_GROUP = "LEOS"
PANEL_WIDGETS = (
    "org.kde.plasma.kickoff",
    "org.kde.plasma.icontasks",
    "org.kde.plasma.marginsseparator",
    "org.kde.plasma.systemtray",
    "org.kde.plasma.digitalclock",
    "org.kde.plasma.showdesktop",
)


def build_panel_management_script(layout: object) -> str:
    """Build a Plasma 6 JavaScript script; never execute it here."""
    if not validate_layout(layout):
        raise ValueError("Invalid LEOS desktop layout")
    assert isinstance(layout, dict)
    config: dict[str, Any] = {
        "enabled": layout["dock"]["enabled"],
        "position": layout["dock"]["position"],
        "alignment": layout["dock"]["alignment"],
        "autoHide": layout["dock"]["auto_hide"],
        "widgetsEnabled": layout["widgets_enabled"],
    }
    config_json = json.dumps(config, ensure_ascii=True, separators=(",", ":"))
    widgets_json = json.dumps(PANEL_WIDGETS, ensure_ascii=True)
    return _SCRIPT.replace("__LEOS_CONFIG__", config_json).replace("__LEOS_WIDGETS__", widgets_json)


_SCRIPT = r'''(function () {
    "use strict";
    var desired = __LEOS_CONFIG__;
    var widgetTypes = __LEOS_WIDGETS__;
    var markerGroup = "LEOS";
    var markerValue = "leos-panel-v1";
    var existing = [];
    var allPanels = panels();

    function isLeosPanel(panel) {
        panel.currentConfigGroup = [markerGroup];
        return panel.readConfig("managedBy", "") === markerValue;
    }

    for (var i = 0; i < allPanels.length; i++) {
        if (isLeosPanel(allPanels[i])) {
            existing.push(allPanels[i]);
        }
    }

    if (existing.length > 1) {
        throw new Error("Plusieurs panneaux LEOS sont marqués ; intervention manuelle requise.");
    }

    var panel = existing.length === 1 ? existing[0] : null;

    if (!desired.enabled) {
        if (panel) {
            panel.remove();
            print("LEOS_PANEL_REMOVED");
        } else {
            print("LEOS_PANEL_ALREADY_ABSENT");
        }
        return;
    }

    var created = false;
    var addedWidgets = [];
    var before = null;

    try {
        if (!panel) {
            panel = new Panel();
            if (!panel) {
                throw new Error("KDE n'a pas pu créer un panneau Plasma.");
            }
            created = true;
        } else {
            before = {
                location: panel.location,
                alignment: panel.alignment,
                hiding: panel.hiding,
                height: panel.height,
                lengthMode: panel.lengthMode,
                length: panel.length
            };
        }

        panel.location = desired.position;
        panel.alignment = desired.alignment;
        panel.hiding = desired.autoHide ? "autohide" : "none";
        panel.height = 52;
        panel.lengthMode = "fit";

        var currentTypes = [];
        var currentWidgets = panel.widgets();
        for (var w = 0; w < currentWidgets.length; w++) {
            currentTypes.push(currentWidgets[w].type);
        }

        var availableTypes = knownWidgetTypes;
        for (var a = 0; a < widgetTypes.length; a++) {
            var widgetType = widgetTypes[a];
            if (currentTypes.indexOf(widgetType) !== -1) {
                continue;
            }
            if (availableTypes.indexOf(widgetType) === -1) {
                print("LEOS_WIDGET_UNAVAILABLE=" + widgetType);
                continue;
            }
            var added = panel.addWidget(widgetType);
            if (!added) {
                throw new Error("Échec de l'ajout du widget " + widgetType);
            }
            addedWidgets.push(added);
        }

        if (created && addedWidgets.length < 2) {
            throw new Error("Pas assez de widgets KDE sont disponibles pour créer le dock LEOS.");
        }

        panel.currentConfigGroup = [markerGroup];
        panel.writeConfig("managedBy", markerValue);
        panel.writeConfig("schemaVersion", 1);

        if (desired.widgetsEnabled) {
            print("LEOS_DESKTOP_WIDGETS_PENDING=1");
        }
        print("LEOS_PANEL_APPLIED=" + panel.id);
    } catch (error) {
        try {
            if (created && panel) {
                panel.remove();
            } else if (panel && before) {
                for (var r = addedWidgets.length - 1; r >= 0; r--) {
                    addedWidgets[r].remove();
                }
                panel.location = before.location;
                panel.alignment = before.alignment;
                panel.hiding = before.hiding;
                panel.height = before.height;
                panel.lengthMode = before.lengthMode;
                panel.length = before.length;
            }
        } catch (rollbackError) {
            print("LEOS_ROLLBACK_WARNING=" + rollbackError);
        }
        throw error;
    }
})();'''


def adapter_capabilities() -> dict[str, Any]:
    """Describe implemented adapter scope without claiming runtime validation."""
    return {
        "plasma_api": "Plasma scripting API",
        "target_major_version": 6,
        "can_create_dock": True,
        "can_update_leos_owned_dock": True,
        "can_remove_leos_owned_dock": True,
        "touches_unmanaged_panels": False,
        "desktop_widgets_applied": False,
        "runtime_validated_on_bazzite": False,
        "requires_backup_and_explicit_confirmation": True,
    }
