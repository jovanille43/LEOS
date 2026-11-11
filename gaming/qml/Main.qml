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
    property string selectedCategory: "Accueil"
    property bool selectedIsFavorite: false
    property var categoryNames: ["Accueil", "PC Gaming", "Nintendo", "PlayStation", "SEGA", "Arcade", "Favoris", "Récemment joués"]
    property int selectedCategoryIndex: 0
    property string navigationArea: "categories"

    function selectGame(row, title, platform, source, favorite) {
        navigationArea = "games"
        selectedIndex = row
        selectedTitle = title
        selectedPlatform = platform
        selectedSource = source
        selectedIsFavorite = favorite
    }

    function selectGameAt(row) {
        const info = gameLibrary.gameInfo(row)
        if (info && info.title)
            selectGame(row, info.title, info.platform, info.source, info.favorite)
    }

    function clearSelection() {
        selectedIndex = -1
        selectedTitle = ""
        selectedPlatform = ""
        selectedSource = ""
        selectedIsFavorite = false
    }

    function chooseCategory(index) {
        if (index < 0 || index >= categoryNames.length)
            return
        selectedCategoryIndex = index
        selectedCategory = categoryNames[index]
        gameLibrary.setCategory(selectedCategory)
        clearSelection()
        navigationArea = "games"
    }

    function moveCategory(direction) {
        let next = selectedCategoryIndex
        if (direction === "up")
            next -= 1
        else if (direction === "down")
            next += 1
        selectedCategoryIndex = Math.max(0, Math.min(categoryNames.length - 1, next))
    }

    function moveSelection(direction) {
        if (gameGrid.count < 1)
            return
        const columns = Math.max(1, Math.floor(gameGrid.width / gameGrid.cellWidth))
        let next = selectedIndex < 0 ? 0 : selectedIndex
        if (direction === "left")
            next -= 1
        else if (direction === "right")
            next += 1
        else if (direction === "up")
            next -= columns
        else if (direction === "down")
            next += columns
        next = Math.max(0, Math.min(gameGrid.count - 1, next))
        selectGameAt(next)
        gameGrid.positionViewAtIndex(next, GridView.Contain)
    }

    function navigateDirection(action) {
        if (navigationArea === "categories") {
            if (action === "up" || action === "down")
                moveCategory(action)
            else if (action === "right") {
                chooseCategory(selectedCategoryIndex)
                if (gameGrid.count > 0)
                    selectGameAt(0)
            }
            return
        }
        if (action === "left") {
            const columns = Math.max(1, Math.floor(gameGrid.width / gameGrid.cellWidth))
            if (selectedIndex < 0 || selectedIndex % columns === 0) {
                navigationArea = "categories"
                selectedCategoryIndex = categoryNames.indexOf(selectedCategory)
                return
            }
        }
        moveSelection(action)
    }

    function handleGamepadAction(action) {
        if (returnDialog.visible) {
            if (action === "confirm") {
                returnDialog.close()
                leos.returnToDesktop()
            } else if (action === "back") {
                returnDialog.close()
            }
            return
        }
        if (addDialog.visible) {
            if (action === "back")
                addDialog.close()
            return
        }
        if (action === "menu") {
            quickPanel.visible = !quickPanel.visible
            return
        }
        if (quickPanel.visible) {
            if (action === "back")
                quickPanel.visible = false
            return
        }
        if (action === "up" || action === "down" ||
                action === "left" || action === "right") {
            navigateDirection(action)
        } else if (action === "confirm") {
            if (navigationArea === "categories") {
                chooseCategory(selectedCategoryIndex)
                if (gameGrid.count > 0)
                    selectGameAt(0)
            } else if (selectedIndex >= 0) {
                if (!leos.launchGame(selectedIndex))
                    statusText.text = "Lancement impossible : vérifie le lanceur associé."
                else
                    statusText.text = "Demande de lancement envoyée."
            } else {
                moveSelection("right")
            }
        } else if (action === "back") {
            if (navigationArea === "games" && selectedIndex >= 0)
                clearSelection()
            else
                returnDialog.open()
        }
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

                Label {
                    text: leos.gamepadStatus
                    color: window.muted
                    font.pixelSize: 10
                    elide: Text.ElideRight
                }

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
                        model: window.categoryNames
                        delegate: Button {
                            required property string modelData
                            Layout.fillWidth: true
                            text: modelData
                            background: Rectangle {
                                radius: 9
                                color: modelData === window.selectedCategory ? "#202b38" : "transparent"
                                border.width: modelData === window.categoryNames[window.selectedCategoryIndex] && window.navigationArea === "categories" ? 2 : 1
                                border.color: modelData === window.categoryNames[window.selectedCategoryIndex] && window.navigationArea === "categories" ? window.magenta : (modelData === window.selectedCategory ? window.cyan : "transparent")
                            }
                            contentItem: Label {
                                text: parent.text
                                color: "white"
                                leftPadding: 9
                                verticalAlignment: Text.AlignVCenter
                                font.pixelSize: 13
                            }
                            onClicked: {
                                window.chooseCategory(window.categoryNames.indexOf(modelData))
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
                            text: window.selectedCategory
                            color: "white"
                            font.pixelSize: 25
                            font.weight: Font.Bold
                        }
                        Item { Layout.fillWidth: true }
                        TextField {
                            id: searchField
                            Layout.preferredWidth: 270
                            placeholderText: "Rechercher un jeu…"
                            color: "white"
                            selectByMouse: true
                            onTextChanged: {
                                gameLibrary.setSearchQuery(text)
                                window.clearSelection()
                            }
                        }
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
                                required property bool favorite
                                required property string artwork
                                width: gameGrid.cellWidth - 12
                                height: gameGrid.cellHeight - 12
                                onClicked: window.selectGame(index, title, platform, source, favorite)
                                background: Rectangle {
                                    radius: 13
                                    color: window.selectedIndex === gameCard.index ? "#1a2c38" : "#151a24"
                                    border.width: window.selectedIndex === gameCard.index ? 2 : 1
                                    border.color: window.selectedIndex === gameCard.index ? window.cyan : "#2a3444"
                                }
                                contentItem: ColumnLayout {
                                    spacing: 7
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        spacing: 10
                                        Image {
                                            Layout.preferredWidth: gameCard.artwork.length > 0 ? 70 : 0
                                            Layout.fillHeight: true
                                            source: gameCard.artwork
                                            visible: gameCard.artwork.length > 0
                                            fillMode: Image.PreserveAspectCrop
                                            asynchronous: true
                                            cache: true
                                            sourceSize.width: 140
                                            sourceSize.height: 210
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            spacing: 5
                                            Label {
                                                text: gameCard.title
                                                color: "white"
                                                font.pixelSize: 15
                                                font.weight: Font.DemiBold
                                                wrapMode: Text.WordWrap
                                                Layout.fillWidth: true
                                            }
                                            Item { Layout.fillHeight: true }
                                            Label {
                                                text: gameCard.favorite ? "★ FAVORI" : ""
                                                color: window.magenta
                                                font.pixelSize: 9
                                                font.weight: Font.Bold
                                            }
                                        }
                                    }
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
                                text: searchField.text.length > 0
                                    ? "Aucun résultat pour « " + searchField.text + " »."
                                    : window.selectedCategory === "Favoris"
                                        ? "Aucun favori pour le moment. Sélectionne un jeu et ajoute-le à tes favoris."
                                        : window.selectedCategory === "Récemment joués"
                                            ? "Aucun jeu lancé récemment."
                                            : "Aucun jeu détecté dans cette catégorie.\\n\\nSteam sera analysé automatiquement. Tu peux aussi ajouter un jeu manuellement."
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
                                    text: window.selectedIsFavorite ? "RETIRER DES FAVORIS" : "AJOUTER AUX FAVORIS"
                                    onClicked: {
                                        const row = window.selectedIndex
                                        const wasFavorite = window.selectedIsFavorite
                                        const nowFavorite = gameLibrary.toggleFavorite(row)
                                        if (window.selectedCategory === "Favoris" && wasFavorite && !nowFavorite)
                                            window.clearSelection()
                                        else
                                            window.selectGameAt(row)
                                    }
                                    background: Rectangle {
                                        radius: 9
                                        color: "#191d2a"
                                        border.color: window.magenta
                                    }
                                    contentItem: Label {
                                        text: parent.text
                                        color: "white"
                                        font.pixelSize: 11
                                        font.weight: Font.DemiBold
                                        horizontalAlignment: Text.AlignHCenter
                                    }
                                }
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
        function onGamepadAction(action) {
            window.handleGamepadAction(action)
        }
    }

    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_Left) {
            window.navigateDirection("left")
            event.accepted = true
        } else if (event.key === Qt.Key_Right) {
            window.navigateDirection("right")
            event.accepted = true
        } else if (event.key === Qt.Key_Up) {
            window.navigateDirection("up")
            event.accepted = true
        } else if (event.key === Qt.Key_Down) {
            window.navigateDirection("down")
            event.accepted = true
        } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter ||
                   event.key === Qt.Key_Space) {
            window.handleGamepadAction("confirm")
            event.accepted = true
        } else if (event.key === Qt.Key_F1) {
            window.handleGamepadAction("menu")
            event.accepted = true
        } else if (event.key === Qt.Key_F2) {
            addDialog.open()
            event.accepted = true
        } else if (event.key === Qt.Key_Escape || event.key === Qt.Key_Backspace) {
            window.handleGamepadAction("back")
            event.accepted = true
        }
    }
}
