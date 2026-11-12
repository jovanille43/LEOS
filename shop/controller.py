"""Safe Flatpak operations for LEOS Store.

No package operation is started until the UI calls an explicit confirmation slot.
All commands use argument arrays; no shell is involved.
"""

from __future__ import annotations

import re
import shutil

from PySide6.QtCore import QObject, Property, Signal, Slot, QProcess, QTimer

from shop.catalog import CatalogModel
from shop.flatpak_inventory import (
    flatpak_uninstall_args,
    trusted_flathub_remote_url,
    parse_flatpak_inventory,
)
from shop.flatpak_metadata import runtime_summary
from desktop.notifications import post_notification


MAX_PROCESS_OUTPUT_BYTES = 4 * 1024 * 1024
OPERATION_TIMEOUTS_MS = {
    "list": 60_000,
    "verify-remote": 30_000,
    "verify-install": 90_000,
    "recheck-remote": 30_000,
    "install": 30 * 60 * 1000,
    "uninstall": 30 * 60 * 1000,
}


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
        self._status = (
            self.catalog.load_error
            or "Catalogue LEOS prêt. Vérifie les sources avant toute opération."
        )
        self._verification_details = "Les dépendances seront résolues par Flatpak."
        self._busy = False
        self._process = QProcess(self)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_error)
        self._process.readyReadStandardOutput.connect(self._read_output)
        self._process.readyReadStandardError.connect(self._read_output)
        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._on_timeout)
        self._action = ""
        self._target = ""
        self._verified_source_url = ""
        self._stdout = bytearray()
        self._stderr = bytearray()
        self._output_overflowed = False

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
            if action in {"verify-remote", "verify-install", "recheck-remote"}:
                self._set_verification_details("Une autre opération Flatpak est déjà en cours ; la vérification est annulée.")
            self._set_status("Une opération est déjà en cours.")
            return
        executable = shutil.which(program)
        if not executable:
            if action in {"verify-remote", "verify-install", "recheck-remote"}:
                self._set_verification_details("Flatpak n'est pas disponible : la source et les dépendances n'ont pas pu être vérifiées.")
            self._set_status(f"{program} n'est pas disponible sur ce système.")
            post_notification("Opération impossible", self._status, "error")
            self.operationFinished.emit(False, self._status)
            return
        self._action, self._target = action, target
        self._stdout.clear()
        self._stderr.clear()
        self._output_overflowed = False
        # QProcess reports startup failures through errorOccurred. Do not
        # block the GUI thread while Flatpak initializes.
        self._set_busy(True)
        self._set_status("Vérification ou opération Flatpak en cours…")
        self._process.start(executable, args)
        self._timeout_timer.start(OPERATION_TIMEOUTS_MS.get(action, 60_000))

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
        self._verified_source_url = ""
        self._set_verification_details("Vérification de l'adresse officielle Flathub…")
        self._start(
            "verify-remote",
            item["id"],
            "flatpak",
            ["remotes", "--user", "--columns=name,url"],
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
        # Recheck the remote after the user's final confirmation to avoid
        # installing from a source that changed after the metadata preview.
        self._start(
            "recheck-remote",
            item["id"],
            "flatpak",
            ["remotes", "--user", "--columns=name,url"],
        )

    @Slot()
    def refreshCatalogue(self) -> None:
        self.refreshInstalled()

    def _on_finished(self, exit_code: int, exit_status) -> None:
        # FailedToStart and some runtime errors can be followed by a finished
        # signal. The error handler already released this operation.
        if not self._busy:
            return
        self._timeout_timer.stop()
        if exit_status != QProcess.ExitStatus.NormalExit:
            exit_code = -1
        self._append_output(self._stdout, self._process.readAllStandardOutput().data())
        self._append_output(self._stderr, self._process.readAllStandardError().data())
        stdout = bytes(self._stdout).decode("utf-8", errors="replace")
        stderr = bytes(self._stderr).decode("utf-8", errors="replace")
        action, target = self._action, self._target
        self._set_busy(False)

        if self._output_overflowed:
            self._action = ""
            self._target = ""
            self._verified_source_url = ""
            self._set_status("La sortie Flatpak dépasse la limite ; le résultat n'est pas vérifiable. Vérifie l'état de l'application avant de réessayer.")
            self.operationFinished.emit(False, self._status)
            post_notification("Sortie Flatpak trop volumineuse", self._status, "warning")
            return

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
            remote_url = trusted_flathub_remote_url(stdout) if exit_code == 0 else ""
            if remote_url:
                self._verified_source_url = remote_url
                self._set_verification_details(
                    f"Adresse officielle Flathub confirmée : {remote_url}. Lecture des métadonnées et du runtime…"
                )
                self._start(
                    "verify-install",
                    target,
                    "flatpak",
                    ["remote-info", "--user", "--show-metadata", "flathub", target],
                )
            else:
                self._action = ""
                self._verified_source_url = ""
                self._set_verification_details("Le dépôt nommé Flathub est absent ou son adresse n'est pas reconnue comme officielle. Aucune installation n'a été lancée.")
                self._set_status("Source Flathub non vérifiée : installation bloquée.")
                post_notification("Source non vérifiée", self._status, "warning")
                self.operationFinished.emit(False, self._status)
            return

        if action == "recheck-remote":
            remote_url = trusted_flathub_remote_url(stdout) if exit_code == 0 else ""
            if remote_url and remote_url == self._verified_source_url:
                self._start(
                    "install",
                    target,
                    "flatpak",
                    ["install", "--user", "--assumeyes", "flathub", target],
                )
            else:
                self._action = ""
                self._verified_source_url = ""
                self._set_verification_details(
                    "Le dépôt Flathub a changé ou n'est plus vérifiable depuis l'aperçu. Aucune installation n'a été lancée."
                )
                self._set_status("La source Flathub a changé : installation bloquée.")
                post_notification("Source modifiée", self._status, "warning")
                self.operationFinished.emit(False, self._status)
            return

        if action == "verify-install":
            if exit_code == 0:
                self._action = "verified"
                self._set_verification_details(
                    f"Source vérifiée : {self._verified_source_url}\n{runtime_summary(stdout)}"
                )
                self._set_status(
                    f"{target} est disponible sur Flathub. Tu peux maintenant confirmer son installation."
                )
                self.operationFinished.emit(True, self._status)
            else:
                self._action = ""
                self._verified_source_url = ""
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

    def _on_timeout(self) -> None:
        if not self._busy or self._process.state() == QProcess.ProcessState.NotRunning:
            return
        failed_action = self._action
        target = self._target
        self._timeout_timer.stop()
        self._set_busy(False)
        self._action = ""
        self._target = ""
        self._verified_source_url = ""
        self._process.kill()
        if failed_action in {"verify-remote", "verify-install", "recheck-remote"}:
            self._set_verification_details("Le délai de vérification Flatpak est dépassé. La source n'est pas considérée comme vérifiée.")
        if failed_action in {"install", "uninstall"}:
            self._set_status(
                f"L'opération sur {target} dépasse le délai prévu. Son état doit être vérifié dans l'inventaire avant toute nouvelle tentative."
            )
        else:
            self._set_status("La vérification Flatpak a dépassé le délai prévu. Réessaie après avoir vérifié la connexion.")
        post_notification("Délai Flatpak dépassé", self._status, "warning")
        self.operationFinished.emit(False, self._status)

    def _on_error(self, _error) -> None:
        if self._busy:
            self._timeout_timer.stop()
            failed_action = self._action
            self._set_busy(False)
            self._action = ""
            self._target = ""
            self._verified_source_url = ""
            if failed_action in {"verify-remote", "verify-install", "recheck-remote"}:
                self._set_verification_details("Erreur pendant la vérification de la source ou des métadonnées Flathub.")
            self._set_status("Erreur pendant l'exécution de Flatpak.")
            post_notification("Erreur Flatpak", self._status, "error")
            self.operationFinished.emit(False, self._status)

    def _append_output(self, buffer: bytearray, chunk: bytes) -> None:
        remaining = MAX_PROCESS_OUTPUT_BYTES - len(buffer)
        if len(chunk) > remaining:
            self._output_overflowed = True
        if remaining > 0:
            buffer.extend(chunk[:remaining])

    def _read_output(self) -> None:
        self._append_output(self._stdout, self._process.readAllStandardOutput().data())
        self._append_output(self._stderr, self._process.readAllStandardError().data())
