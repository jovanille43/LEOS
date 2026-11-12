"""Generate guarded Plasma scripting commands for the LEOS dock.

The returned JavaScript is executed only by the explicit Control Center action
after a private backup and user confirmation. It supports only a single panel
and never deletes panels or alters multi-panel layouts.
"""
from __future__ import annotations

import json
import re
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


MAX_PINNED_LAUNCHERS = 32
_DESKTOP_ID_RE = re.compile(r"^[A-Za-z0-9_.+-]{1,240}\.desktop$")


def build_panel_management_script(
    layout: object, pinned_apps: object = ()
) -> str:
    """Build a Plasma 6 script with validated launcher IDs; never execute it here."""
    if not validate_layout(layout):
        raise ValueError("Invalid LEOS desktop layout")
    if (
        not isinstance(pinned_apps, (list, tuple))
        or len(pinned_apps) > MAX_PINNED_LAUNCHERS
        or any(
            not isinstance(item, str) or not _DESKTOP_ID_RE.fullmatch(item)
            for item in pinned_apps
        )
        or len(set(pinned_apps)) != len(pinned_apps)
    ):
        raise ValueError("Invalid LEOS dock favourites")
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
    launchers_json = json.dumps(list(pinned_apps), ensure_ascii=True, separators=(",", ":"))
    return (
        _SCRIPT.replace("__LEOS_CONFIG__", config_json)
        .replace("__LEOS_WIDGETS__", widgets_json)
        .replace("__LEOS_PINNED_APPS__", launchers_json)
    )


_SCRIPT = r'''(function () {
    "use strict";
    var versionMajor = parseInt(String(applicationVersion).split(".")[0], 10);
    if (!versionMajor || versionMajor < 6) {
        throw new Error("Cet adaptateur exige Plasma 6 ou une version ultérieure.");
    }

    var desired = __LEOS_CONFIG__;
    var widgetTypes = __LEOS_WIDGETS__;
    var pinnedApps = __LEOS_PINNED_APPS__;
    var markerGroup = "LEOS";
    var markerValue = "leos-panel-v1";
    var allPanels = panels();
    var existing = [];

    function isLeosPanel(candidate) {
        candidate.currentConfigGroup = [markerGroup];
        return candidate.readConfig("managedBy", "") === markerValue;
    }

    function findTaskManager(candidate) {
        var manager = candidate.widgets("org.kde.plasma.icontasks");
        if (manager.length === 0) {
            manager = candidate.widgets("org.kde.plasma.taskmanager");
        }
        return manager.length ? manager[0] : null;
    }

    function snapshotPanel(candidate) {
        candidate.currentConfigGroup = [markerGroup];
        var state = {
            location: candidate.location,
            alignment: candidate.alignment,
            hiding: candidate.hiding,
            height: candidate.height,
            lengthMode: candidate.lengthMode,
            length: candidate.length,
            managedBy: candidate.readConfig("managedBy", ""),
            taskManager: null,
            launchers: null
        };
        var manager = findTaskManager(candidate);
        if (manager) {
            manager.currentConfigGroup = ["General"];
            state.taskManager = manager;
            state.launchers = manager.readConfig("launchers", []);
        }
        return state;
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
        before = snapshotPanel(panel);
    } else if (allPanels.length === 1) {
        panel = allPanels[0];
        adopted = true;
        before = snapshotPanel(panel);
        // Keep all existing applets, including a regular task manager.
        var essentialWidgets = [
            "org.kde.plasma.systemtray",
            "org.kde.plasma.digitalclock"
        ];
        if (!findTaskManager(panel)
                && knownWidgetTypes.indexOf("org.kde.plasma.icontasks") !== -1) {
            widgetsToAdd.push("org.kde.plasma.icontasks");
        }
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

        var manager = findTaskManager(panel);
        if (!manager) {
            throw new Error("Le gestionnaire de tâches KDE est indisponible ; le dock n'a pas été modifié.");
        }
        var resolvedLaunchers = [];
        for (var p = 0; p < pinnedApps.length; p++) {
            if (applicationExists(pinnedApps[p])) {
                resolvedLaunchers.push("applications:" + pinnedApps[p]);
            }
        }
        if (pinnedApps.length === 0 || resolvedLaunchers.length > 0) {
            manager.currentConfigGroup = ["General"];
            manager.writeConfig("launchers", resolvedLaunchers);
            manager.reloadConfig();
            print("LEOS_PINNED_LAUNCHERS_APPLIED=" + resolvedLaunchers.length);
        } else {
            print("LEOS_PINNED_LAUNCHERS_UNAVAILABLE=1");
        }

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
                if (before.taskManager && before.launchers !== null) {
                    before.taskManager.currentConfigGroup = ["General"];
                    before.taskManager.writeConfig("launchers", before.launchers);
                    before.taskManager.reloadConfig();
                }
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
