"""Safe Flatpak operations for LEOS Store.

No package operation is started until the UI calls an explicit confirmation slot.
All commands use argument arrays; no shell is involved.
"""

from __future__ import annotations

import re
import shutil

from PySide6.QtCore import QObject, Property, Signal, Slot, QProcess

from shop.catalog import CatalogModel
from shop.flatpak_inventory import (
    flatpak_uninstall_args,
    is_trusted_flathub_remote,
    parse_flatpak_inventory,
)
from shop.flatpak_metadata import runtime_summary
from desktop.notifications import post_notification


APP_ID_RE = re.compile(r"^[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)+$")


class StoreController(QObject):
    statusChanged = Signal(str)
    busyChanged = Signal(bool)
    operationFinished = Signal(bool, str)
    catalogUpdated = Signal()
    verificationDetailsChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.catalog = CatalogModel(self)
        self._status = "Catalogue LEOS prêt. Vérifie les sources avant toute opération."
        self._verification_details = "Les dépendances seront résolues par Flatpak."
        self._busy = False
        self._process = QProcess(self)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_error)
        self._process.readyReadStandardOutput.connect(self._read_output)
        self._process.readyReadStandardError.connect(self._read_output)
        self._action = ""
        self._target = ""
        self._stdout = bytearray()
        self._stderr = bytearray()

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=verificationDetailsChanged)
    def verificationDetails(self) -> str:
        return self._verification_details

    def _set_verification_details(self, message: str) -> None:
        if self._verification_details != message:
            self._verification_details = message
            self.verificationDetailsChanged.emit()

    def _set_status(self, message: str) -> None:
        self._status = message
        self.statusChanged.emit(message)

    def _set_busy(self, value: bool) -> None:
        if self._busy != value:
            self._busy = value
            self.busyChanged.emit(value)

    def _start(self, action: str, target: str, program: str, args: list[str]) -> None:
        if self._busy:
            if action == "verify-install":
                self._set_verification_details("Une autre opération Flatpak est déjà en cours.")
            self._set_status("Une opération est déjà en cours.")
            return
        executable = shutil.which(program)
        if not executable:
            if action in {"verify-remote", "verify-install"}:
                self._set_verification_details("Flatpak n'est pas disponible : la source et les dépendances n'ont pas pu être vérifiées.")
            self._set_status(f"{program} n'est pas disponible sur ce système.")
            post_notification("Opération impossible", self._status, "error")
            self.operationFinished.emit(False, self._status)
            return
        self._action, self._target = action, target
        self._stdout.clear()
        self._stderr.clear()
        self._process.start(executable, args)
        if not self._process.waitForStarted(1500):
            if action in {"verify-remote", "verify-install"}:
                self._set_verification_details("Impossible de vérifier la source Flathub et ses métadonnées.")
            self._set_status(f"Impossible de démarrer {program}.")
            self.operationFinished.emit(False, self._status)
            return
        self._set_busy(True)
        self._set_status("Vérification ou opération Flatpak en cours…")

    @Slot()
    def refreshInstalled(self) -> None:
        self._start("list", "", "flatpak", ["list", "--app", "--columns=application,installation"])

    @Slot(int, result="QVariant")
    def catalogItem(self, row: int):
        """Expose one catalogue record to QML for synchronizing the details pane."""
        return self.catalog.itemAt(row)

    @Slot(int)
    def requestInstall(self, row: int) -> None:
        item = self.catalog.itemAt(row)
        if not item:
            self._set_status("Application inconnue dans le catalogue.")
            return
        if not APP_ID_RE.fullmatch(item["id"]):
            self._set_status("Identifiant d'application invalide.")
            return
        if item.get("installed_scope"):
            self._set_status("Cette application est déjà installée.")
            return
        self._set_verification_details("Vérification de l'adresse officielle Flathub…")
        self._start(
            "verify-remote",
            item["id"],
            "flatpak",
            ["remotes", "--columns=name,url"],
        )

    @Slot(int)
    def requestUninstall(self, row: int) -> None:
        item = self.catalog.itemAt(row)
        if (
            not item
            or not APP_ID_RE.fullmatch(item["id"])
            or item.get("installed_scope") not in {"user", "system"}
        ):
            self._set_status("Cette application n'est pas reconnue comme une installation Flatpak gérable.")
            return
        self._start(
            "uninstall",
            item["id"],
            "flatpak",
            flatpak_uninstall_args(item["id"], item["installed_scope"]),
        )

    @Slot(int)
    def confirmInstall(self, row: int) -> None:
        item = self.catalog.itemAt(row)
        if (
            not item
            or item["id"] != self._target
            or self._action != "verified"
            or item.get("installed_scope")
        ):
            self._set_status("La vérification doit réussir et l'application ne doit pas déjà être installée.")
            return
        self._start(
            "install",
            item["id"],
            "flatpak",
            ["install", "--user", "--assumeyes", "flathub", item["id"]],
        )

    @Slot()
    def refreshCatalogue(self) -> None:
        self.refreshInstalled()

    def _on_finished(self, exit_code: int, _exit_status) -> None:
        stdout = bytes(self._stdout + self._process.readAllStandardOutput().data()).decode(
            "utf-8", errors="replace"
        )
        stderr = bytes(self._stderr + self._process.readAllStandardError().data()).decode(
            "utf-8", errors="replace"
        )
        action, target = self._action, self._target
        self._set_busy(False)

        if action == "list":
            if exit_code != 0:
                lines = stderr.strip().splitlines()
                reason = lines[-1] if lines else "Inventaire Flatpak indisponible."
                self._set_status(f"Impossible d'actualiser la boutique : {reason}")
                post_notification("Boutique LEOS", self._status, "warning")
                self.operationFinished.emit(False, self._status)
                return
            user_apps, system_apps = parse_flatpak_inventory(stdout)
            self.catalog.setInstalled(user_apps, system_apps)
            self.catalogUpdated.emit()
            total = len(user_apps | system_apps)
            self._set_status(
                f"{total} application(s) Flatpak détectée(s) "
                f"({len(user_apps)} utilisateur, {len(system_apps)} système)."
            )
            self.operationFinished.emit(True, self._status)
            return

        if action == "verify-remote":
            if exit_code == 0 and is_trusted_flathub_remote(stdout):
                self._set_verification_details("Adresse officielle Flathub confirmée. Lecture des métadonnées et du runtime…")
                self._start(
                    "verify-install",
                    target,
                    "flatpak",
                    ["remote-info", "--user", "--show-metadata", "flathub", target],
                )
            else:
                self._action = ""
                self._set_verification_details("Le dépôt nommé Flathub est absent ou son adresse n'est pas reconnue comme officielle. Aucune installation n'a été lancée.")
                self._set_status("Source Flathub non vérifiée : installation bloquée.")
                post_notification("Source non vérifiée", self._status, "warning")
                self.operationFinished.emit(False, self._status)
            return

        if action == "verify-install":
            if exit_code == 0:
                self._action = "verified"
                self._set_verification_details(runtime_summary(stdout))
                self._set_status(
                    f"{target} est disponible sur Flathub. Tu peux maintenant confirmer son installation."
                )
                self.operationFinished.emit(True, self._status)
            else:
                self._action = ""
                self._set_verification_details("Les informations de dépendances n’ont pas pu être vérifiées.")
                detail = stderr.strip().splitlines()
                reason = detail[-1] if detail else "Application ou dépôt indisponible."
                self._set_status(f"Vérification impossible : {reason}")
                post_notification("Vérification Flatpak échouée", self._status, "warning")
                self.operationFinished.emit(False, self._status)
            return

        if exit_code == 0:
            verb = "installée" if action == "install" else "désinstallée"
            message = f"{target} a été {verb}."
            self._set_status(message)
            post_notification("Boutique LEOS", message, "success")
            self.operationFinished.emit(True, message)
            self.refreshInstalled()
        else:
            lines = stderr.strip().splitlines()
            reason = lines[-1] if lines else "Flatpak a signalé une erreur."
            self._set_status(f"Opération non terminée : {reason}")
            post_notification("Échec d’une opération Flatpak", self._status, "error")
            self.operationFinished.emit(False, self._status)

    def _on_error(self, _error) -> None:
        if self._busy:
            failed_action = self._action
            self._set_busy(False)
            if failed_action in {"verify-remote", "verify-install"}:
                self._set_verification_details("Erreur pendant la lecture des métadonnées Flathub.")
            self._set_status("Erreur pendant l'exécution de Flatpak.")
            post_notification("Erreur Flatpak", self._status, "error")
            self.operationFinished.emit(False, self._status)

    def _read_output(self) -> None:
        self._stdout.extend(self._process.readAllStandardOutput().data())
        self._stderr.extend(self._process.readAllStandardError().data())
