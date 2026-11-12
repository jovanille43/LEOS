"""Generate guarded Plasma scripting commands for the LEOS dock.

The returned JavaScript is executed only by the explicit Control Center action
after a private backup and user confirmation. It supports only a single panel
and never deletes panels or alters multi-panel layouts.
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
    var versionMajor = parseInt(String(applicationVersion).split(".")[0], 10);
    if (!versionMajor || versionMajor < 6) {
        throw new Error("Cet adaptateur exige Plasma 6 ou une version ultérieure.");
    }

    var desired = __LEOS_CONFIG__;
    var widgetTypes = __LEOS_WIDGETS__;
    var markerGroup = "LEOS";
    var markerValue = "leos-panel-v1";
    var allPanels = panels();
    var existing = [];

    function isLeosPanel(candidate) {
        candidate.currentConfigGroup = [markerGroup];
        return candidate.readConfig("managedBy", "") === markerValue;
    }

    for (var i = 0; i < allPanels.length; i++) {
        if (isLeosPanel(allPanels[i])) {
            existing.push(allPanels[i]);
        }
    }

    if (existing.length > 1) {
        throw new Error("Plusieurs panneaux LEOS sont marqués ; intervention manuelle requise.");
    }
    if (allPanels.length > 1) {
        throw new Error("Plusieurs panneaux KDE sont présents. LEOS refuse de modifier une disposition multi-panneaux.");
    }
    if (!desired.enabled) {
        throw new Error("Le dock LEOS est désactivé dans les préférences ; aucun panneau ne sera supprimé.");
    }
    if (desired.widgetsEnabled) {
        throw new Error("L'activation des widgets du bureau n'est pas encore prise en charge par cet adaptateur.");
    }

    var panel = existing.length === 1 ? existing[0] : null;
    var created = false;
    var adopted = false;
    var before = null;
    var addedWidgets = [];
    var widgetsToAdd = [];

    if (panel) {
        panel.currentConfigGroup = [markerGroup];
        before = {
            location: panel.location,
            alignment: panel.alignment,
            hiding: panel.hiding,
            height: panel.height,
            lengthMode: panel.lengthMode,
            length: panel.length,
            managedBy: panel.readConfig("managedBy", "")
        };
    } else if (allPanels.length === 1) {
        panel = allPanels[0];
        adopted = true;
        panel.currentConfigGroup = [markerGroup];
        before = {
            location: panel.location,
            alignment: panel.alignment,
            hiding: panel.hiding,
            height: panel.height,
            lengthMode: panel.lengthMode,
            length: panel.length,
            managedBy: panel.readConfig("managedBy", "")
        };
        // Keep all existing applets. Add only missing core dock components.
        var essentialWidgets = [
            "org.kde.plasma.icontasks",
            "org.kde.plasma.systemtray",
            "org.kde.plasma.digitalclock"
        ];
        for (var e = 0; e < essentialWidgets.length; e++) {
            if (knownWidgetTypes.indexOf(essentialWidgets[e]) !== -1
                    && panel.widgets(essentialWidgets[e]).length === 0) {
                widgetsToAdd.push(essentialWidgets[e]);
            }
        }
    } else if (allPanels.length === 0) {
        var availableTypes = knownWidgetTypes;
        for (var a = 0; a < widgetTypes.length; a++) {
            if (availableTypes.indexOf(widgetTypes[a]) !== -1) {
                widgetsToAdd.push(widgetTypes[a]);
            }
        }
        if (widgetsToAdd.length < 2) {
            throw new Error("Pas assez de widgets KDE sont disponibles pour créer le dock LEOS.");
        }
    }

    try {
        if (!panel) {
            panel = new Panel();
            if (!panel) {
                throw new Error("KDE n'a pas pu créer un panneau Plasma.");
            }
            created = true;
        }

        for (var w = 0; w < widgetsToAdd.length; w++) {
            var added = panel.addWidget(widgetsToAdd[w]);
            if (!added) {
                throw new Error("Échec de l'ajout du widget " + widgetsToAdd[w]);
            }
            addedWidgets.push(added);
        }

        panel.location = desired.position;
        panel.alignment = desired.alignment;
        panel.hiding = desired.autoHide ? "autohide" : "none";
        panel.height = 56;
        panel.lengthMode = "fit";

        panel.currentConfigGroup = [markerGroup];
        panel.writeConfig("managedBy", markerValue);
        panel.writeConfig("schemaVersion", 1);

        if (adopted) {
            print("LEOS_PANEL_ADOPTED=" + panel.id);
        } else if (created) {
            print("LEOS_PANEL_CREATED=" + panel.id);
        } else {
            print("LEOS_PANEL_UPDATED=" + panel.id);
        }
    } catch (error) {
        try {
            if (created && panel) {
                // This exact panel was created by this transaction.
                panel.remove();
                print("LEOS_PARTIAL_PANEL_ROLLED_BACK=1");
            } else if (panel && before) {
                for (var r = 0; r < addedWidgets.length; r++) {
                    addedWidgets[r].remove();
                }
                panel.location = before.location;
                panel.alignment = before.alignment;
                panel.hiding = before.hiding;
                panel.height = before.height;
                panel.lengthMode = before.lengthMode;
                panel.length = before.length;
                panel.currentConfigGroup = [markerGroup];
                panel.writeConfig("managedBy", before.managedBy);
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
        "can_remove_leos_owned_dock": False,
        "touches_unmanaged_panels": True,
        "adopts_single_unmanaged_panel_with_backup": True,
        "desktop_widgets_applied": False,
        "runtime_validated_on_bazzite": False,
        "requires_backup_and_explicit_confirmation": True,
    }
