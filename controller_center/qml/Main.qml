import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1040
    height: 760
    minimumWidth: 760
    minimumHeight: 600
    visible: true
    title: "LEOS — Centre des manettes"
    color: "#090b10"

    property color cyan: "#00d9ff"
    property color magenta: "#e33bff"
    property color muted: "#909aac"
    property color panel: "#121720"
    property color line: "#293342"

    Rectangle {
        anchors.fill: parent
        color: window.color

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 32
            spacing: 20

            RowLayout {
                Layout.fillWidth: true
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
                        text: "CENTRE DES MANETTES"
                        color: window.cyan
                        font.pixelSize: 10
                        font.letterSpacing: 3
                    }
                }
                Item { Layout.fillWidth: true }
                Label {
                    text: "CONFIGURATION LOCALE"
                    color: window.muted
                    font.pixelSize: 10
                    font.letterSpacing: 2
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 112
                radius: 15
                color: window.panel
                border.color: window.line

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 16
                    Rectangle {
                        width: 54
                        height: 54
                        radius: 14
                        color: "#17303b"
                        border.color: window.cyan
                        Label {
                            anchors.centerIn: parent
                            text: "⌘"
                            color: window.cyan
                            font.pixelSize: 28
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 5
                        Label {
                            text: controllerCenter.selectedDeviceName
                            color: "white"
                            font.pixelSize: 17
                            font.weight: Font.DemiBold
                        }
                        Label {
                            text: controllerCenter.statusText
                            color: window.muted
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                        }
                    }
                    Button {
                        text: "ACTUALISER"
                        onClicked: controllerCenter.refreshDevices()
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 18

                ColumnLayout {
                    Layout.preferredWidth: 285
                    Layout.fillHeight: true
                    spacing: 14

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 158
                        radius: 14
                        color: window.panel
                        border.color: window.line
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 11
                            Label {
                                text: "MANETTE"
                                color: window.cyan
                                font.pixelSize: 11
                                font.letterSpacing: 2
                            }
                            ComboBox {
                                id: deviceBox
                                Layout.fillWidth: true
                                model: controllerCenter.deviceNames
                                currentIndex: controllerCenter.selectedIndex
                                onActivated: controllerCenter.selectDevice(currentIndex)
                            }
                            Label {
                                text: controllerCenter.backendAvailable
                                    ? "Détection Linux active"
                                    : "Backend evdev non installé"
                                color: controllerCenter.backendAvailable ? "#8bd8a8" : window.magenta
                                font.pixelSize: 11
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: 14
                        color: window.panel
                        border.color: window.line
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            spacing: 12
                            Label {
                                text: "PROFIL LEOS"
                                color: window.cyan
                                font.pixelSize: 11
                                font.letterSpacing: 2
                            }
                            ComboBox {
                                id: profileBox
                                Layout.fillWidth: true
                                model: ["Automatique", "Standard", "Xbox", "PlayStation", "Nintendo", "Personnalisé"]
                                currentIndex: {
                                    const names = ["Automatique", "Standard", "Xbox", "PlayStation", "Nintendo", "Personnalisé"]
                                    return Math.max(0, names.indexOf(controllerCenter.profileName))
                                }
                                onActivated: controllerCenter.setProfile(currentText)
                            }
                            Label {
                                Layout.fillWidth: true
                                text: controllerCenter.profileHint
                                color: window.muted
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                            }
                            Label {
                                text: "Zone morte des sticks"
                                color: "white"
                                font.pixelSize: 12
                            }
                            Slider {
                                id: deadzoneSlider
                                Layout.fillWidth: true
                                from: 0
                                to: 40
                                stepSize: 1
                                value: controllerCenter.deadzone
                                onMoved: controllerCenter.setDeadzone(Math.round(value))
                            }
                            Label {
                                text: Math.round(deadzoneSlider.value) + " %"
                                color: window.cyan
                                font.pixelSize: 13
                            }
                            Item { Layout.fillHeight: true }
                            Button {
                                Layout.fillWidth: true
                                text: "ENREGISTRER LE NEUTRE"
                                enabled: controllerCenter.selectedIndex >= 0
                                onClicked: controllerCenter.saveStickCenter()
                            }
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 14

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: 14
                        color: window.panel
                        border.color: window.line
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 20
                            spacing: 12
                            Label {
                                text: "TEST DES COMMANDES"
                                color: window.cyan
                                font.pixelSize: 11
                                font.letterSpacing: 2
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 104
                                radius: 10
                                color: "#0b1119"
                                border.color: "#263543"
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 14
                                    spacing: 7
                                    Label {
                                        text: "DERNIÈRE ENTRÉE"
                                        color: window.muted
                                        font.pixelSize: 9
                                        font.letterSpacing: 2
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: controllerCenter.lastEventText
                                        color: "white"
                                        font.pixelSize: 16
                                        wrapMode: Text.WordWrap
                                    }
                                }
                            }
                            Label {
                                text: "BOUTONS MAINTENUS"
                                color: window.muted
                                font.pixelSize: 10
                                font.letterSpacing: 2
                            }
                            Label {
                                Layout.fillWidth: true
                                text: controllerCenter.buttonsText
                                color: "white"
                                font.pixelSize: 13
                                wrapMode: Text.WordWrap
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                height: 1
                                color: window.line
                            }
                            Label {
                                text: "AXES ANALOGIQUES"
                                color: window.muted
                                font.pixelSize: 10
                                font.letterSpacing: 2
                            }
                            Label {
                                Layout.fillWidth: true
                                text: controllerCenter.axesText
                                color: "white"
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                            Item { Layout.fillHeight: true }
                            Label {
                                Layout.fillWidth: true
                                text: "Les profils et calibrages sont enregistrés dans ton compte Linux. Ils ne remappent pas encore les commandes dans les jeux : Steam et les lanceurs conservent leur configuration."
                                color: window.muted
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                text: "LEOS · Les périphériques sont surveillés en lecture seule ; aucune règle système ni commande de jeu n'est modifiée."
                color: "#657184"
                font.pixelSize: 10
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
}
