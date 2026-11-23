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
    property color focusColor: "#FFFFFF"
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
        Rectangle { width: 460; height: 460; radius: 230; x: parent.width - 260; y: -250; color: Qt.color(window.accentA); opacity: 0.065 }
        Rectangle { width: 360; height: 360; radius: 180; x: -210; y: parent.height - 190; color: Qt.color(window.accentB); opacity: 0.055 }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 30
        spacing: 20

        RowLayout {
            Layout.fillWidth: true
            RowLayout {
                spacing: 10
                Image {
                    id: desktopMenuLogo
                    source: leosTheme.desktopLogoUrl
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
                        color: window.cyan
                        font.pixelSize: 10
                        font.weight: Font.Bold
                        font.letterSpacing: 3
                    }
                }
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                radius: 10
                color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.07)
                border.color: window.themeColors.border
                implicitWidth: applicationCountLabel.implicitWidth + 22
                implicitHeight: 34
                Label {
                    id: applicationCountLabel
                    anchors.centerIn: parent
                    text: applicationCatalog.applicationCount() + " APPLICATIONS"
                    color: window.muted
                    font.pixelSize: 9
                    font.weight: Font.DemiBold
                    font.letterSpacing: 0.8
                }
            }
            Button {
                id: modeButton
                text: "MODES"
                implicitHeight: 36
                onClicked: {
                    window.launchApplication("leos-mode-selector.desktop", "le sélecteur de modes")
                }
                background: Rectangle {
                    radius: 10
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, modeButton.down ? 0.18 : 0.12) }
                        GradientStop { position: 1.0; color: Qt.rgba(window.accentB.r, window.accentB.g, window.accentB.b, modeButton.down ? 0.12 : 0.07) }
                    }
                    border.color: modeButton.hovered ? window.accentA : window.themeColors.border
                }
                contentItem: Label {
                    text: modeButton.text
                    color: window.themeColors.text
                    font.pixelSize: 9
                    font.weight: Font.Bold
                    letterSpacing: 0.8
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: 10
                    rightPadding: 10
                }
            }
            Button {
                id: controlCenterButton
                text: "CENTRE DE CONTRÔLE"
                implicitHeight: 36
                onClicked: {
                    window.launchApplication("leos-control-center.desktop", "le Centre de contrôle")
                }
                background: Rectangle {
                    radius: 10
                    color: controlCenterButton.hovered ? window.themeColors.surface_elevated : window.themeColors.surface
                    border.color: controlCenterButton.hovered ? window.accentA : window.themeColors.border
                }
                contentItem: Label {
                    text: controlCenterButton.text
                    color: window.themeColors.text
                    font.pixelSize: 9
                    font.weight: Font.DemiBold
                    letterSpacing: 0.4
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: 10
                    rightPadding: 10
                }
            }
            Button {
                id: notificationsButton
                text: applicationCatalog.unreadNotificationCount > 0
                      ? "NOTIFICATIONS · " + applicationCatalog.unreadNotificationCount
                      : "NOTIFICATIONS"
                implicitHeight: 36
                onClicked: {
                    window.launchApplication("leos-notifications.desktop", "le Centre de notifications")
                }
                background: Rectangle {
                    radius: 10
                    color: Qt.rgba(window.accentB.r, window.accentB.g, window.accentB.b, notificationsButton.hovered ? 0.13 : 0.07)
                    border.color: notificationsButton.hovered ? window.accentB : window.themeColors.border
                }
                contentItem: Label {
                    text: notificationsButton.text
                    color: window.themeColors.text
                    font.pixelSize: 9
                    font.weight: Font.DemiBold
                    letterSpacing: 0.4
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: 10
                    rightPadding: 10
                }
            }
            Button {
                id: refreshButton
                text: "ACTUALISER"
                implicitHeight: 36
                onClicked: applicationCatalog.refresh()
                background: Rectangle {
                    radius: 10
                    color: refreshButton.hovered ? window.themeColors.surface_elevated : "transparent"
                    border.color: refreshButton.hovered ? window.themeColors.muted_text : window.themeColors.border
                }
                contentItem: Label {
                    text: refreshButton.text
                    color: window.muted
                    font.pixelSize: 9
                    font.weight: Font.DemiBold
                    letterSpacing: 0.4
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: 10
                    rightPadding: 10
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 2
            radius: 1
            opacity: 0.70
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: window.accentA }
                GradientStop { position: 0.50; color: window.themeColors.border }
                GradientStop { position: 1.0; color: window.accentB }
            }
        }

        TextField {
            id: search
            Layout.fillWidth: true
            placeholderText: "Rechercher une application…"
            font.pixelSize: 17
            color: window.themeColors.text
            selectByMouse: true
            onTextChanged: applicationCatalog.setSearch(text)
            background: Rectangle {
                radius: 14
                color: window.themeColors.surface_elevated
                border.width: search.activeFocus ? 2 : 1
                border.color: search.activeFocus ? window.accentA : window.themeColors.border
                Behavior on border.color { ColorAnimation { duration: 140 } }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 18

            Rectangle {
                Layout.preferredWidth: 215
                Layout.fillHeight: true
                radius: 18
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
                            onClicked: applicationCatalog.setCategory(modelData)
                            background: Rectangle {
                                radius: 9
                                color: categoryMenuButton.down || categoryMenuButton.hovered
                                       || modelData === applicationCatalog.currentCategory
                                       ? window.themeColors.surface_elevated : "transparent"
                                border.width: modelData === applicationCatalog.currentCategory ? 1 : 0
                                border.color: window.accentA
                            }
                            contentItem: Label {
                                text: categoryMenuButton.text
                                color: window.themeColors.text
                                font.pixelSize: 13
                                leftPadding: 9
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
                radius: 18
                color: window.themeColors.surface
                border.color: window.themeColors.border
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
                        cellWidth: 196
                        cellHeight: 126
                        model: applicationCatalog
                        delegate: Item {
                            required property string name
                            required property string desktopId
                            required property string icon
                            required property string category
                            required property string description
                            required property bool isPinned
                            id: appTile
                            width: appGrid.cellWidth - 10
                            height: appGrid.cellHeight - 10
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
                                radius: 14
                                gradient: Gradient {
                                    GradientStop {
                                        position: 0.0
                                        color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b,
                                                       appMouse.containsMouse || appTile.activeFocus ? 0.11 : 0.035)
                                    }
                                    GradientStop { position: 1.0; color: window.themeColors.surface }
                                }
                                border.width: appMouse.containsMouse || appTile.activeFocus ? 2 : 1
                                border.color: appTile.activeFocus ? window.focusColor
                                              : appMouse.containsMouse ? window.accentA : window.themeColors.border
                                Behavior on border.color { ColorAnimation { duration: 140 } }
                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.top: parent.top
                                    anchors.bottom: parent.bottom
                                    width: appMouse.containsMouse || appTile.activeFocus ? 3 : 0
                                    radius: 2
                                    color: window.accentA
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
                                anchors.margins: 12
                                spacing: 7
                                RowLayout {
                                    Layout.fillWidth: true
                                    Image {
                                        source: "image://desktop-icons/" + encodeURIComponent(icon)
                                        sourceSize: Qt.size(64, 64)
                                        Layout.preferredWidth: 36
                                        Layout.preferredHeight: 36
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
                    Label { id: status; Layout.fillWidth: true; color: window.themeColors.muted_text; font.pixelSize: 11; elide: Text.ElideRight }
                }
            }
        }
    }

    Connections {
        target: applicationCatalog
        function onLaunchFailed(message) { status.text = message }
    }
}
