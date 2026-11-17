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
    property color colorA: themeColors.accent_primary
    property color colorB: themeColors.accent_secondary
    property color colorAText: themeColors.accent_primary_text
    property color colorBText: themeColors.accent_secondary_text
    property color muted: themeColors.muted_text

    function accentSurface(accentColor, strength) {
        const base = Qt.color(themeColors.surface)
        const amount = Math.max(0.0, Math.min(1.0, strength))
        return Qt.rgba(
            base.r * (1.0 - amount) + accentColor.r * amount,
            base.g * (1.0 - amount) + accentColor.g * amount,
            base.b * (1.0 - amount) + accentColor.b * amount,
            1.0
        )
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 26
        spacing: 16

        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                spacing: 3
                Label { text: "LEOS"; color: window.themeColors.text; font.pixelSize: 26; font.weight: Font.Black; font.letterSpacing: 5 }
                Label { text: "CENTRE DE NOTIFICATIONS"; color: window.colorAText; font.pixelSize: 10; font.letterSpacing: 2 }
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                radius: 12
                color: window.themeColors.surface_elevated
                border.color: window.colorA
                implicitWidth: 90
                implicitHeight: 34
                Label {
                    anchors.centerIn: parent
                    text: notificationModel.unreadCount + " non lues"
                    color: window.colorAText
                    font.pixelSize: 11
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Button { text: "TOUT MARQUER COMME LU"; onClicked: notificationModel.markAllRead() }
            Button { text: "TOUT EFFACER"; onClicked: confirmClear.open() }
            Item { Layout.fillWidth: true }
            Button { text: "ACTUALISER"; onClicked: notificationModel.refresh() }
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
                    radius: 11
                    color: isRead ? window.themeColors.surface_elevated : window.accentSurface(window.colorA, 0.10)
                    border.width: isRead ? 1 : 2
                    border.color: isRead ? window.themeColors.border : window.colorA
                    RowLayout {
                        id: content
                        anchors.fill: parent
                        anchors.margins: 11
                        spacing: 10
                        Rectangle {
                            Layout.preferredWidth: 3
                            Layout.fillHeight: true
                            radius: 2
                            color: level === "error" ? "#FF5577" : level === "warning" ? "#FFB84D" : level === "success" ? window.colorA : window.colorB
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Label { text: title; color: window.themeColors.text; font.pixelSize: 13; font.weight: Font.DemiBold; Layout.fillWidth: true; wrapMode: Text.Wrap }
                            Label { text: body; color: window.muted; font.pixelSize: 11; Layout.fillWidth: true; wrapMode: Text.Wrap; visible: body.length > 0 }
                            Label { text: createdAt; color: window.muted; font.pixelSize: 9; Layout.fillWidth: true; elide: Text.ElideMiddle }
                        }
                        ColumnLayout {
                            ToolButton {
                                id: markNotificationReadButton
                                text: isRead ? "✓" : "○"
                                onClicked: notificationModel.markRead(notificationId)
                                contentItem: Label { text: markNotificationReadButton.text; color: window.colorAText; font.pixelSize: 17 }
                            }
                            ToolButton {
                                id: dismissNotificationButton
                                text: "×"
                                onClicked: notificationModel.dismiss(notificationId)
                                contentItem: Label { text: dismissNotificationButton.text; color: window.colorBText; font.pixelSize: 18 }
                            }
                        }
                    }
                }
                Label {
                    anchors.centerIn: parent
                    visible: list.count === 0
                    text: "Aucune notification LEOS pour le moment."
                    color: window.muted
                }
            }
        }
        Label {
            Layout.fillWidth: true
            text: "Les notifications système KDE restent gérées par Plasma. Cet espace conserve les événements émis par les composants LEOS."
            color: window.muted
            font.pixelSize: 10
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
