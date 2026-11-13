import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1180
    height: 790
    visible: true
    title: "LEOS — Boutique"
    color: "#080a0f"

    property var themeColors: themeManager.palette
    property color cyan: themeColors.accent_primary
    property color magenta: themeColors.accent_secondary
    property color muted: themeColors.muted_text
    property int selectedRow: -1

    function normalizedSearchText(value) {
        return String(value || "")
            .normalize("NFKD")
            .toLowerCase()
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/\s+/g, " ")
            .trim()
    }

    function matchesSearch(name, appId, category, description, source) {
        const query = normalizedSearchText(searchField.text)
        if (!query)
            return true
        const searchable = normalizedSearchText(
            [name, appId, category, description, source].join(" ")
        )
        return searchable.includes(query)
    }

    Rectangle {
        anchors.fill: parent
        color: window.color
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 30
            spacing: 18

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    spacing: 3
                    Label {
                        text: "LEOS"
                        color: "white"
                        font.pixelSize: 30
                        font.weight: Font.Black
                        font.letterSpacing: 5
                    }
                    Label {
                        text: "BOUTIQUE"
                        color: window.cyan
                        font.pixelSize: 10
                        font.letterSpacing: 4
                    }
                }
                Item { Layout.fillWidth: true }
                Button {
                    text: "ACTUALISER"
                    enabled: !store.busy
                    onClicked: store.refreshInstalled()
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 16
                TextField {
                    id: searchField
                    Layout.fillWidth: true
                    placeholderText: "Rechercher une application…"
                    color: "white"
                    enabled: !store.busy
                }
                ComboBox {
                    id: categoryFilter
                    model: ["Toutes", "Gaming", "Multimedia", "Internet", "Productivité", "Création"]
                    enabled: !store.busy
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 18

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 14
                    color: "#111720"
                    border.color: "#293342"
                    ListView {
                        id: appList
                        anchors.fill: parent
                        anchors.margins: 8
                        clip: true
                        spacing: 6
                        model: catalogModel
                        enabled: !store.busy
                        delegate: Rectangle {
                            required property string appId
                            required property string name
                            required property string category
                            required property string description
                            required property string source
                            required property string compatibility
                            required property string operationNote
                            required property bool installed
                            required property string installedScope
                            required property bool bundled
                            required property int index
                            width: ListView.view.width
                            height: visible ? 86 : 0
                            visible: (categoryFilter.currentText === "Toutes" || category === categoryFilter.currentText)
                                && window.matchesSearch(name, appId, category, description, source)
                            radius: 9
                            color: window.selectedRow === index ? "#182a36" : "#151b25"
                            border.color: window.selectedRow === index ? window.cyan : "#28313e"
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 12
                                Rectangle {
                                    Layout.preferredWidth: 42
                                    Layout.preferredHeight: 42
                                    radius: 10
                                    color: "#202c3b"
                                    Label {
                                        anchors.centerIn: parent
                                        text: name.length ? name.substring(0, 1).toUpperCase() : "L"
                                        color: window.cyan
                                        font.pixelSize: 20
                                        font.weight: Font.Bold
                                    }
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 3
                                    Label { text: name; color: "white"; font.pixelSize: 14; font.weight: Font.DemiBold }
                                    Label { text: category + "  •  " + source; color: window.muted; font.pixelSize: 10 }
                                }
                                Label {
                                    text: installedScope === "system" ? (bundled ? "INCLUSE LEOS" : "SYSTÈME") : installed ? "INSTALLÉE" : "DISPONIBLE"
                                    color: installed ? window.cyan : window.muted
                                    font.pixelSize: 9
                                }
                            }
                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    window.selectedRow = index
                                    detailsPane.appId = appId
                                    detailsPane.appName = name
                                    detailsPane.appDescription = description
                                    detailsPane.appSource = source
                                    detailsPane.appCompatibility = compatibility
                                    detailsPane.operationNote = operationNote
                                    detailsPane.isInstalled = installed
                                    detailsPane.installedScope = installedScope
                                    detailsPane.bundled = bundled
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    id: detailsPane
                    property string appId: ""
                    property string appName: "Choisis une application"
                    property string appDescription: "Les détails et les opérations apparaîtront ici."
                    property string appSource: ""
                    property string appCompatibility: ""
                    property string operationNote: ""
                    property bool isInstalled: false
                    property string installedScope: ""
                    property bool bundled: false
                    Layout.preferredWidth: 360
                    Layout.fillHeight: true
                    radius: 14
                    color: "#111720"
                    border.color: "#293342"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 12
                        Label { text: "FICHE APPLICATION"; color: window.cyan; font.pixelSize: 10; font.letterSpacing: 2 }
                        Label {
                            text: detailsPane.appName
                            color: "white"
                            font.pixelSize: 22
                            font.weight: Font.Bold
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Label {
                            text: detailsPane.appDescription
                            color: window.muted
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#293342" }
                        Label { text: "SOURCE"; color: window.cyan; font.pixelSize: 9 }
                        Label { text: detailsPane.appSource; color: "white"; font.pixelSize: 12 }
                        Label { text: "COMPATIBILITÉ"; color: window.cyan; font.pixelSize: 9 }
                        Label {
                            text: detailsPane.appCompatibility
                            color: window.muted
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Label {
                            text: detailsPane.operationNote
                            color: window.muted
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Label {
                            Layout.fillWidth: true
                            visible: detailsPane.installedScope === "system"
                            text: "Cette application est installée pour tout le système. Sa désinstallation peut demander une autorisation administrateur."
                            color: window.cyan
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                        }
                        Item { Layout.fillHeight: true }
                        Button {
                            id: installRemoveButton
                            Layout.fillWidth: true
                            enabled: detailsPane.appId.length > 0 && !store.busy
                            text: detailsPane.isInstalled ? "DÉSINSTALLER" : "INSTALLER"
                            onClicked: operationDialog.open()
                            background: Rectangle {
                                radius: 8
                                color: detailsPane.installedScope === "system" ? "#19322e" : detailsPane.isInstalled ? "#33202a" : "#12313b"
                                border.color: detailsPane.installedScope === "system" ? "#4aaf91" : detailsPane.isInstalled ? window.magenta : window.cyan
                            }
                            contentItem: Label {
                                text: installRemoveButton.text
                                color: "white"
                                font.weight: Font.Bold
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: store.status
                    color: window.muted
                    font.pixelSize: 11
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
                BusyIndicator { running: store.busy; visible: store.busy; implicitWidth: 28; implicitHeight: 28 }
            }
        }
    }

    Dialog {
        id: operationDialog
        title: detailsPane.isInstalled ? "Confirmer la désinstallation" : "Confirmer l'installation"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Cancel
        width: 480

        ColumnLayout {
            width: parent.width
            spacing: 12
            Label {
                text: (detailsPane.isInstalled ? "Tu vas désinstaller " : "Tu vas installer ")
                      + detailsPane.appName + "."
                color: "white"
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                text: "Identifiant : " + detailsPane.appId + "\nSource : " + detailsPane.appSource
                color: window.muted
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                text: detailsPane.isInstalled
                    ? (detailsPane.installedScope === "system" ? "L'application sera retirée de l'installation système. Une autorisation administrateur peut être demandée. Les données personnelles ne sont pas supprimées automatiquement." : "L'application sera retirée du profil utilisateur. Les données personnelles ne sont pas supprimées automatiquement.")
                    : "LEOS vérifiera d'abord la disponibilité sur Flathub. Flatpak pourra installer les dépendances et runtimes nécessaires."
                color: window.muted
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Button {
                text: "CONFIRMER"
                Layout.fillWidth: true
                onClicked: {
                    operationDialog.close()
                    if (detailsPane.isInstalled)
                        store.requestUninstall(window.selectedRow)
                    else
                        store.requestInstall(window.selectedRow)
                }
            }
        }
    }

    Connections {
        target: store
        function onOperationFinished(success, message) {
            if (!success || !message.includes("disponible sur Flathub"))
                return
            verifyDialog.open()
        }
        function onCatalogUpdated() {
            if (window.selectedRow < 0)
                return
            const item = store.catalogItem(window.selectedRow)
            if (!item)
                return
            detailsPane.isInstalled = item.installed_scope !== ""
            detailsPane.installedScope = item.installed_scope
        }
    }

    Dialog {
        id: verifyDialog
        title: "Source vérifiée"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Cancel
        width: 440
        ColumnLayout {
            width: parent.width
            Label {
                text: "Flathub confirme que " + detailsPane.appName + " est disponible. Confirmer maintenant son installation ?"
                color: "white"
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                text: store.verificationDetails
                color: window.muted
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Button {
                text: "INSTALLER MAINTENANT"
                Layout.fillWidth: true
                onClicked: {
                    verifyDialog.close()
                    store.confirmInstall(window.selectedRow)
                }
            }
        }
    }

    Component.onCompleted: {
        if (Qt.application.arguments.includes("--debug"))
            console.log("LEOS Store started")
    }
}
