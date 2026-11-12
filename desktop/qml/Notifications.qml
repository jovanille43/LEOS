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
    color: "#090B10"
    property color cyan: "#00D9FF"
    property color magenta: "#E33BFF"
    property color muted: "#929BAD"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 26
        spacing: 16

        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                spacing: 3
                Label { text: "LEOS"; color: "white"; font.pixelSize: 26; font.weight: Font.Black; font.letterSpacing: 5 }
                Label { text: "CENTRE DE NOTIFICATIONS"; color: window.cyan; font.pixelSize: 10; font.letterSpacing: 2 }
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                radius: 12
                color: "#14202B"
                border.color: "#245064"
                implicitWidth: 90
                implicitHeight: 34
                Label {
                    anchors.centerIn: parent
                    text: notificationModel.unreadCount + " non lues"
                    color: window.cyan
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
            color: "#10151E"
            border.color: "#263140"
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
                    color: isRead ? "#141B25" : "#172330"
                    border.width: isRead ? 1 : 2
                    border.color: isRead ? "#2B3544" : window.cyan
                    RowLayout {
                        id: content
                        anchors.fill: parent
                        anchors.margins: 11
                        spacing: 10
                        Rectangle {
                            Layout.preferredWidth: 3
                            Layout.fillHeight: true
                            radius: 2
                            color: level === "error" ? "#FF5577" : level === "warning" ? "#FFB84D" : level === "success" ? window.cyan : window.magenta
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Label { text: title; color: "white"; font.pixelSize: 13; font.weight: Font.DemiBold; Layout.fillWidth: true; wrapMode: Text.Wrap }
                            Label { text: body; color: window.muted; font.pixelSize: 11; Layout.fillWidth: true; wrapMode: Text.Wrap; visible: body.length > 0 }
                            Label { text: createdAt; color: "#657184"; font.pixelSize: 9; Layout.fillWidth: true; elide: Text.ElideMiddle }
                        }
                        ColumnLayout {
                            ToolButton {
                                id: markNotificationReadButton
                                text: isRead ? "✓" : "○"
                                onClicked: notificationModel.markRead(notificationId)
                                contentItem: Label { text: markNotificationReadButton.text; color: window.cyan; font.pixelSize: 17 }
                            }
                            ToolButton {
                                id: dismissNotificationButton
                                text: "×"
                                onClicked: notificationModel.dismiss(notificationId)
                                contentItem: Label { text: dismissNotificationButton.text; color: window.magenta; font.pixelSize: 18 }
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
            color: "#657184"
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
