import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1180
    height: 790
    minimumWidth: 900
    minimumHeight: 640
    visible: true
    title: "LEOS — Boutique"
    property var themeColors: leosTheme.themePalette
    color: themeColors.background

    property color cyan: themeColors.accent_primary_text
    property color magenta: themeColors.accent_secondary_text
    property color accentA: themeColors.accent_primary
    property color accentB: themeColors.accent_secondary
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

    function clearSelection() {
        selectedRow = -1
        detailsPane.appId = ""
        detailsPane.appName = "Choisis une application"
        detailsPane.appDescription = "Sélectionne une application pour consulter sa fiche et ses options."
        detailsPane.appSource = ""
        detailsPane.appCompatibility = ""
        detailsPane.operationNote = ""
        detailsPane.isInstalled = false
        detailsPane.installedScope = ""
        detailsPane.bundled = false
    }

    function selectApp(row, id, name, description, source, compatibility, note, installed, scope, bundled) {
        selectedRow = row
        detailsPane.appId = id
        detailsPane.appName = name
        detailsPane.appDescription = description
        detailsPane.appSource = source
        detailsPane.appCompatibility = compatibility
        detailsPane.operationNote = note
        detailsPane.isInstalled = installed
        detailsPane.installedScope = scope
        detailsPane.bundled = bundled
    }

    Rectangle {
        anchors.fill: parent
        color: window.color
        Rectangle {
            width: 500
            height: 500
            radius: 250
            x: parent.width - width * 0.52
            y: -height * 0.5
            color: window.themeColors.accent_primary
            opacity: 0.05
        }
        Rectangle {
            width: 420
            height: 420
            radius: 210
            x: -width * 0.48
            y: parent.height - height * 0.52
            color: window.themeColors.accent_secondary
            opacity: 0.04
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: window.width < 1080 ? 18 : 30
            spacing: window.width < 1080 ? 12 : 18

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    spacing: 3
                    Label {
                        text: "LEOS"
                        color: window.themeColors.text
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
                ColumnLayout {
                    spacing: 2
                    Label {
                        text: "DÉCOUVRIR · INSTALLER · GÉRER"
                        color: window.muted
                        font.pixelSize: 9
                        font.letterSpacing: 1.1
                    }
                    Label {
                        text: "Un catalogue clair, des actions toujours confirmées."
                        color: window.themeColors.text
                        font.pixelSize: 11
                    }
                }
                Button {
                    id: refreshStoreButton
                    text: "ACTUALISER"
                    enabled: !store.busy
                    Accessible.name: "Actualiser les applications installées"
                    onClicked: store.refreshInstalled()
                    background: Rectangle {
                        radius: 8
                        color: refreshStoreButton.hovered || refreshStoreButton.activeFocus ? window.themeColors.surface_elevated : window.themeColors.surface
                        border.width: refreshStoreButton.activeFocus ? 2 : 1
                        border.color: refreshStoreButton.activeFocus ? window.themeColors.text : refreshStoreButton.hovered ? window.accentB : window.themeColors.border
                    }
                    contentItem: Label {
                        text: refreshStoreButton.text
                        color: window.themeColors.text
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 16
                TextField {
                    id: searchField
                    Layout.fillWidth: true
                    placeholderText: "Rechercher une application, un éditeur ou un identifiant…"
                    color: window.themeColors.text
                    font.pixelSize: 13
                    enabled: !store.busy
                    Accessible.name: "Rechercher dans la Boutique LEOS"
                    Accessible.description: "Recherche dans les noms, descriptions, catégories et identifiants des applications."
                    onTextChanged: window.clearSelection()
                    background: Rectangle {
                        radius: 9
                        color: window.themeColors.surface
                        border.width: searchField.activeFocus ? 2 : 1
                        border.color: searchField.activeFocus ? window.themeColors.text : window.themeColors.border
                    }
                }
                ComboBox {
                    id: categoryFilter
                    model: ["Toutes", "Gaming", "Émulation", "Multimedia", "Internet", "Productivité", "Création"]
                    enabled: !store.busy
                    Accessible.name: "Filtrer par catégorie"
                    onCurrentTextChanged: window.clearSelection()
                    background: Rectangle {
                        radius: 9
                        color: window.themeColors.surface
                        border.width: categoryFilter.activeFocus ? 2 : 1
                        border.color: categoryFilter.activeFocus ? window.themeColors.text : window.themeColors.border
                    }
                    contentItem: Label {
                        leftPadding: 10
                        rightPadding: 24
                        text: categoryFilter.displayText
                        color: window.themeColors.text
                        font.pixelSize: 12
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
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
                    color: window.themeColors.surface
                    border.color: window.themeColors.border
                    RowLayout {
                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.topMargin: 12
                        anchors.leftMargin: 14
                        anchors.rightMargin: 14
                        height: 20
                        Label {
                            text: "CATALOGUE"
                            color: window.cyan
                            font.pixelSize: 10
                            font.letterSpacing: 1.8
                        }
                        Item { Layout.fillWidth: true }
                        Label {
                            text: appList.count + " APPLICATIONS"
                            color: window.muted
                            font.pixelSize: 9
                            font.letterSpacing: 0.8
                        }
                    }
                    ListView {
                        id: appList
                        anchors.fill: parent
                        anchors.margins: 8
                        anchors.topMargin: 40
                        clip: true
                        spacing: 6
                        model: catalogModel
                        currentIndex: window.selectedRow
                        enabled: !store.busy
                        Accessible.role: Accessible.List
                        Accessible.name: "Catalogue d'applications LEOS"
                        Accessible.description: "Sélectionne une application pour afficher sa fiche et l'action disponible."
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
                            color: window.selectedRow === index || appRowButton.hovered || appRowButton.activeFocus
                                   ? window.themeColors.surface_elevated : window.themeColors.surface
                            border.width: window.selectedRow === index || appRowButton.activeFocus ? 1 : 0
                            border.color: appRowButton.activeFocus ? window.themeColors.text : window.selectedRow === index ? window.accentA : window.themeColors.border
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 12
                                Rectangle {
                                    Layout.preferredWidth: 42
                                    Layout.preferredHeight: 42
                                    radius: 10
                                    color: window.themeColors.surface_elevated
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
                                    Label { text: name; color: window.themeColors.text; font.pixelSize: 14; font.weight: Font.DemiBold }
                                    Label { text: category + "  •  " + source; color: window.muted; font.pixelSize: 10 }
                                }
                                Rectangle {
                                    radius: 6
                                    Layout.preferredHeight: 24
                                    Layout.preferredWidth: 86
                                    color: installed ? window.themeColors.surface_elevated : window.themeColors.background
                                    border.color: installed ? window.accentA : window.themeColors.border
                                    Label {
                                        anchors.centerIn: parent
                                        text: installedScope === "system" ? "SYSTÈME" : installed ? "INSTALLÉE" : "DISPONIBLE"
                                        color: installed ? window.cyan : window.muted
                                        font.pixelSize: 9
                                        font.weight: Font.DemiBold
                                    }
                                }
                            }
                            Button {
                                id: appRowButton
                                anchors.fill: parent
                                activeFocusOnTab: true
                                Accessible.role: Accessible.Button
                                Accessible.name: name + (installed ? ", installée" : ", disponible")
                                Accessible.description: category + ". Source " + source + ". Activer pour ouvrir la fiche."
                                Accessible.selected: window.selectedRow === index
                                background: Item { }
                                contentItem: Item { }
                                onClicked: window.selectApp(index, appId, name, description, source,
                                                            compatibility, operationNote, installed,
                                                            installedScope, bundled)
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
                    Layout.preferredWidth: window.width < 1080 ? 300 : 360
                    Layout.minimumWidth: 280
                    Layout.fillHeight: true
                    radius: 14
                    color: window.themeColors.surface
                    border.color: window.themeColors.border

                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.leftMargin: 16
                        anchors.rightMargin: 16
                        height: 2
                        radius: 1
                        gradient: Gradient {
                            GradientStop { position: 0; color: window.accentA }
                            GradientStop { position: 1; color: window.accentB }
                        }
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 12
                        RowLayout {
                            Layout.fillWidth: true
                            Label { text: "FICHE APPLICATION"; color: window.cyan; font.pixelSize: 10; font.letterSpacing: 2 }
                            Item { Layout.fillWidth: true }
                            Rectangle {
                                radius: 6
                                color: detailsPane.isInstalled ? window.themeColors.surface_elevated : window.themeColors.background
                                border.color: detailsPane.isInstalled ? window.accentA : window.themeColors.border
                                Layout.preferredHeight: 22
                                Layout.preferredWidth: detailsPane.appId.length === 0 ? 92 : detailsPane.isInstalled ? 86 : 96
                                Label {
                                    anchors.centerIn: parent
                                    text: detailsPane.appId.length === 0 ? "EN ATTENTE" : detailsPane.isInstalled ? "INSTALLÉE" : "À DÉCOUVRIR"
                                    color: detailsPane.isInstalled ? window.cyan : window.muted
                                    font.pixelSize: 9
                                    font.weight: Font.DemiBold
                                }
                            }
                        }
                        Label {
                            text: detailsPane.appName
                            color: window.themeColors.text
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
                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: window.themeColors.border }
                        Label { text: "SOURCE"; color: window.cyan; font.pixelSize: 9 }
                        Label { text: detailsPane.appSource; color: window.themeColors.text; font.pixelSize: 12 }
                        Label { text: "IDENTIFIANT"; color: window.cyan; font.pixelSize: 9 }
                        Label {
                            text: detailsPane.appId || "—"
                            color: window.themeColors.muted_text
                            font.pixelSize: 10
                            wrapMode: Text.WrapAnywhere
                            Layout.fillWidth: true
                        }
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
                            Layout.preferredHeight: 46
                            enabled: detailsPane.appId.length > 0 && !store.busy
                            text: detailsPane.isInstalled ? "DÉSINSTALLER" : "INSTALLER"
                            Accessible.name: text + " " + detailsPane.appName
                            Accessible.description: "Une confirmation sera demandée avant toute modification."
                            onClicked: operationDialog.open()
                            background: Rectangle {
                                radius: 9
                                color: installRemoveButton.down || installRemoveButton.hovered || installRemoveButton.activeFocus
                                       ? window.themeColors.surface_elevated : window.themeColors.surface
                                border.width: installRemoveButton.activeFocus ? 2 : 1
                                border.color: installRemoveButton.activeFocus ? window.themeColors.text
                                              : detailsPane.installedScope === "system" ? window.accentA
                                              : detailsPane.isInstalled ? window.accentB : window.accentA
                            }
                            contentItem: Label {
                                text: installRemoveButton.text
                                color: window.themeColors.text
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
                color: window.themeColors.text
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
                color: window.themeColors.text
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
