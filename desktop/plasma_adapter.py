"""Generate guarded Plasma scripting commands for LEOS-owned panels.

The returned JavaScript is never executed by this module. It uses KDE's
documented Plasma 6 scripting API and only updates panels carrying the
LEOS-specific ownership marker. Existing user panels are never adopted,
moved, or removed.
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
    var existing = [];
    var allPanels = panels();

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

    var panel = existing.length === 1 ? existing[0] : null;

    if (!desired.enabled) {
        print("LEOS_PANEL_DISABLE_NOT_IMPLEMENTED=1");
        print("Le panneau KDE est conservé ; aucune suppression n'est effectuée.");
        return;
    }

    if (!panel && allPanels.length > 0) {
        throw new Error(
            "Un panneau KDE non géré existe déjà. LEOS refuse de créer un doublon ou de l'adopter automatiquement."
        );
    }

    var created = false;
    var before = null;
    var newPanelWidgets = [];

    if (panel) {
        before = {
            location: panel.location,
            alignment: panel.alignment,
            hiding: panel.hiding,
            height: panel.height,
            lengthMode: panel.lengthMode,
            length: panel.length
        };
    } else {
        var availableTypes = knownWidgetTypes;
        for (var a = 0; a < widgetTypes.length; a++) {
            if (availableTypes.indexOf(widgetTypes[a]) !== -1) {
                newPanelWidgets.push(widgetTypes[a]);
            }
        }
        if (newPanelWidgets.length < 2) {
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

        panel.location = desired.position;
        panel.alignment = desired.alignment;
        panel.hiding = desired.autoHide ? "autohide" : "none";
        panel.height = 52;
        panel.lengthMode = "fit";

        if (created) {
            for (var w = 0; w < newPanelWidgets.length; w++) {
                var added = panel.addWidget(newPanelWidgets[w]);
                if (!added) {
                    throw new Error("Échec de l'ajout du widget " + newPanelWidgets[w]);
                }
            }
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
                // This exact panel was created by this transaction; no user
                // panel can enter this branch.
                panel.remove();
                print("LEOS_PARTIAL_PANEL_ROLLED_BACK=1");
            } else if (panel && before) {
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
        "can_remove_leos_owned_dock": False,
        "touches_unmanaged_panels": False,
        "desktop_widgets_applied": False,
        "runtime_validated_on_bazzite": False,
        "requires_backup_and_explicit_confirmation": True,
    }
