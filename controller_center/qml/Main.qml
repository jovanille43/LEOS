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

        Rectangle {
            width: 500
            height: 500
            radius: 250
            x: parent.width - width * 0.54
            y: -height * 0.46
            color: window.themeColors.accent_primary
            opacity: 0.05
        }
        Rectangle {
            width: 430
            height: 430
            radius: 215
            x: -width * 0.5
            y: parent.height - height * 0.48
            color: window.themeColors.accent_secondary
            opacity: 0.04
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: window.width < 920 || window.height < 680 ? 18 : 32
            spacing: window.width < 920 ? 12 : 20

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    spacing: 2
                    Label {
                        text: "LEOS"
                        color: window.themeColors.text
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
                Rectangle {
                    radius: 9
                    color: window.themeColors.surface
                    border.color: window.themeColors.border
                    Layout.preferredHeight: 34
                    Layout.preferredWidth: 190
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 11
                        anchors.rightMargin: 11
                        spacing: 8
                        Rectangle {
                            Layout.preferredWidth: 7
                            Layout.preferredHeight: 7
                            radius: 4
                            color: controllerCenter.selectedIndex >= 0 ? "#78C99B" : window.muted
                        }
                        Label {
                            Layout.fillWidth: true
                            text: controllerCenter.selectedIndex >= 0 ? "MANETTE CONNECTÉE" : "EN ATTENTE"
                            color: window.muted
                            font.pixelSize: 9
                            font.letterSpacing: 1.1
                            elide: Text.ElideRight
                        }
                    }
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
                        Layout.preferredWidth: 54
                        Layout.preferredHeight: 54
                        radius: 14
                        color: window.themeColors.surface_elevated
                        border.color: window.cyan
                        Rectangle {
                            x: 8
                            y: 15
                            width: 38
                            height: 24
                            radius: 9
                            color: "transparent"
                            border.color: window.cyan
                            border.width: 2
                        }
                        Rectangle { x: 14; y: 25; width: 10; height: 3; radius: 1; color: window.cyan }
                        Rectangle { x: 17.5; y: 21.5; width: 3; height: 10; radius: 1; color: window.cyan }
                        Repeater {
                            model: 2
                            delegate: Rectangle {
                                required property int index
                                width: 5
                                height: 5
                                radius: 3
                                x: index === 0 ? 31 : 37
                                y: index === 0 ? 21 : 27
                                color: index === 0 ? window.accentA : window.accentB
                            }
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 5
                        Label {
                            text: controllerCenter.selectedDeviceName
                            color: window.themeColors.text
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
                        id: refreshDevicesButton
                        text: "ACTUALISER"
                        Accessible.name: "Actualiser la détection des manettes"
                        onClicked: controllerCenter.refreshDevices()
                        background: Rectangle {
                            radius: 8
                            color: refreshDevicesButton.hovered || refreshDevicesButton.activeFocus ? window.themeColors.surface_elevated : window.themeColors.surface
                            border.width: refreshDevicesButton.activeFocus ? 2 : 1
                            border.color: refreshDevicesButton.activeFocus ? window.themeColors.text : refreshDevicesButton.hovered ? window.accentB : window.themeColors.border
                        }
                        contentItem: Label {
                            text: refreshDevicesButton.text
                            color: window.themeColors.text
                            font.weight: Font.DemiBold
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 18

                ColumnLayout {
                    Layout.preferredWidth: window.width < 920 ? 245 : 285
                    Layout.minimumWidth: 220
                    Layout.fillHeight: true
                    spacing: 14

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 158
                        radius: 14
                        color: window.panel
                        border.color: window.line
                        clip: true
                        Rectangle {
                            anchors { left: parent.left; right: parent.right; top: parent.top }
                            height: 2
                            gradient: Gradient {
                                GradientStop { position: 0; color: window.accentA }
                                GradientStop { position: 1; color: window.accentB }
                            }
                            opacity: 0.58
                        }
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
                        clip: true
                        Rectangle {
                            anchors { left: parent.left; right: parent.right; top: parent.top }
                            height: 2
                            gradient: Gradient {
                                GradientStop { position: 0; color: window.accentA }
                                GradientStop { position: 1; color: window.accentB }
                            }
                            opacity: 0.58
                        }
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
                                color: window.themeColors.text
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
                        clip: true
                        Rectangle {
                            anchors { left: parent.left; right: parent.right; top: parent.top }
                            height: 2
                            gradient: Gradient {
                                GradientStop { position: 0; color: window.accentA }
                                GradientStop { position: 1; color: window.accentB }
                            }
                            opacity: 0.58
                        }
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
                                color: window.themeColors.background
                                border.color: window.themeColors.border
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
                                        color: window.themeColors.text
                                        font.pixelSize: 16
                                        wrapMode: Text.WordWrap
                                    }
                                }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Label {
                                    text: "STICKS ANALOGIQUES"
                                    color: window.muted
                                    font.pixelSize: 10
                                    font.letterSpacing: 1.5
                                }
                                Item { Layout.fillWidth: true }
                                Label {
                                    text: controllerCenter.hasLeftStick || controllerCenter.hasRightStick ? "EN DIRECT" : "NON DÉTECTÉS"
                                    color: controllerCenter.hasLeftStick || controllerCenter.hasRightStick ? window.cyan : window.muted
                                    font.pixelSize: 9
                                    font.letterSpacing: 1
                                }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10
                                visible: controllerCenter.hasLeftStick || controllerCenter.hasRightStick
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 116
                                    radius: 10
                                    color: window.themeColors.background
                                    border.color: window.themeColors.border
                                    visible: controllerCenter.hasLeftStick
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 2
                                        Label {
                                            Layout.fillWidth: true
                                            text: "GAUCHE"
                                            color: window.cyan
                                            font.pixelSize: 9
                                            font.letterSpacing: 1.4
                                            horizontalAlignment: Text.AlignHCenter
                                        }
                                        Item {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            Rectangle {
                                                width: 66
                                                height: 66
                                                radius: 33
                                                anchors.centerIn: parent
                                                color: window.themeColors.surface
                                                border.color: window.themeColors.border
                                                Rectangle {
                                                    anchors.centerIn: parent
                                                    width: 1
                                                    height: 50
                                                    color: window.themeColors.border
                                                }
                                                Rectangle {
                                                    anchors.centerIn: parent
                                                    width: 50
                                                    height: 1
                                                    color: window.themeColors.border
                                                }
                                                Rectangle {
                                                    width: 13
                                                    height: 13
                                                    radius: 7
                                                    x: (parent.width - width) / 2 + controllerCenter.leftStickX * 23
                                                    y: (parent.height - height) / 2 + controllerCenter.leftStickY * 23
                                                    color: window.accentA
                                                    border.color: window.themeColors.text
                                                    border.width: 1
                                                }
                                            }
                                        }
                                    }
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 116
                                    radius: 10
                                    color: window.themeColors.background
                                    border.color: window.themeColors.border
                                    visible: controllerCenter.hasRightStick
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 2
                                        Label {
                                            Layout.fillWidth: true
                                            text: "DROIT"
                                            color: window.accentB
                                            font.pixelSize: 9
                                            font.letterSpacing: 1.4
                                            horizontalAlignment: Text.AlignHCenter
                                        }
                                        Item {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            Rectangle {
                                                width: 66
                                                height: 66
                                                radius: 33
                                                anchors.centerIn: parent
                                                color: window.themeColors.surface
                                                border.color: window.themeColors.border
                                                Rectangle {
                                                    anchors.centerIn: parent
                                                    width: 1
                                                    height: 50
                                                    color: window.themeColors.border
                                                }
                                                Rectangle {
                                                    anchors.centerIn: parent
                                                    width: 50
                                                    height: 1
                                                    color: window.themeColors.border
                                                }
                                                Rectangle {
                                                    width: 13
                                                    height: 13
                                                    radius: 7
                                                    x: (parent.width - width) / 2 + controllerCenter.rightStickX * 23
                                                    y: (parent.height - height) / 2 + controllerCenter.rightStickY * 23
                                                    color: window.accentB
                                                    border.color: window.themeColors.text
                                                    border.width: 1
                                                }
                                            }
                                        }
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
                                color: window.themeColors.text
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
                                color: window.themeColors.text
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
