import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1040
    height: 720
    minimumWidth: 760
    minimumHeight: 560
    visible: true
    title: "LEOS — Applications"
    color: "#090B10"
    property var themeColors: themeManager.palette
    property color primaryAccent: themeColors.accent_primary
    property color secondaryAccent: themeColors.accent_secondary
    property color primaryGlow: themeColors.accent_primary_glow
    property color secondaryGlow: themeColors.accent_secondary_glow
    property color muted: themeColors.muted_text

    function launchApplication(desktopId, applicationName) {
        if (!applicationCatalog.launch(desktopId))
            return false
        status.text = applicationName + " : lancement demandé."
        window.close()
        return true
    }

    Shortcut {
        sequence: "Escape"
        context: Qt.WindowShortcut
        onActivated: window.close()
    }

    Component.onCompleted: search.forceActiveFocus()

    Rectangle {
        anchors.fill: parent
        color: "transparent"
        Rectangle { width: 460; height: 460; radius: 230; x: parent.width - 260; y: -250; color: window.themeColors.accent_primary_soft; opacity: 0.13 }
        Rectangle { width: 360; height: 360; radius: 180; x: -210; y: parent.height - 190; color: window.themeColors.accent_secondary_soft; opacity: 0.12 }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 18

        RowLayout {
            Layout.fillWidth: true
            RowLayout {
                spacing: 10
                Image {
                    id: desktopMenuLogo
                    source: themeManager.assets.desktop_logo
                    asynchronous: true
                    smooth: true
                    fillMode: Image.PreserveAspectFit
                    Layout.preferredWidth: 92
                    Layout.preferredHeight: 52
                    visible: status === Image.Ready
                }
                ColumnLayout {
                    spacing: 2
                    Label {
                        text: "LEOS"
                        color: "white"
                        font.pixelSize: 27
                        font.weight: Font.Black
                        font.letterSpacing: 5
                        visible: desktopMenuLogo.status !== Image.Ready
                    }
                    Label {
                        text: "APPLICATIONS"
                        color: window.primaryAccent
                        font.pixelSize: 10
                        font.letterSpacing: 3
                    }
                }
            }
            Item { Layout.fillWidth: true }
            Label { text: applicationCatalog.applicationCount() + " applications détectées"; color: window.muted; font.pixelSize: 11 }
            Button {
                text: "MODES"
                onClicked: {
                    window.launchApplication("leos-mode-selector.desktop", "le sélecteur de modes")
                }
            }
            Button {
                text: "CENTRE DE CONTRÔLE"
                onClicked: {
                    window.launchApplication("leos-control-center.desktop", "le Centre de contrôle")
                }
            }
            Button {
                text: applicationCatalog.unreadNotificationCount > 0
                      ? "NOTIFICATIONS · " + applicationCatalog.unreadNotificationCount
                      : "NOTIFICATIONS"
                onClicked: {
                    window.launchApplication("leos-notifications.desktop", "le Centre de notifications")
                }
            }
            Button {
                text: "ACTUALISER"
                onClicked: applicationCatalog.refresh()
            }
        }

        TextField {
            id: search
            Layout.fillWidth: true
            placeholderText: "Rechercher une application…"
            font.pixelSize: 16
            color: "white"
            onTextChanged: applicationCatalog.setSearch(text)
            background: Rectangle { radius: 12; color: "#141B25"; border.width: search.activeFocus ? 2 : 1; border.color: search.activeFocus ? window.primaryAccent : "#303A49" }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 18

            Rectangle {
                Layout.preferredWidth: 205
                Layout.fillHeight: true
                radius: 15
                color: "#10151E"
                border.color: "#263140"
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    Label { text: "CATÉGORIES"; color: window.muted; font.pixelSize: 10; font.letterSpacing: 2 }
                    Repeater {
                        model: applicationCatalog.availableCategories
                        delegate: Button {
                            id: categoryMenuButton
                            required property string modelData
                            Layout.fillWidth: true
                            text: modelData
                            onClicked: applicationCatalog.setCategory(modelData)
                            background: Rectangle { radius: 8; color: categoryMenuButton.down ? "#1B2A36" : "transparent"; border.color: categoryMenuButton.down ? window.primaryAccent : "transparent" }
                            contentItem: Label { text: categoryMenuButton.text; color: "white"; font.pixelSize: 12; leftPadding: 7; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
                        }
                    }
                    Item { Layout.fillHeight: true }
                    Label { text: "UNE EXPÉRIENCE. DEUX MODES."; color: "#596678"; font.pixelSize: 8; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 15
                color: "#0E131B"
                border.color: "#263140"
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: applicationCatalog.currentCategory === "Tout" ? "Toutes les applications" : applicationCatalog.currentCategory; color: "white"; font.pixelSize: 18; font.weight: Font.DemiBold }
                        Item { Layout.fillWidth: true }
                        Button {
                            visible: applicationCatalog.currentCategory === "Récemment utilisées"
                            text: "EFFACER L’HISTORIQUE"
                            onClicked: {
                                if (applicationCatalog.clearRecentApplications())
                                    status.text = "Historique des applications effacé."
                                else
                                    status.text = "Impossible d’effacer l’historique."
                            }
                        }
                    }
                    GridView {
                        id: appGrid
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        keyNavigationEnabled: true
                        keyNavigationWraps: false
                        activeFocusOnTab: true
                        cellWidth: 180
                        cellHeight: 112
                        model: applicationCatalog
                        delegate: Item {
                            required property string name
                            required property string desktopId
                            required property string icon
                            required property string category
                            required property string description
                            required property bool isPinned
                            width: appGrid.cellWidth - 8
                            height: appGrid.cellHeight - 8
                            activeFocusOnTab: true
                            focus: GridView.isCurrentItem
                            function activateApplication() {
                                window.launchApplication(desktopId, name)
                            }
                            Keys.onPressed: {
                                if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter
                                        || event.key === Qt.Key_Space) {
                                    activateApplication()
                                    event.accepted = true
                                }
                            }
                            Rectangle {
                                anchors.fill: parent
                                radius: 11
                                color: appMouse.containsMouse ? "#1B2633" : "#151B25"
                                border.color: appMouse.containsMouse ? window.primaryAccent : "#2B3544"
                                Rectangle {
                                    anchors.fill: parent
                                    anchors.margins: -3
                                    radius: 14
                                    color: "transparent"
                                    border.width: 5
                                    border.color: window.primaryGlow
                                    opacity: appMouse.containsMouse ? 0.10 : 0
                                    Behavior on opacity { NumberAnimation { duration: 140 } }
                                }
                                Rectangle {
                                    anchors.fill: parent
                                    anchors.margins: -1
                                    radius: 12
                                    color: "transparent"
                                    border.width: 2
                                    border.color: window.secondaryGlow
                                    opacity: appMouse.containsMouse ? 0.12 : 0
                                    Behavior on opacity { NumberAnimation { duration: 140 } }
                                }
                            }
                            MouseArea {
                                id: appMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: window.launchApplication(desktopId, name)
                            }
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 5
                                RowLayout {
                                    Layout.fillWidth: true
                                    Image {
                                        source: "image://desktop-icons/" + encodeURIComponent(icon)
                                        sourceSize: Qt.size(64, 64)
                                        Layout.preferredWidth: 28
                                        Layout.preferredHeight: 28
                                        fillMode: Image.PreserveAspectFit
                                    }
                                    Item { Layout.fillWidth: true }
                                    ColumnLayout {
                                        visible: applicationCatalog.currentCategory === "Favoris"
                                        spacing: 0
                                        ToolButton {
                                            id: favouriteMoveUpButton
                                            text: "↑"
                                            enabled: visible && search.text.length === 0 && index > 0
                                            onClicked: {
                                                if (!applicationCatalog.moveFavourite(desktopId, -1))
                                                    status.text = "Impossible de réordonner les favoris."
                                            }
                                            contentItem: Label { text: favouriteMoveUpButton.text; color: favouriteMoveUpButton.enabled ? window.primaryAccent : "#596678"; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter }
                                            background: Rectangle { color: "transparent" }
                                        }
                                        ToolButton {
                                            id: favouriteMoveDownButton
                                            text: "↓"
                                            enabled: visible && search.text.length === 0 && index < appGrid.count - 1
                                            onClicked: {
                                                if (!applicationCatalog.moveFavourite(desktopId, 1))
                                                    status.text = "Impossible de réordonner les favoris."
                                            }
                                            contentItem: Label { text: favouriteMoveDownButton.text; color: favouriteMoveDownButton.enabled ? window.primaryAccent : "#596678"; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter }
                                            background: Rectangle { color: "transparent" }
                                        }
                                    }
                                    ToolButton {
                                        id: favouritePinButton
                                        text: isPinned ? "★" : "☆"
                                        onClicked: {
                                            const wasPinned = isPinned
                                            if (!applicationCatalog.toggleFavourite(desktopId))
                                                status.text = "Impossible de modifier les favoris du dock."
                                            else
                                                status.text = wasPinned ? "Application retirée des favoris." : "Application ajoutée aux favoris."
                                        }
                                        contentItem: Label { text: favouritePinButton.text; color: window.secondaryAccent; font.pixelSize: 18 }
                                        background: Rectangle { color: "transparent" }
                                    }
                                }
                                Label { text: name; color: "white"; font.pixelSize: 12; font.weight: Font.DemiBold; Layout.fillWidth: true; elide: Text.ElideRight }
                                Label { text: category; color: window.muted; font.pixelSize: 9; Layout.fillWidth: true; elide: Text.ElideRight }
                            }
                        }
                        Label {
                            anchors.centerIn: parent
                            visible: appGrid.count === 0
                            text: applicationCatalog.loading
                                ? "Chargement des applications…"
                                : "Aucune application trouvée.\\nEssaie une autre recherche ou actualise la liste."
                            color: window.muted
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }
                    Label { id: status; Layout.fillWidth: true; color: window.secondaryAccent; font.pixelSize: 10; elide: Text.ElideRight }
                }
            }
        }
    }

    Connections {
        target: applicationCatalog
        function onLaunchFailed(message) { status.text = message }
    }
}
