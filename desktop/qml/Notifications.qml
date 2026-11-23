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
        color: "transparent"
        Rectangle {
            width: 420; height: 420; radius: 210
            x: parent.width - 220; y: -230
            color: window.accentA; opacity: 0.06
        }
        Rectangle {
            width: 340; height: 340; radius: 170
            x: -190; y: parent.height - 180
            color: window.accentB; opacity: 0.05
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 26
        spacing: 16

        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                spacing: 6
                Label { text: "LEOS"; color: window.themeColors.text; font.pixelSize: 27; font.weight: Font.Black; font.letterSpacing: 5 }
                Rectangle {
                    Layout.preferredWidth: 76
                    Layout.preferredHeight: 2
                    radius: 1
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0.0; color: window.accentA }
                        GradientStop { position: 1.0; color: window.accentB }
                    }
                }
                Label { text: "CENTRE DE NOTIFICATIONS"; color: window.cyan; font.pixelSize: 10; font.letterSpacing: 2 }
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                radius: 11
                color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.09)
                border.color: window.themeColors.border
                implicitWidth: 104
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
            color: window.themeColors.surface
            border.color: window.themeColors.border
            ListView {
                id: list
                anchors.fill: parent
                anchors.margins: 12
                clip: true
                spacing: 11
                model: notificationModel
                delegate: Rectangle {
                    required property string notificationId
                    required property string title
                    required property string body
                    required property string level
                    required property string createdAt
                    required property bool isRead
                    width: list.width
                    height: content.implicitHeight + 26
                    radius: 14
                    color: isRead ? window.themeColors.surface : window.themeColors.surface_elevated
                    border.width: isRead ? 1 : 2
                    border.color: isRead ? window.themeColors.border : window.accentA
                    Behavior on border.color { ColorAnimation { duration: 150 } }
                    RowLayout {
                        id: content
                        anchors.fill: parent
                        anchors.margins: 13
                        spacing: 12
                        Rectangle {
                            Layout.preferredWidth: 3
                            Layout.fillHeight: true
                            radius: 2
                            color: level === "error" ? "#FF5577" : level === "warning" ? "#FFB84D" : level === "success" ? window.accentA : window.accentB
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Label { text: title; color: window.themeColors.text; font.pixelSize: 14; font.weight: Font.DemiBold; Layout.fillWidth: true; wrapMode: Text.Wrap }
                            Label { text: body; color: window.muted; font.pixelSize: 12; Layout.fillWidth: true; wrapMode: Text.Wrap; visible: body.length > 0 }
                            Label { text: createdAt; color: window.themeColors.muted_text; font.pixelSize: 10; Layout.fillWidth: true; elide: Text.ElideMiddle }
                        }
                        ColumnLayout {
                            ToolButton {
                                id: markNotificationReadButton
                                text: isRead ? "✓" : "○"
                                onClicked: notificationModel.markRead(notificationId)
                                contentItem: Label { text: markNotificationReadButton.text; color: window.accentA; font.pixelSize: 17 }
                            }
                            ToolButton {
                                id: dismissNotificationButton
                                text: "×"
                                onClicked: notificationModel.dismiss(notificationId)
                                contentItem: Label { text: dismissNotificationButton.text; color: window.accentB; font.pixelSize: 18 }
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
            color: window.themeColors.muted_text
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
