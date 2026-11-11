import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1280
    height: 760
    visible: true
    visibility: Window.FullScreen
    title: "LEOS — Choix du mode"
    color: "#07080c"
    focus: true

    property color cyan: "#00d9ff"
    property color magenta: "#e33bff"
    property color muted: "#929bad"
    property date currentDate: new Date()

    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: window.currentDate = new Date()
    }

    Rectangle {
        anchors.fill: parent
        color: window.color

        Rectangle {
            width: 650; height: 650; radius: 325
            x: parent.width * 0.55; y: -height * 0.55
            color: "#102b3a"; opacity: 0.18
        }
        Rectangle {
            width: 560; height: 560; radius: 280
            x: -width * 0.4; y: parent.height * 0.55
            color: "#321437"; opacity: 0.15
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 48
            spacing: 20

            ColumnLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 5

                Label {
                    text: "LEOS"
                    color: "white"
                    font.pixelSize: 39
                    font.weight: Font.Black
                    font.letterSpacing: 9
                    Layout.alignment: Qt.AlignHCenter
                }
                Label {
                    text: "CHOISISSEZ VOTRE EXPÉRIENCE"
                    color: window.muted
                    font.pixelSize: 11
                    font.letterSpacing: 3
                    Layout.alignment: Qt.AlignHCenter
                }
                Label {
                    text: window.currentDate.toLocaleTimeString(Qt.locale("fr_FR"), "HH:mm")
                    color: "white"
                    font.pixelSize: 48
                    font.weight: Font.Light
                    font.letterSpacing: 2
                    Layout.alignment: Qt.AlignHCenter
                    topPadding: 5
                }
                Label {
                    text: window.currentDate.toLocaleDateString(Qt.locale("fr_FR"), "dddd d MMMM yyyy")
                    color: window.muted
                    font.pixelSize: 13
                    Layout.alignment: Qt.AlignHCenter
                }
                Label {
                    text: "DERNIÈRE SESSION : " +
                          (modeManager.lastMode === "gaming" ? "GAMING MODE" : "DESKTOP MODE")
                    color: window.cyan
                    font.pixelSize: 10
                    font.letterSpacing: 1.5
                    Layout.alignment: Qt.AlignHCenter
                    topPadding: 4
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 24

                Button {
                    id: desktopCard
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    focus: true
                    onClicked: modeManager.requestMode("desktop")
                    background: Rectangle {
                        radius: 22
                        color: desktopCard.down ? "#1a2630" : "#111720"
                        border.width: desktopCard.activeFocus ? 2 : 1
                        border.color: desktopCard.activeFocus ? window.cyan : "#303a49"
                    }
                    contentItem: ColumnLayout {
                        spacing: 15
                        Item { Layout.fillHeight: true }
                        Image {
                            source: "../../branding/desktop-logo.png"
                            fillMode: Image.PreserveAspectFit
                            Layout.alignment: Qt.AlignHCenter
                            Layout.preferredWidth: 185
                            Layout.preferredHeight: 175
                            visible: status === Image.Ready
                        }
                        Label {
                            text: "LEOS DESKTOP"
                            color: "white"
                            font.pixelSize: 23
                            font.weight: Font.Bold
                            font.letterSpacing: 2
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Label {
                            text: "Bureau, création et quotidien"
                            color: window.muted
                            font.pixelSize: 13
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Label {
                            text: "Une expérience KDE personnalisée"
                            color: "#687487"
                            font.pixelSize: 10
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Item { Layout.fillHeight: true }
                    }
                }

                Button {
                    id: gamingCard
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    onClicked: transitionDialog.open()
                    background: Rectangle {
                        radius: 22
                        color: gamingCard.down ? "#25172a" : "#15121d"
                        border.width: gamingCard.activeFocus ? 2 : 1
                        border.color: gamingCard.activeFocus ? window.magenta : "#3a2b43"
                    }
                    contentItem: ColumnLayout {
                        spacing: 15
                        Item { Layout.fillHeight: true }
                        Image {
                            source: "../../branding/gaming-logo.png"
                            fillMode: Image.PreserveAspectFit
                            Layout.alignment: Qt.AlignHCenter
                            Layout.preferredWidth: 185
                            Layout.preferredHeight: 175
                            visible: status === Image.Ready
                        }
                        Label {
                            text: "LEOS GAMING"
                            color: "white"
                            font.pixelSize: 23
                            font.weight: Font.Bold
                            font.letterSpacing: 2
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Label {
                            text: "Bibliothèque et expérience manette"
                            color: window.muted
                            font.pixelSize: 13
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Label {
                            text: "Vos jeux et lanceurs réunis au même endroit"
                            color: "#687487"
                            font.pixelSize: 10
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Item { Layout.fillHeight: true }
                    }
                }
            }

            Label {
                text: modeManager.status
                color: window.magenta
                font.pixelSize: 12
                Layout.alignment: Qt.AlignHCenter
            }
            Label {
                text: "Bazzite KDE · Une seule session · Aucune application ne sera fermée automatiquement"
                color: "#667184"
                font.pixelSize: 10
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }

    Dialog {
        id: transitionDialog
        title: "Avant de passer en Gaming"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Cancel
        width: 470

        ColumnLayout {
            width: parent.width
            spacing: 14
            Label {
                text: "Les applications actuellement ouvertes resteront en arrière-plan. Aucune application ne sera fermée automatiquement."
                color: "white"
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Button {
                text: "CONTINUER VERS GAMING"
                Layout.fillWidth: true
                onClicked: {
                    transitionDialog.close()
                    modeManager.requestMode("gaming")
                }
                background: Rectangle { radius: 9; color: "#17313d"; border.color: window.cyan }
                contentItem: Label {
                    text: parent.text
                    color: "white"
                    font.weight: Font.Bold
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }

    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_G) {
            transitionDialog.open()
            event.accepted = true
        } else if (event.key === Qt.Key_D) {
            modeManager.requestMode("desktop")
            event.accepted = true
        } else if (event.key === Qt.Key_Left || event.key === Qt.Key_Right) {
            if (desktopCard.activeFocus)
                gamingCard.forceActiveFocus()
            else
                desktopCard.forceActiveFocus()
            event.accepted = true
        } else if (event.key === Qt.Key_Escape && transitionDialog.visible) {
            transitionDialog.close()
            event.accepted = true
        }
    }
}
