import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1120
    height: 780
    minimumWidth: 820
    minimumHeight: 620
    visible: true
    title: "LEOS — Centre de contrôle"
    color: "#090b10"

    property color cyan: "#00d9ff"
    property color magenta: "#e33bff"
    property color muted: "#909aac"
    property int selectedPage: 0
    property string launchNotice: ""

    Rectangle {
        anchors.fill: parent
        color: window.color

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 30
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
                spacing: 18

                ColumnLayout {
                    Layout.preferredWidth: 220
                    Layout.minimumWidth: 185
                    Layout.fillHeight: true
                    spacing: 9

                    Repeater {
                        model: [
                            { label: "Vue d'ensemble", page: 0 },
                            { label: "Apparence", page: 1 },
                            { label: "Matériel & connexions", page: 2 },
                            { label: "Performances", page: 3 },
                            { label: "Paramètres KDE", page: 4 }
                        ]
                        delegate: Button {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 48
                            text: modelData.label
                            onClicked: {
                                window.selectedPage = modelData.page
                                window.launchNotice = ""
                            }
                            background: Rectangle {
                                radius: 10
                                color: window.selectedPage === modelData.page ? "#182732" : "#121720"
                                border.color: window.selectedPage === modelData.page ? window.cyan : "#293342"
                            }
                            contentItem: Label {
                                text: parent.text
                                color: "white"
                                font.pixelSize: 12
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 8
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                    Label {
                        text: "LEOS • BUILD EN DÉVELOPPEMENT"
                        color: "#626d7d"
                        font.pixelSize: 9
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }

                StackLayout {
                    id: pages
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: window.selectedPage

                    ScrollView {
                        clip: true
                        ColumnLayout {
                            width: pages.width - 12
                            spacing: 14

                            Label {
                                text: "VUE D'ENSEMBLE"
                                color: "white"
                                font.pixelSize: 20
                                font.weight: Font.Bold
                            }
                            Label {
                                text: "État en direct des ressources détectées sur cet appareil."
                                color: window.muted
                                font.pixelSize: 12
                                Layout.fillWidth: true
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 3
                                columnSpacing: 10
                                rowSpacing: 10

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 132
                                    radius: 13
                                    color: "#121720"
                                    border.color: "#293342"
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 14
                                        spacing: 10
                                        Label {
                                            text: "UTILISATION CPU"
                                            color: window.cyan
                                            font.pixelSize: 10
                                            font.letterSpacing: 1
                                        }
                                        Label {
                                            text: systemMonitor.cpuUsage >= 0
                                                ? Math.round(systemMonitor.cpuUsage) + "%"
                                                : "—"
                                            color: "white"
                                            font.pixelSize: 26
                                            font.weight: Font.Bold
                                        }
                                        Label {
                                            text: "Processeur"
                                            color: window.muted
                                            font.pixelSize: 10
                                        }
                                    }
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 132
                                    radius: 13
                                    color: "#121720"
                                    border.color: "#293342"
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 14
                                        spacing: 10
                                        Label {
                                            text: "MÉMOIRE"
                                            color: window.cyan
                                            font.pixelSize: 10
                                            font.letterSpacing: 1
                                        }
                                        Label {
                                            text: systemMonitor.memoryUsage >= 0
                                                ? Math.round(systemMonitor.memoryUsage) + "%"
                                                : "—"
                                            color: "white"
                                            font.pixelSize: 26
                                            font.weight: Font.Bold
                                        }
                                        Label {
                                            text: "RAM utilisée"
                                            color: window.muted
                                            font.pixelSize: 10
                                        }
                                    }
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 132
                                    radius: 13
                                    color: "#121720"
                                    border.color: "#293342"
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 14
                                        spacing: 10
                                        Label {
                                            text: "TEMPÉRATURE CPU"
                                            color: window.cyan
                                            font.pixelSize: 10
                                            font.letterSpacing: 1
                                        }
                                        Label {
                                            text: systemMonitor.cpuTemperature >= 0
                                                ? Math.round(systemMonitor.cpuTemperature) + " °C"
                                                : "Indisponible"
                                            color: "white"
                                            font.pixelSize: systemMonitor.cpuTemperature >= 0 ? 26 : 16
                                            font.weight: Font.Bold
                                        }
                                        Label {
                                            text: "Selon les capteurs Linux"
                                            color: window.muted
                                            font.pixelSize: 10
                                            wrapMode: Text.WordWrap
                                            Layout.fillWidth: true
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 108
                                radius: 13
                                color: "#121720"
                                border.color: "#293342"
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 18
                                    spacing: 7
                                    Label {
                                        text: "SURVEILLANCE LEOS"
                                        color: window.cyan
                                        font.pixelSize: 10
                                        font.letterSpacing: 1
                                    }
                                    Label {
                                        text: systemMonitor.available
                                            ? "Actualisation automatique toutes les deux secondes. Les valeurs non exposées par le matériel restent indisponibles."
                                            : "Le module de mesure système n'est pas disponible sur cette installation."
                                        color: window.muted
                                        font.pixelSize: 11
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }

                    ScrollView {
                        clip: true
                        ColumnLayout {
                            width: pages.width - 12
                            spacing: 14

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 160
                                radius: 15
                                color: "#121720"
                                border.color: "#293342"
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
                                Layout.preferredHeight: 205
                                radius: 15
                                color: "#121720"
                                border.color: "#293342"
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
                                        Label { text: "Animations LEOS"; color: "white"; Layout.fillWidth: true }
                                        Switch {
                                            checked: controlCenter.animationsEnabled
                                            onToggled: controlCenter.setAnimationsEnabled(checked)
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Label { text: "Sons LEOS"; color: "white"; Layout.fillWidth: true }
                                        Switch {
                                            checked: controlCenter.soundsEnabled
                                            onToggled: controlCenter.setSoundsEnabled(checked)
                                        }
                                    }
                                }
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }

                    ScrollView {
                        clip: true
                        ColumnLayout {
                            width: pages.width - 12
                            spacing: 14
                            Label {
                                text: "MATÉRIEL & CONNEXIONS"
                                color: "white"
                                font.pixelSize: 20
                                font.weight: Font.Bold
                            }
                            Label {
                                text: "Accède directement aux réglages KDE. LEOS ne modifie aucun périphérique sans ton action."
                                color: window.muted
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                columnSpacing: 12
                                rowSpacing: 12

                                Repeater {
                                    model: [
                                        { title: "Bluetooth", description: "Manettes, casques, claviers et souris", section: "bluetooth" },
                                        { title: "Réseau", description: "Wi-Fi, Ethernet et connexions", section: "network" },
                                        { title: "Audio", description: "Sortie, entrée et périphériques audio", section: "audio" },
                                        { title: "Écrans", description: "Résolution, fréquence et disposition", section: "display" },
                                        { title: "Énergie", description: "Gestion de l'alimentation et autonomie", section: "power" },
                                        { title: "Clavier", description: "Disposition et comportement du clavier", section: "keyboard" },
                                        { title: "Souris & pavé tactile", description: "Vitesse, clics et défilement", section: "mouse" }
                                    ]
                                    delegate: Rectangle {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 132
                                        radius: 12
                                        color: "#121720"
                                        border.color: "#293342"
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 14
                                            spacing: 7
                                            Label {
                                                text: modelData.title
                                                color: "white"
                                                font.pixelSize: 14
                                                font.weight: Font.DemiBold
                                            }
                                            Label {
                                                text: modelData.description
                                                color: window.muted
                                                font.pixelSize: 10
                                                wrapMode: Text.WordWrap
                                                Layout.fillWidth: true
                                                Layout.fillHeight: true
                                            }
                                            Button {
                                                text: "Ouvrir les réglages"
                                                onClicked: {
                                                    window.launchNotice = controlCenter.openSettingsModule(modelData.section)
                                                        ? ""
                                                        : "Impossible d'ouvrir ce module KDE sur cette session."
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            Label {
                                text: window.launchNotice
                                visible: text.length > 0
                                color: window.magenta
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }

                    ScrollView {
                        clip: true
                        ColumnLayout {
                            width: pages.width - 12
                            spacing: 14
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 190
                                radius: 15
                                color: "#121720"
                                border.color: "#293342"
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
                                        text: "Le choix est enregistré localement. L'application réelle des profils CPU/GPU reste à intégrer et à valider sur le matériel."
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
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 105
                                radius: 15
                                color: "#121720"
                                border.color: "#293342"
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
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
                            Item { Layout.fillHeight: true }
                        }
                    }

                    ColumnLayout {
                        spacing: 14
                        Label {
                            text: "PARAMÈTRES KDE"
                            color: "white"
                            font.pixelSize: 20
                            font.weight: Font.Bold
                        }
                        Label {
                            text: "Les paramètres avancés restent ceux de KDE et de Bazzite. LEOS ne remplace pas les outils natifs du système."
                            color: window.muted
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Button {
                            text: "OUVRIR TOUS LES PARAMÈTRES KDE"
                            onClicked: {
                                window.launchNotice = controlCenter.openAdvancedSettings()
                                    ? ""
                                    : "System Settings KDE est introuvable sur cette session."
                            }
                        }
                        Label {
                            text: window.launchNotice
                            visible: text.length > 0
                            color: window.magenta
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Item { Layout.fillHeight: true }
                    }
                }
            }
        }
    }
}
