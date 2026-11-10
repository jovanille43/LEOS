import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1120
    height: 780
    visible: true
    title: "LEOS — Centre de contrôle"
    color: "#090b10"

    property color cyan: "#00d9ff"
    property color magenta: "#e33bff"
    property color muted: "#909aac"

    Rectangle {
        anchors.fill: parent
        color: window.color

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 34
            spacing: 22

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
                        text: "CENTRE DE CONTRÔLE"
                        color: window.cyan
                        font.pixelSize: 10
                        font.letterSpacing: 3
                    }
                }
                Item { Layout.fillWidth: true }
                Label {
                    text: "PRÉFÉRENCES UTILISATEUR"
                    color: window.muted
                    font.pixelSize: 10
                    font.letterSpacing: 2
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 20

                ColumnLayout {
                    Layout.preferredWidth: 220
                    Layout.fillHeight: true
                    spacing: 10
                    Repeater {
                        model: ["Apparence", "Animations et sons", "Performances", "Paramètres système"]
                        delegate: Rectangle {
                            required property string modelData
                            Layout.fillWidth: true
                            height: 48
                            radius: 10
                            color: modelData === "Apparence" ? "#182732" : "#121720"
                            border.color: modelData === "Apparence" ? window.cyan : "#293342"
                            Label {
                                anchors.left: parent.left
                                anchors.leftMargin: 14
                                anchors.verticalCenter: parent.verticalCenter
                                text: modelData
                                color: "white"
                                font.pixelSize: 13
                            }
                        }
                    }
                    Item { Layout.fillHeight: true }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 16

                    Rectangle {
                        Layout.fillWidth: true
                        radius: 15
                        color: "#121720"
                        border.color: "#293342"
                        Layout.preferredHeight: 175

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 20
                            spacing: 12
                            Label {
                                text: "THÈME LEOS"
                                color: window.cyan
                                font.pixelSize: 11
                                font.letterSpacing: 2
                            }
                            Label {
                                text: "Choisis l'apparence générale de ton interface."
                                color: window.muted
                                font.pixelSize: 12
                            }
                            ComboBox {
                                id: themeBox
                                Layout.fillWidth: true
                                model: ["LEOS Original", "Light", "Cyan", "Magenta", "Gaming"]
                                Component.onCompleted: {
                                    const values = ["leos-original", "light", "cyan", "magenta", "gaming"]
                                    currentIndex = Math.max(0, values.indexOf(controlCenter.theme))
                                }
                                onActivated: {
                                    const values = ["leos-original", "light", "cyan", "magenta", "gaming"]
                                    controlCenter.setTheme(values[currentIndex])
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        radius: 15
                        color: "#121720"
                        border.color: "#293342"
                        Layout.preferredHeight: 205

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 20
                            spacing: 10
                            Label {
                                text: "EXPÉRIENCE"
                                color: window.cyan
                                font.pixelSize: 11
                                font.letterSpacing: 2
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Label {
                                    text: "Animations LEOS"
                                    color: "white"
                                    Layout.fillWidth: true
                                }
                                Switch {
                                    checked: controlCenter.animationsEnabled
                                    onToggled: controlCenter.setAnimationsEnabled(checked)
                                }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Label {
                                    text: "Sons LEOS"
                                    color: "white"
                                    Layout.fillWidth: true
                                }
                                Switch {
                                    checked: controlCenter.soundsEnabled
                                    onToggled: controlCenter.setSoundsEnabled(checked)
                                }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Label {
                                    text: "Overlay de performances en jeu"
                                    color: "white"
                                    Layout.fillWidth: true
                                }
                                Switch {
                                    checked: controlCenter.gamingOverlayEnabled
                                    onToggled: controlCenter.setGamingOverlayEnabled(checked)
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        radius: 15
                        color: "#121720"
                        border.color: "#293342"
                        Layout.preferredHeight: 150

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 20
                            spacing: 10
                            Label {
                                text: "PROFIL DE PERFORMANCES"
                                color: window.cyan
                                font.pixelSize: 11
                                font.letterSpacing: 2
                            }
                            Label {
                                text: "Le profil choisi sera appliqué par le gestionnaire LEOS lorsqu'il sera intégré."
                                color: window.muted
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            ComboBox {
                                id: profileBox
                                Layout.fillWidth: true
                                model: ["Performance", "Balanced", "Quiet", "Battery Saver"]
                                Component.onCompleted: {
                                    const values = ["performance", "balanced", "quiet", "battery-saver"]
                                    currentIndex = Math.max(0, values.indexOf(controlCenter.performanceProfile))
                                }
                                onActivated: {
                                    const values = ["performance", "balanced", "quiet", "battery-saver"]
                                    controlCenter.setPerformanceProfile(values[currentIndex])
                                }
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                    RowLayout {
                        Layout.fillWidth: true
                        Item { Layout.fillWidth: true }
                        Button {
                            text: "OUVRIR LES PARAMÈTRES KDE"
                            onClicked: {
                                if (!controlCenter.openAdvancedSettings())
                                    advancedError.visible = true
                            }
                        }
                    }
                    Label {
                        id: advancedError
                        visible: false
                        text: "System Settings KDE est introuvable sur cette session."
                        color: window.magenta
                        font.pixelSize: 11
                    }
                }
            }
        }
    }
}
