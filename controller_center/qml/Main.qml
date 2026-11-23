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
    property var themeColors: leosTheme.themePalette
    color: themeColors.background

    property color cyan: themeColors.accent_primary_text
    property color magenta: themeColors.accent_secondary_text
    property color accentA: themeColors.accent_primary
    property color accentB: themeColors.accent_secondary
    property color muted: themeColors.muted_text
    property color panel: themeColors.surface
    property color line: themeColors.border

    Rectangle {
        anchors.fill: parent
        color: window.color
        clip: true

        Rectangle {
            width: 500
            height: width
            radius: width / 2
            x: parent.width - width * 0.58
            y: -height * 0.62
            color: window.accentA
            opacity: 0.045
        }
        Rectangle {
            width: 420
            height: width
            radius: width / 2
            x: -width * 0.52
            y: parent.height * 0.62
            color: window.accentB
            opacity: 0.04
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 32
            spacing: 20

            RowLayout {
                Layout.fillWidth: true
                RowLayout {
                    spacing: 11
                    Image {
                        id: controllerCenterLogo
                        source: leosTheme.desktopLogoUrl
                        asynchronous: true
                        smooth: true
                        fillMode: Image.PreserveAspectFit
                        Layout.preferredWidth: 82
                        Layout.preferredHeight: 50
                        visible: status === Image.Ready
                    }
                    ColumnLayout {
                        spacing: 2
                        Label {
                            text: "LEOS"
                            color: window.themeColors.text
                            font.pixelSize: 27
                            font.weight: Font.Black
                            font.letterSpacing: 5
                            visible: controllerCenterLogo.status !== Image.Ready
                        }
                        Label {
                            text: "CENTRE DES MANETTES"
                            color: window.cyan
                            font.pixelSize: 10
                            font.weight: Font.Bold
                            font.letterSpacing: 2.6
                        }
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
                Layout.preferredHeight: 2
                radius: 1
                opacity: 0.72
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: window.accentA }
                    GradientStop { position: 0.52; color: window.themeColors.border }
                    GradientStop { position: 1.0; color: window.accentB }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 116
                radius: 17
                gradient: Gradient {
                    GradientStop {
                        position: 0.0
                        color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.07)
                    }
                    GradientStop { position: 1.0; color: window.panel }
                }
                border.color: window.line

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 16
                    Rectangle {
                        Layout.preferredWidth: 54
                        Layout.preferredHeight: 54
                        radius: 16
                        gradient: Gradient {
                            GradientStop {
                                position: 0.0
                                color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.22)
                            }
                            GradientStop {
                                position: 1.0
                                color: Qt.rgba(window.accentB.r, window.accentB.g, window.accentB.b, 0.12)
                            }
                        }
                        border.color: window.accentA
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
                        radius: 16
                        gradient: Gradient {
                            GradientStop {
                                position: 0.0
                                color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.045)
                            }
                            GradientStop { position: 1.0; color: window.panel }
                        }
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
                        radius: 16
                        gradient: Gradient {
                            GradientStop {
                                position: 0.0
                                color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.045)
                            }
                            GradientStop { position: 1.0; color: window.panel }
                        }
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
                        radius: 16
                        gradient: Gradient {
                            GradientStop {
                                position: 0.0
                                color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.045)
                            }
                            GradientStop { position: 1.0; color: window.panel }
                        }
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
                                Layout.preferredHeight: 112
                                radius: 12
                                gradient: Gradient {
                                    GradientStop {
                                        position: 0.0
                                        color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.09)
                                    }
                                    GradientStop { position: 1.0; color: window.themeColors.background }
                                }
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 14
                                    spacing: 7
                                    Label {
                                        text: "DERNIÈRE ENTRÉE"
                                        color: window.cyan
                                        font.pixelSize: 10
                                        font.weight: Font.DemiBold
                                        font.letterSpacing: 1.8
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: controllerCenter.lastEventText
                                        color: window.themeColors.text
                                        font.pixelSize: 17
                                        font.weight: Font.DemiBold
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
                                Layout.preferredHeight: 1
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
                color: window.themeColors.muted_text
                font.pixelSize: 10
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
}
