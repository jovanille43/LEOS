import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1440
    height: 900
    visible: true
    visibility: Window.FullScreen
    title: "LEOS Gaming"

    color: "#08090d"

    property color accentCyan: "#00d9ff"
    property color accentMagenta: "#e33bff"
    property color panelColor: "#11141c"
    property color mutedText: "#8d96a8"

    Rectangle {
        anchors.fill: parent
        color: window.color

        Rectangle {
            width: 620
            height: 620
            radius: 310
            x: parent.width - width * 0.55
            y: -height * 0.48
            color: "#102331"
            opacity: 0.22
        }

        Rectangle {
            width: 520
            height: 520
            radius: 260
            x: -width * 0.5
            y: parent.height - height * 0.45
            color: "#2a1232"
            opacity: 0.16
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 36
            spacing: 28

            RowLayout {
                Layout.fillWidth: true
                spacing: 20

                ColumnLayout {
                    spacing: 2
                    Label {
                        text: "LEOS"
                        color: "white"
                        font.pixelSize: 28
                        font.weight: Font.Black
                        font.letterSpacing: 5
                    }
                    Label {
                        text: "GAMING MODE"
                        color: window.accentCyan
                        font.pixelSize: 10
                        font.letterSpacing: 3
                    }
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: "PANNEAU RAPIDE  ☰"
                    onClicked: quickPanel.visible = !quickPanel.visible
                    background: Rectangle {
                        radius: 10
                        color: parent.down ? "#26313e" : "#171d28"
                        border.color: "#344052"
                    }
                    contentItem: Label {
                        text: parent.text
                        color: "white"
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }

            Rectangle {
                id: quickPanel
                Layout.fillWidth: true
                visible: false
                height: 76
                radius: 14
                color: "#e611141c"
                border.color: "#354052"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 28
                    Repeater {
                        model: ["Performances", "Audio", "Manettes", "Captures", "Paramètres", "Alimentation"]
                        delegate: Label {
                            required property string modelData
                            text: modelData
                            color: "white"
                            font.pixelSize: 13
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 30

                ColumnLayout {
                    Layout.preferredWidth: 190
                    Layout.fillHeight: true
                    spacing: 12

                    Label {
                        text: "BIBLIOTHÈQUE"
                        color: window.mutedText
                        font.pixelSize: 11
                        font.letterSpacing: 2
                    }

                    Repeater {
                        model: ["Accueil", "PC Gaming", "Nintendo", "PlayStation", "SEGA", "Arcade", "Favoris", "Récemment joués"]
                        delegate: Button {
                            required property string modelData
                            Layout.fillWidth: true
                            text: modelData
                            background: Rectangle {
                                radius: 9
                                color: modelData === "Accueil" ? "#202b38" : "transparent"
                                border.color: modelData === "Accueil" ? window.accentCyan : "transparent"
                            }
                            contentItem: Label {
                                text: parent.text
                                color: "white"
                                leftPadding: 10
                                verticalAlignment: Text.AlignVCenter
                                font.pixelSize: 13
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                    Label {
                        text: "UNE EXPÉRIENCE. DEUX MODES."
                        color: "#626c7e"
                        font.pixelSize: 9
                        wrapMode: Text.WordWrap
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 22
                    color: "#10141d"
                    border.color: "#252d3b"

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 14

                        Label {
                            text: "BIENVENUE DANS LEOS"
                            color: "white"
                            font.pixelSize: 26
                            font.weight: Font.Bold
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Label {
                            text: "Votre bibliothèque de jeux prendra place ici."
                            color: window.mutedText
                            font.pixelSize: 14
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Label {
                            text: "PREMIER SQUELETTE DE L’INTERFACE"
                            color: window.accentCyan
                            font.pixelSize: 10
                            font.letterSpacing: 2
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }
            }
        }
    }
}
