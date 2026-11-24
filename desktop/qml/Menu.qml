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
    property var themeColors: leosTheme.themePalette
    color: themeColors.background
    property color cyan: themeColors.accent_primary_text
    property color magenta: themeColors.accent_secondary_text
    property color accentA: themeColors.accent_primary
    property color accentB: themeColors.accent_secondary
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
        Rectangle { width: 460; height: 460; radius: 230; x: parent.width - 260; y: -250; color: Qt.color(window.themeColors.accent_primary); opacity: 0.13 }
        Rectangle { width: 360; height: 360; radius: 180; x: -210; y: parent.height - 190; color: Qt.color(window.themeColors.accent_secondary); opacity: 0.12 }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: window.width < 900 ? 16 : 28
        spacing: window.width < 900 ? 12 : 18

        RowLayout {
            Layout.fillWidth: true
            RowLayout {
                spacing: window.width < 900 ? 7 : 10
                Image {
                    id: desktopMenuLogo
                    source: leosTheme.desktopLogoUrl
                    asynchronous: true
                    smooth: true
                    fillMode: Image.PreserveAspectFit
                    Layout.preferredWidth: window.width < 900 ? 70 : 92
                    Layout.preferredHeight: window.width < 900 ? 42 : 52
                    visible: status === Image.Ready
                }
                ColumnLayout {
                    spacing: 2
                    Label {
                        text: "LEOS"
                        color: window.themeColors.text
                        font.pixelSize: window.width < 900 ? 23 : 27
                        font.weight: Font.Black
                        font.letterSpacing: window.width < 900 ? 3 : 5
                        visible: desktopMenuLogo.status !== Image.Ready
                    }
                    Label {
                        text: "APPLICATIONS"
                        color: window.cyan
                        font.pixelSize: 10
                        font.letterSpacing: 3
                    }
                }
            }
            Item { Layout.fillWidth: true }
            Label {
                text: applicationCatalog.applicationCount() + " applications détectées"
                color: window.muted
                font.pixelSize: 11
                visible: window.width >= 980
            }
            Button {
                id: modesButton
                text: "MODES"
                onClicked: {
                    window.launchApplication("leos-mode-selector.desktop", "le sélecteur de modes")
                }
                background: Rectangle {
                    radius: 9
                    color: modesButton.down || modesButton.hovered || modesButton.activeFocus
                           ? window.themeColors.surface_elevated : window.themeColors.surface
                    border.width: modesButton.activeFocus ? 2 : 1
                    border.color: modesButton.activeFocus ? window.cyan
                                  : modesButton.hovered ? window.accentB : window.themeColors.border
                }
                contentItem: Label {
                    text: modesButton.text
                    color: window.themeColors.text
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
            Button {
                id: controlCenterButton
                text: window.width < 900 ? "CONTRÔLE" : "CENTRE DE CONTRÔLE"
                onClicked: {
                    window.launchApplication("leos-control-center.desktop", "le Centre de contrôle")
                }
                background: Rectangle {
                    radius: 9
                    color: controlCenterButton.down || controlCenterButton.hovered || controlCenterButton.activeFocus
                           ? window.themeColors.surface_elevated : window.themeColors.surface
                    border.width: controlCenterButton.activeFocus ? 2 : 1
                    border.color: controlCenterButton.activeFocus ? window.cyan
                                  : controlCenterButton.hovered ? window.accentB : window.themeColors.border
                }
                contentItem: Label {
                    text: controlCenterButton.text
                    color: window.themeColors.text
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
            Button {
                id: notificationsButton
                text: applicationCatalog.unreadNotificationCount > 0
                      ? (window.width < 900 ? "NOTIFS · " : "NOTIFICATIONS · ") + applicationCatalog.unreadNotificationCount
                      : (window.width < 900 ? "NOTIFS" : "NOTIFICATIONS")
                Accessible.name: "Ouvrir le centre de notifications LEOS"
                onClicked: {
                    window.launchApplication("leos-notifications.desktop", "le Centre de notifications")
                }
                background: Rectangle {
                    radius: 9
                    color: notificationsButton.down || notificationsButton.hovered || notificationsButton.activeFocus
                           ? window.themeColors.surface_elevated : window.themeColors.surface
                    border.width: notificationsButton.activeFocus ? 2 : 1
                    border.color: notificationsButton.activeFocus ? window.cyan
                                  : notificationsButton.hovered ? window.accentB : window.themeColors.border
                }
                contentItem: Label {
                    text: notificationsButton.text
                    color: window.themeColors.text
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
            Button {
                id: refreshButton
                text: window.width < 900 ? "↻" : "ACTUALISER"
                Accessible.name: "Actualiser le catalogue d'applications"
                onClicked: applicationCatalog.refresh()
                background: Rectangle {
                    radius: 9
                    color: refreshButton.down || refreshButton.hovered || refreshButton.activeFocus
                           ? window.themeColors.surface_elevated : window.themeColors.surface
                    border.width: refreshButton.activeFocus ? 2 : 1
                    border.color: refreshButton.activeFocus ? window.cyan
                                  : refreshButton.hovered ? window.accentB : window.themeColors.border
                }
                contentItem: Label {
                    text: refreshButton.text
                    color: window.themeColors.text
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }

        TextField {
            id: search
            Layout.fillWidth: true
            placeholderText: "Rechercher une application…"
            font.pixelSize: 16
            color: window.themeColors.text
            onTextChanged: applicationCatalog.setSearch(text)
            background: Rectangle {
                radius: 12
                color: window.themeColors.surface
                border.width: search.activeFocus ? 2 : 1
                border.color: search.activeFocus ? window.cyan : window.themeColors.border
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: window.width < 900 ? 12 : 18

            Rectangle {
                Layout.preferredWidth: window.width < 900 ? 160 : 205
                Layout.fillHeight: true
                radius: 15
                color: window.themeColors.surface
                border.color: window.themeColors.border
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
                            property bool categorySelected: applicationCatalog.currentCategory === modelData
                            onClicked: applicationCatalog.setCategory(modelData)
                            background: Rectangle {
                                radius: 9
                                color: categoryMenuButton.categorySelected
                                       ? window.themeColors.surface_elevated
                                       : (categoryMenuButton.down || categoryMenuButton.hovered
                                          ? window.themeColors.surface : "transparent")
                                border.width: categoryMenuButton.categorySelected || categoryMenuButton.activeFocus ? 1 : 0
                                border.color: categoryMenuButton.categorySelected ? window.accentA : window.themeColors.border

                                Rectangle {
                                    anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                                    anchors.leftMargin: 1
                                    width: 3
                                    radius: 2
                                    visible: categoryMenuButton.categorySelected
                                    gradient: Gradient {
                                        GradientStop { position: 0; color: window.accentA }
                                        GradientStop { position: 1; color: window.accentB }
                                    }
                                }
                            }
                            contentItem: Label {
                                text: categoryMenuButton.text
                                color: window.themeColors.text
                                font.pixelSize: 12
                                font.weight: categoryMenuButton.categorySelected ? Font.DemiBold : Font.Normal
                                leftPadding: 10
                                verticalAlignment: Text.AlignVCenter
                                elide: Text.ElideRight
                            }
                        }
                    }
                    Item { Layout.fillHeight: true }
                    Label { text: "UNE EXPÉRIENCE. DEUX MODES."; color: window.themeColors.muted_text; font.pixelSize: 8; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 15
                color: window.themeColors.surface
                border.color: window.themeColors.border
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: applicationCatalog.currentCategory === "Tout" ? "Toutes les applications" : applicationCatalog.currentCategory; color: window.themeColors.text; font.pixelSize: 18; font.weight: Font.DemiBold }
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
                        cellWidth: window.width < 900 ? 164 : 188
                        cellHeight: window.width < 900 ? 116 : 124
                        model: applicationCatalog
                        delegate: Item {
                            required property string name
                            required property string desktopId
                            required property string icon
                            required property string category
                            required property string description
                            required property bool isPinned
                            property bool keyboardFocused: appGrid.activeFocus && GridView.isCurrentItem
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
                                radius: 13
                                color: appMouse.containsMouse || keyboardFocused
                                       ? window.themeColors.surface_elevated : window.themeColors.surface
                                border.width: keyboardFocused ? 2 : 1
                                border.color: keyboardFocused ? window.cyan
                                              : appMouse.containsMouse ? window.accentB
                                              : window.themeColors.border

                                Rectangle {
                                    anchors { left: parent.left; right: parent.right; top: parent.top }
                                    anchors.leftMargin: 16
                                    anchors.rightMargin: 16
                                    height: 2
                                    radius: 1
                                    visible: keyboardFocused || appMouse.containsMouse
                                    gradient: Gradient {
                                        GradientStop { position: 0; color: window.accentA }
                                        GradientStop { position: 1; color: window.accentB }
                                    }
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
                                            contentItem: Label { text: favouriteMoveUpButton.text; color: favouriteMoveUpButton.enabled ? window.cyan : window.themeColors.muted_text; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter }
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
                                            contentItem: Label { text: favouriteMoveDownButton.text; color: favouriteMoveDownButton.enabled ? window.cyan : window.themeColors.muted_text; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter }
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
                                        contentItem: Label { text: favouritePinButton.text; color: window.magenta; font.pixelSize: 18 }
                                        background: Rectangle { color: "transparent" }
                                    }
                                }
                                Label { text: name; color: window.themeColors.text; font.pixelSize: 13; font.weight: Font.DemiBold; Layout.fillWidth: true; elide: Text.ElideRight }
                                Label { text: category; color: window.muted; font.pixelSize: 10; Layout.fillWidth: true; elide: Text.ElideRight }
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
                    Label { id: status; Layout.fillWidth: true; color: window.magenta; font.pixelSize: 10; elide: Text.ElideRight }
                }
            }
        }
    }

    Connections {
        target: applicationCatalog
        function onLaunchFailed(message) { status.text = message }
    }
}
