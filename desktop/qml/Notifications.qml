import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 760
    height: 680
    minimumWidth: 560
    minimumHeight: 440
    visible: true
    title: "LEOS — Notifications"
    property var themeColors: leosTheme.themePalette
    color: themeColors.background
    property color cyan: themeColors.accent_primary_text
    property color magenta: themeColors.accent_secondary_text
    property color accentA: themeColors.accent_primary
    property color accentB: themeColors.accent_secondary
    property color muted: themeColors.muted_text

    Rectangle {
        anchors.fill: parent
        color: window.color
        Rectangle {
            width: 500
            height: 500
            radius: 250
            x: parent.width - width * 0.54
            y: -height * 0.48
            color: window.themeColors.accent_primary
            opacity: 0.035
        }
        Rectangle {
            width: 420
            height: 420
            radius: 210
            x: -width * 0.5
            y: parent.height - height * 0.5
            color: window.themeColors.accent_secondary
            opacity: 0.025
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: window.width < 640 ? 16 : 26
        spacing: window.width < 640 ? 12 : 16

        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                spacing: 3
                Label { text: "LEOS"; color: window.themeColors.text; font.pixelSize: 26; font.weight: Font.Black; font.letterSpacing: 5 }
                Label { text: "CENTRE DE NOTIFICATIONS"; color: window.cyan; font.pixelSize: 12; font.letterSpacing: 2 }
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                radius: 10
                color: window.themeColors.surface_elevated
                border.color: window.themeColors.border
                implicitWidth: 126
                implicitHeight: 36
                Accessible.role: Accessible.Grouping
                Accessible.name: notificationModel.unreadCount + " notifications non lues"
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 7
                    Rectangle {
                        Layout.preferredWidth: 6
                        Layout.preferredHeight: 6
                        radius: 3
                        color: notificationModel.unreadCount > 0 ? window.accentA : window.muted
                    }
                    Label {
                        Layout.fillWidth: true
                        text: notificationModel.unreadCount + " NON LUES"
                        color: window.themeColors.text
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        font.letterSpacing: 0.65
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Button {
                id: markAllReadButton
                text: "TOUT MARQUER COMME LU"
                onClicked: notificationModel.markAllRead()
                background: Rectangle {
                    radius: 9
                    color: markAllReadButton.down || markAllReadButton.hovered || markAllReadButton.activeFocus
                           ? window.themeColors.surface_elevated : window.themeColors.surface
                    border.width: markAllReadButton.activeFocus ? 2 : 1
                    border.color: markAllReadButton.activeFocus ? window.accentA
                                  : markAllReadButton.hovered ? window.accentB : window.themeColors.border
                }
                contentItem: Label {
                    text: markAllReadButton.text
                    color: window.themeColors.text
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
            Button {
                id: clearAllButton
                text: "TOUT EFFACER"
                onClicked: confirmClear.open()
                background: Rectangle {
                    radius: 9
                    color: clearAllButton.down || clearAllButton.hovered || clearAllButton.activeFocus
                           ? window.themeColors.surface_elevated : window.themeColors.surface
                    border.width: clearAllButton.activeFocus ? 2 : 1
                    border.color: clearAllButton.activeFocus ? window.accentB
                                  : clearAllButton.hovered ? window.accentA : window.themeColors.border
                }
                contentItem: Label {
                    text: clearAllButton.text
                    color: window.themeColors.text
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
            Item { Layout.fillWidth: true }
            Button {
                id: refreshNotificationsButton
                text: "ACTUALISER"
                onClicked: notificationModel.refresh()
                background: Rectangle {
                    radius: 9
                    color: refreshNotificationsButton.down || refreshNotificationsButton.hovered || refreshNotificationsButton.activeFocus
                           ? window.themeColors.surface_elevated : window.themeColors.surface
                    border.width: refreshNotificationsButton.activeFocus ? 2 : 1
                    border.color: refreshNotificationsButton.activeFocus ? window.accentA
                                  : refreshNotificationsButton.hovered ? window.accentB : window.themeColors.border
                }
                contentItem: Label {
                    text: refreshNotificationsButton.text
                    color: window.themeColors.text
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 16
            color: window.themeColors.surface
            border.color: window.themeColors.border
            ListView {
                id: list
                anchors.fill: parent
                anchors.margins: 12
                clip: true
                spacing: 9
                model: notificationModel
                delegate: Rectangle {
                    required property string notificationId
                    required property string title
                    required property string body
                    required property string level
                    required property string createdAt
                    required property bool isRead
                    width: list.width
                    height: content.implicitHeight + 22
                    radius: 13
                    clip: true
                    color: isRead ? window.themeColors.surface : window.themeColors.surface_elevated
                    border.width: isRead ? 1 : 1.5
                    border.color: isRead ? window.themeColors.border : window.accentA
                    Rectangle {
                        anchors { left: parent.left; right: parent.right; top: parent.top }
                        height: 2
                        visible: !isRead
                        gradient: Gradient {
                            GradientStop { position: 0; color: window.accentA }
                            GradientStop { position: 1; color: window.accentB }
                        }
                    }
                    RowLayout {
                        id: content
                        anchors.fill: parent
                        anchors.margins: 11
                        spacing: 10
                        Rectangle {
                            Layout.preferredWidth: 3
                            Layout.fillHeight: true
                            radius: 2
                            color: level === "error" ? window.themeColors.semantic_critical
                                 : level === "warning" ? window.themeColors.semantic_warning
                                 : level === "success" ? window.themeColors.semantic_healthy
                                 : window.accentB
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Label {
                                    text: title
                                    color: window.themeColors.text
                                    font.pixelSize: 13
                                    font.weight: Font.DemiBold
                                    Layout.fillWidth: true
                                    wrapMode: Text.Wrap
                                }
                                Rectangle {
                                    visible: !isRead
                                    implicitWidth: 64
                                    implicitHeight: 20
                                    radius: 10
                                    color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.13)
                                    border.color: window.accentA
                                    Label {
                                        anchors.centerIn: parent
                                        text: "NON LUE"
                                        color: window.themeColors.text
                                        font.pixelSize: 10
                                        font.weight: Font.Bold
                                        font.letterSpacing: 0.6
                                    }
                                }
                            }
                            Label { text: body; color: window.muted; font.pixelSize: 13; Layout.fillWidth: true; wrapMode: Text.Wrap; visible: body.length > 0 }
                            Label { text: createdAt; color: window.themeColors.muted_text; font.pixelSize: 11; Layout.fillWidth: true; elide: Text.ElideMiddle }
                        }
                        ColumnLayout {
                            ToolButton {
                                id: markNotificationReadButton
                                text: isRead ? "✓" : "○"
                                Accessible.name: "Marquer cette notification comme lue"
                                Accessible.description: "Conserver l'événement dans l'historique et le signaler comme lu."
                                onClicked: notificationModel.markRead(notificationId)
                                background: Rectangle {
                                    radius: 7
                                    color: markNotificationReadButton.down || markNotificationReadButton.hovered || markNotificationReadButton.activeFocus
                                           ? window.themeColors.surface_elevated : "transparent"
                                    border.width: markNotificationReadButton.activeFocus ? 1 : 0
                                    border.color: window.accentA
                                }
                                contentItem: Label {
                                    text: markNotificationReadButton.text
                                    color: window.accentA
                                    font.pixelSize: 17
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                            ToolButton {
                                id: dismissNotificationButton
                                text: "×"
                                Accessible.name: "Supprimer cette notification"
                                Accessible.description: "Retirer cet événement de l'historique local LEOS."
                                onClicked: notificationModel.dismiss(notificationId)
                                background: Rectangle {
                                    radius: 7
                                    color: dismissNotificationButton.down || dismissNotificationButton.hovered || dismissNotificationButton.activeFocus
                                           ? window.themeColors.surface_elevated : "transparent"
                                    border.width: dismissNotificationButton.activeFocus ? 1 : 0
                                    border.color: window.accentB
                                }
                                contentItem: Label {
                                    text: dismissNotificationButton.text
                                    color: window.accentB
                                    font.pixelSize: 18
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                        }
                    }
                }
                ColumnLayout {
                    anchors.centerIn: parent
                    width: Math.max(220, parent.width - 56)
                    visible: list.count === 0
                    spacing: 10
                    Accessible.role: Accessible.Grouping
                    Accessible.name: "Aucune notification LEOS"

                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.preferredWidth: 58
                        Layout.preferredHeight: 58
                        radius: 29
                        color: window.themeColors.surface_elevated
                        border.color: window.themeColors.border
                        Label {
                            anchors.centerIn: parent
                            text: "✓"
                            color: window.cyan
                            font.pixelSize: 25
                            font.weight: Font.DemiBold
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "TOUT EST CALME"
                        color: window.themeColors.text
                        font.pixelSize: 13
                        font.weight: Font.Bold
                        font.letterSpacing: 1.5
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Label {
                        Layout.fillWidth: true
                        text: "Aucune notification LEOS pour le moment."
                        color: window.muted
                        font.pixelSize: 13
                        wrapMode: Text.WordWrap
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
        }
        Label {
            Layout.fillWidth: true
            text: "Les notifications système KDE restent gérées par Plasma. Cet espace conserve les événements émis par les composants LEOS."
            color: window.themeColors.muted_text
            font.pixelSize: 12
            wrapMode: Text.WordWrap
        }
    }

    Dialog {
        id: confirmClear
        title: "Effacer les notifications ?"
        modal: true
        standardButtons: Dialog.Yes | Dialog.No
        onAccepted: notificationModel.clearAll()
        Label { text: "Cette action supprimera tout l'historique local des notifications LEOS."; wrapMode: Text.WordWrap }
    }
}
