import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 760
    height: 680
    minimumWidth: 620
    minimumHeight: 500
    visible: true
    title: "LEOS — Notifications"
    property var themeColors: leosTheme.themePalette
    color: themeColors.background

    property color cyan: themeColors.accent_primary_text
    property color magenta: themeColors.accent_secondary_text
    property color accentA: themeColors.accent_primary
    property color accentB: themeColors.accent_secondary
    property color muted: themeColors.muted_text

    function levelColor(level) {
        if (level === "error")
            return "#E47F89"
        if (level === "warning")
            return "#E2B875"
        if (level === "success")
            return window.accentA
        return window.accentB
    }

    function levelLabel(level) {
        if (level === "error")
            return "ERREUR"
        if (level === "warning")
            return "ATTENTION"
        if (level === "success")
            return "TERMINÉ"
        return "INFORMATION"
    }

    Rectangle {
        anchors.fill: parent
        color: window.color
        clip: true

        Rectangle {
            width: 440
            height: width
            radius: width / 2
            x: parent.width - 220
            y: -230
            color: window.accentA
            opacity: 0.045
        }
        Rectangle {
            width: 350
            height: width
            radius: width / 2
            x: -190
            y: parent.height - 180
            color: window.accentB
            opacity: 0.04
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 26
            spacing: 15

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 54
                spacing: 12

                Image {
                    id: notificationLogo
                    source: leosTheme.desktopLogoUrl
                    asynchronous: true
                    smooth: true
                    fillMode: Image.PreserveAspectFit
                    Layout.preferredWidth: 74
                    Layout.preferredHeight: 48
                    visible: status === Image.Ready
                }

                ColumnLayout {
                    spacing: 2
                    Label {
                        text: "LEOS"
                        color: window.themeColors.text
                        font.pixelSize: 26
                        font.weight: Font.Black
                        font.letterSpacing: 5
                        visible: notificationLogo.status !== Image.Ready
                    }
                    Label {
                        text: "CENTRE DE NOTIFICATIONS"
                        color: window.cyan
                        font.pixelSize: 9
                        font.weight: Font.Bold
                        font.letterSpacing: 1.8
                    }
                    Label {
                        text: "L’activité de ton environnement, au même endroit."
                        color: window.muted
                        font.pixelSize: 10
                    }
                }

                Item { Layout.fillWidth: true }

                Rectangle {
                    radius: 11
                    color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.09)
                    border.color: window.themeColors.border
                    implicitWidth: unreadCountLabel.implicitWidth + 22
                    implicitHeight: 36
                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 7
                        Rectangle {
                            width: 7
                            height: 7
                            radius: 4
                            color: notificationModel.unreadCount > 0 ? window.accentA : window.muted
                        }
                        Label {
                            id: unreadCountLabel
                            text: notificationModel.unreadCount + " non lue(s)"
                            color: window.cyan
                            font.pixelSize: 10
                            font.weight: Font.DemiBold
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 2
                radius: 1
                opacity: 0.72
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: window.accentA }
                    GradientStop { position: 0.50; color: window.themeColors.border }
                    GradientStop { position: 1.0; color: window.accentB }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Button {
                    id: markAllReadButton
                    text: "TOUT MARQUER COMME LU"
                    onClicked: notificationModel.markAllRead()
                    implicitHeight: 38
                    background: Rectangle {
                        radius: 10
                        color: markAllReadButton.hovered || markAllReadButton.down
                               ? window.themeColors.surface_elevated : window.themeColors.surface
                        border.color: markAllReadButton.hovered ? window.accentA : window.themeColors.border
                    }
                    contentItem: Label {
                        text: markAllReadButton.text
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
                    id: clearAllButton
                    text: "TOUT EFFACER"
                    onClicked: confirmClear.open()
                    implicitHeight: 38
                    background: Rectangle {
                        radius: 10
                        color: clearAllButton.hovered || clearAllButton.down
                               ? window.themeColors.surface_elevated : "transparent"
                        border.color: window.themeColors.border
                    }
                    contentItem: Label {
                        text: clearAllButton.text
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

                Item { Layout.fillWidth: true }

                Button {
                    id: refreshNotificationsButton
                    text: "ACTUALISER"
                    onClicked: notificationModel.refresh()
                    implicitHeight: 38
                    background: Rectangle {
                        radius: 10
                        color: Qt.rgba(window.accentB.r, window.accentB.g, window.accentB.b, 0.08)
                        border.color: refreshNotificationsButton.hovered ? window.accentB : window.themeColors.border
                    }
                    contentItem: Label {
                        text: refreshNotificationsButton.text
                        color: window.themeColors.text
                        font.pixelSize: 9
                        font.weight: Font.DemiBold
                        letterSpacing: 0.8
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 13
                        rightPadding: 13
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
                    spacing: 10
                    model: notificationModel
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                    delegate: Rectangle {
                        required property string notificationId
                        required property string title
                        required property string body
                        required property string level
                        required property string createdAt
                        required property bool isRead

                        width: list.width
                        height: content.implicitHeight + 24
                        radius: 14
                        gradient: Gradient {
                            GradientStop {
                                position: 0.0
                                color: isRead ? window.themeColors.surface
                                    : Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.075)
                            }
                            GradientStop { position: 1.0; color: window.themeColors.surface }
                        }
                        border.width: isRead ? 1 : 1.5
                        border.color: isRead ? window.themeColors.border : window.accentA
                        Behavior on border.color { ColorAnimation { duration: 150 } }

                        RowLayout {
                            id: content
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 11

                            Rectangle {
                                Layout.preferredWidth: 38
                                Layout.preferredHeight: 38
                                radius: 11
                                color: Qt.rgba(window.levelColor(level).r,
                                               window.levelColor(level).g,
                                               window.levelColor(level).b, 0.12)
                                border.color: Qt.rgba(window.levelColor(level).r,
                                                      window.levelColor(level).g,
                                                      window.levelColor(level).b, 0.32)
                                Label {
                                    anchors.centerIn: parent
                                    text: level === "error" ? "!" : level === "warning" ? "△"
                                          : level === "success" ? "✓" : "i"
                                    color: window.levelColor(level)
                                    font.pixelSize: 17
                                    font.weight: Font.Bold
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 7
                                    Label {
                                        text: title
                                        color: window.themeColors.text
                                        font.pixelSize: 13
                                        font.weight: Font.DemiBold
                                        Layout.fillWidth: true
                                        wrapMode: Text.Wrap
                                    }
                                    Rectangle {
                                        radius: 6
                                        implicitWidth: levelBadge.implicitWidth + 12
                                        implicitHeight: 21
                                        color: Qt.rgba(window.levelColor(level).r,
                                                       window.levelColor(level).g,
                                                       window.levelColor(level).b, 0.09)
                                        Label {
                                            id: levelBadge
                                            anchors.centerIn: parent
                                            text: window.levelLabel(level)
                                            color: window.levelColor(level)
                                            font.pixelSize: 7
                                            font.weight: Font.Bold
                                            font.letterSpacing: 0.4
                                        }
                                    }
                                }

                                Label {
                                    text: body
                                    color: window.muted
                                    font.pixelSize: 11
                                    Layout.fillWidth: true
                                    wrapMode: Text.Wrap
                                    visible: body.length > 0
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 7
                                    Label {
                                        text: createdAt
                                        color: window.themeColors.muted_text
                                        font.pixelSize: 9
                                        Layout.fillWidth: true
                                        elide: Text.ElideMiddle
                                    }
                                    Label {
                                        text: isRead ? "LUE" : "NON LUE"
                                        color: isRead ? window.muted : window.cyan
                                        font.pixelSize: 8
                                        font.weight: Font.Bold
                                        font.letterSpacing: 0.8
                                    }
                                }
                            }

                            ColumnLayout {
                                spacing: 5
                                ToolButton {
                                    id: markNotificationReadButton
                                    implicitWidth: 34
                                    implicitHeight: 32
                                    text: isRead ? "✓" : "○"
                                    onClicked: notificationModel.markRead(notificationId)
                                    background: Rectangle {
                                        radius: 9
                                        color: markNotificationReadButton.hovered
                                               ? Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.12)
                                               : "transparent"
                                    }
                                    contentItem: Label {
                                        text: markNotificationReadButton.text
                                        color: window.accentA
                                        font.pixelSize: 16
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    ToolTip.visible: hovered
                                    ToolTip.text: isRead ? "Marquer comme lue" : "Marquer comme non lue"
                                }
                                ToolButton {
                                    id: dismissNotificationButton
                                    implicitWidth: 34
                                    implicitHeight: 32
                                    text: "×"
                                    onClicked: notificationModel.dismiss(notificationId)
                                    background: Rectangle {
                                        radius: 9
                                        color: dismissNotificationButton.hovered
                                               ? Qt.rgba(window.accentB.r, window.accentB.g, window.accentB.b, 0.12)
                                               : "transparent"
                                    }
                                    contentItem: Label {
                                        text: dismissNotificationButton.text
                                        color: window.accentB
                                        font.pixelSize: 18
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    ToolTip.visible: hovered
                                    ToolTip.text: "Supprimer cette notification"
                                }
                            }
                        }
                    }

                    ColumnLayout {
                        anchors.centerIn: parent
                        visible: list.count === 0
                        spacing: 8
                        Label {
                            text: "✓"
                            color: window.cyan
                            font.pixelSize: 30
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Label {
                            text: "Tout est calme."
                            color: window.themeColors.text
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Label {
                            text: "Aucune notification LEOS pour le moment."
                            color: window.muted
                            font.pixelSize: 10
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                radius: 10
                color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.045)
                border.color: window.themeColors.border
                implicitHeight: noteLabel.implicitHeight + 16
                Label {
                    id: noteLabel
                    anchors.fill: parent
                    anchors.margins: 9
                    text: "Les notifications système KDE restent gérées par Plasma. Cet espace conserve les événements émis par les composants LEOS."
                    color: window.themeColors.muted_text
                    font.pixelSize: 9
                    wrapMode: Text.WordWrap
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }

    Dialog {
        id: confirmClear
        title: "Effacer les notifications ?"
        modal: true
        standardButtons: Dialog.Yes | Dialog.No
        onAccepted: notificationModel.clearAll()
        background: Rectangle {
            radius: 15
            color: window.themeColors.surface
            border.color: window.themeColors.border
        }
        Label {
            text: "Cette action supprimera tout l'historique local des notifications LEOS."
            color: window.themeColors.text
            wrapMode: Text.WordWrap
        }
    }
}
