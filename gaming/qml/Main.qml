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
    focus: true

    property color cyan: "#00d9ff"
    property color magenta: "#e33bff"
    property color muted: "#8d96a8"
    property int selectedIndex: -1
    property string selectedTitle: ""
    property string selectedPlatform: ""
    property string selectedSource: ""

    function selectGame(row, title, platform, source) {
        selectedIndex = row
        selectedTitle = title
        selectedPlatform = platform
        selectedSource = source
    }

    function metric(value, suffix) {
        return value < 0 ? "—" : Math.round(value) + suffix
    }

    Rectangle {
        anchors.fill: parent
        color: window.color

        Rectangle {
            width: 620; height: 620; radius: 310
            x: parent.width - width * 0.55; y: -height * 0.48
            color: "#102331"; opacity: 0.20
        }
        Rectangle {
            width: 520; height: 520; radius: 260
            x: -width * 0.5; y: parent.height - height * 0.45
            color: "#2a1232"; opacity: 0.15
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 34
            spacing: 22

            RowLayout {
                Layout.fillWidth: true
                spacing: 18

                ColumnLayout {
                    spacing: 1
                    Label {
                        text: "LEOS"
                        color: "white"
                        font.pixelSize: 29
                        font.weight: Font.Black
                        font.letterSpacing: 5
                    }
                    Label {
                        text: "GAMING MODE"
                        color: window.cyan
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
                implicitHeight: 104
                radius: 15
                color: "#ee111722"
                border.color: "#354052"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 22

                    ColumnLayout {
                        Label { text: "PERFORMANCES"; color: window.cyan; font.pixelSize: 10; font.letterSpacing: 2 }
                        Label { text: "CPU  " + window.metric(systemMonitor.cpuUsage, "%"); color: "white"; font.pixelSize: 15 }
                        Label { text: "RAM  " + window.metric(systemMonitor.memoryUsage, "%"); color: "white"; font.pixelSize: 15 }
                    }
                    Rectangle { width: 1; Layout.fillHeight: true; color: "#374253" }
                    ColumnLayout {
                        Label { text: "TEMPÉRATURE"; color: window.cyan; font.pixelSize: 10; font.letterSpacing: 2 }
                        Label { text: "CPU  " + window.metric(systemMonitor.cpuTemperature, " °C"); color: "white"; font.pixelSize: 15 }
                        Label { text: "GPU  —"; color: window.muted; font.pixelSize: 15 }
                    }
                    Rectangle { width: 1; Layout.fillHeight: true; color: "#374253" }
                    ColumnLayout {
                        Label { text: "JEUX"; color: window.cyan; font.pixelSize: 10; font.letterSpacing: 2 }
                        Label { text: "FPS  —"; color: window.muted; font.pixelSize: 15 }
                        Label { text: "Les métriques avancées seront ajoutées par intégration."; color: window.muted; font.pixelSize: 11 }
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        text: "RETOUR DESKTOP"
                        onClicked: returnDialog.open()
                    }
                    Button {
                        text: "FERMER"
                        onClicked: quickPanel.visible = false
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 26

                ColumnLayout {
                    Layout.preferredWidth: 190
                    Layout.fillHeight: true
                    spacing: 10

                    Label {
                        text: "BIBLIOTHÈQUE"
                        color: window.muted
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
                                border.color: modelData === "Accueil" ? window.cyan : "transparent"
                            }
                            contentItem: Label {
                                text: parent.text
                                color: "white"
                                leftPadding: 9
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

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 16

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: "Votre bibliothèque"
                            color: "white"
                            font.pixelSize: 25
                            font.weight: Font.Bold
                        }
                        Item { Layout.fillWidth: true }
                        Button {
                            text: "ACTUALISER"
                            onClicked: leos.refreshLibrary()
                        }
                        Button {
                            text: "+ AJOUTER UN JEU"
                            onClicked: addDialog.open()
                            background: Rectangle { radius: 9; color: "#17313d"; border.color: window.cyan }
                            contentItem: Label {
                                text: parent.text
                                color: "white"
                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 18

                        GridView {
                            id: gameGrid
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            cellWidth: 230
                            cellHeight: 150
                            clip: true
                            model: gameLibrary
                            currentIndex: window.selectedIndex

                            delegate: Button {
                                id: gameCard
                                required property int index
                                required property string title
                                required property string platform
                                required property string source
                                width: gameGrid.cellWidth - 12
                                height: gameGrid.cellHeight - 12
                                onClicked: window.selectGame(index, title, platform, source)
                                background: Rectangle {
                                    radius: 13
                                    color: window.selectedIndex === gameCard.index ? "#1a2c38" : "#151a24"
                                    border.width: window.selectedIndex === gameCard.index ? 2 : 1
                                    border.color: window.selectedIndex === gameCard.index ? window.cyan : "#2a3444"
                                }
                                contentItem: ColumnLayout {
                                    spacing: 7
                                    Label {
                                        text: gameCard.title
                                        color: "white"
                                        font.pixelSize: 15
                                        font.weight: Font.DemiBold
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                        Layout.alignment: Qt.AlignVCenter
                                    }
                                    Item { Layout.fillHeight: true }
                                    Label {
                                        text: gameCard.platform + "  •  " + gameCard.source
                                        color: window.muted
                                        font.pixelSize: 10
                                    }
                                }
                            }

                            Label {
                                anchors.centerIn: parent
                                width: parent.width - 50
                                visible: gameGrid.count === 0
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.WordWrap
                                text: "Aucun jeu détecté pour le moment.\n\nSteam sera analysé automatiquement. Tu peux aussi ajouter un jeu manuellement."
                                color: window.muted
                                font.pixelSize: 14
                            }
                        }

                        Rectangle {
                            Layout.preferredWidth: 280
                            Layout.fillHeight: true
                            radius: 16
                            color: "#111720"
                            border.color: "#293342"

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 20
                                spacing: 12

                                Label {
                                    text: "JEU SÉLECTIONNÉ"
                                    color: window.cyan
                                    font.pixelSize: 10
                                    font.letterSpacing: 2
                                }
                                Label {
                                    text: window.selectedTitle || "Choisis un jeu"
                                    color: "white"
                                    font.pixelSize: 22
                                    font.weight: Font.Bold
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }
                                Label {
                                    text: window.selectedTitle ? window.selectedPlatform + " • " + window.selectedSource : "Les détails apparaîtront ici."
                                    color: window.muted
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                }
                                Item { Layout.fillHeight: true }
                                Button {
                                    Layout.fillWidth: true
                                    enabled: window.selectedIndex >= 0
                                    text: "JOUER"
                                    onClicked: {
                                        if (!leos.launchGame(window.selectedIndex))
                                            statusText.text = "Lancement impossible : vérifie le lanceur associé."
                                        else
                                            statusText.text = "Demande de lancement envoyée."
                                    }
                                    background: Rectangle {
                                        radius: 10
                                        color: parent.enabled ? "#103847" : "#202630"
                                        border.color: parent.enabled ? window.cyan : "#344052"
                                    }
                                    contentItem: Label {
                                        text: parent.text
                                        color: parent.enabled ? "white" : "#778091"
                                        font.pixelSize: 13
                                        font.weight: Font.Bold
                                        horizontalAlignment: Text.AlignHCenter
                                    }
                                }
                                Label {
                                    id: statusText
                                    Layout.fillWidth: true
                                    color: window.muted
                                    font.pixelSize: 10
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: returnDialog
        title: "Retourner à Desktop Mode ?"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Cancel
        width: 430
        ColumnLayout {
            width: parent.width
            spacing: 14
            Label {
                text: "Gaming va se fermer et le bureau KDE réapparaître. Les applications déjà ouvertes resteront en arrière-plan ; aucune ne sera fermée automatiquement."
                color: "white"
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Button {
                text: "CONFIRMER LE RETOUR AU DESKTOP"
                Layout.fillWidth: true
                onClicked: {
                    returnDialog.close()
                    leos.returnToDesktop()
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

    Dialog {
        id: addDialog
        title: "Ajouter un jeu à LEOS"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        width: 440

        ColumnLayout {
            width: parent.width
            spacing: 12
            Label { text: "Nom du jeu"; color: "white" }
            TextField { id: gameName; Layout.fillWidth: true; placeholderText: "Ex. : Mon jeu" }
            Label { text: "Plateforme"; color: "white" }
            ComboBox {
                id: gamePlatform
                Layout.fillWidth: true
                model: ["PC", "Nintendo", "PlayStation", "SEGA", "Arcade", "Autre"]
            }
            Label { text: "Commande de lancement"; color: "white" }
            TextField {
                id: launchCommand
                Layout.fillWidth: true
                placeholderText: "Ex. : steam steam://rungameid/123456"
            }
            Label {
                text: "La commande est enregistrée dans ton profil et exécutée sans passer par un shell."
                color: window.muted
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                font.pixelSize: 10
            }
        }

        onAccepted: {
            if (leos.addGame(gameName.text, gamePlatform.currentText, launchCommand.text)) {
                gameName.clear()
                launchCommand.clear()
                statusText.text = "Jeu ajouté. Sélectionne-le dans la bibliothèque."
            } else {
                statusText.text = "Impossible d'ajouter ce jeu. Vérifie les champs."
            }
        }
        onRejected: {
            gameName.clear()
            launchCommand.clear()
        }
    }

    Connections {
        target: leos
        function onMessageChanged(message) {
            statusText.text = message
        }
    }

    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_F1) {
            quickPanel.visible = !quickPanel.visible
            event.accepted = true
        } else if (event.key === Qt.Key_F2) {
            addDialog.open()
            event.accepted = true
        } else if (event.key === Qt.Key_Escape && quickPanel.visible) {
            quickPanel.visible = false
            event.accepted = true
        }
    }
}
