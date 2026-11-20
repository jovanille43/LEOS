import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtMultimedia

ApplicationWindow {
    id: window
    width: 1280
    height: 760
    visible: true
    visibility: Window.FullScreen
    title: "LEOS — Choix du mode"
    property var themeColors: leosTheme.themePalette
    color: themeColors.background

    property color colorA: themeColors.accent_primary
    property color colorB: themeColors.accent_secondary
    property color colorAText: themeColors.accent_primary_text
    property color colorBText: themeColors.accent_secondary_text
    property color muted: themeColors.muted_text
    property string draftColorA: leosTheme.themeColorA
    property string draftColorB: leosTheme.themeColorB
    property bool draftColorAChosen: leosTheme.themeColorsConfigured
    property bool draftColorBChosen: leosTheme.themeColorsConfigured
    property string themeColorNotice: ""
    property date currentDate: new Date()
    property string pendingMode: ""
    property bool transitionInProgress: false
    property int appearanceDialogFocusIndex: 0

    function requestDesktopMode() {
        if (modeSelectorController.desktopAppearanceStatus === "pending") {
            appearanceDialogFocusIndex = 0
            appearanceDialog.open()
            appearanceColorAButton.forceActiveFocus()
            return
        }
        requestModeWithIntro("desktop")
    }

    function colorToHex(color) {
        function byteHex(value) {
            const valueHex = Math.max(0, Math.min(255, Math.round(value * 255))).toString(16).toUpperCase()
            return valueHex.length === 1 ? "0" + valueHex : valueHex
        }
        return "#" + byteHex(color.r) + byteHex(color.g) + byteHex(color.b)
    }

    function activateDesktopAppearance() {
        if (!draftColorAChosen || !draftColorBChosen) {
            appearanceStatusText.text = "Choisis d’abord les deux couleurs A et B. Elles restent entièrement libres."
            return
        }
        themeColorNotice = leosTheme.setThemeColors(draftColorA, draftColorB)
        if (!leosTheme.themeColorsConfigured) {
            appearanceStatusText.text = themeColorNotice
            return
        }
        appearanceStatusText.text = "Sauvegarde du bureau et application du profil LEOS…"
        if (!modeSelectorController.beginDesktopAppearanceSetup())
            appearanceStatusText.text = "L'activation ne peut pas démarrer. Vérifie l'état du premier démarrage."
    }

    function keepCurrentDesktopAppearance() {
        if (modeSelectorController.skipDesktopAppearance()) {
            appearanceDialog.close()
            window.requestModeWithIntro("desktop")
        } else {
            appearanceStatusText.text = "Le choix n'a pas pu être enregistré. Aucun réglage KDE n'a été modifié."
        }
    }

    function requestModeWithIntro(mode) {
        if (transitionInProgress)
            return
        pendingMode = mode
        if (!modeSelectorController.animationsEnabled) {
            finishModeTransition()
            return
        }
        transitionInProgress = true
        introOverlay.visible = true
        introPlayer.source = mode === "gaming"
            ? leosTheme.gamingIntroUrl
            : leosTheme.desktopIntroUrl
        introAudioOutput.muted = !modeSelectorController.soundsEnabled
        introTimeout.start()
        introPlayer.play()
    }

    function finishModeTransition() {
        if (pendingMode === "")
            return
        const mode = pendingMode
        pendingMode = ""
        transitionInProgress = false
        introTimeout.stop()
        introPlayer.stop()
        introOverlay.visible = false
        modeManager.requestMode(mode)
    }

    function handleGamepadAction(action) {
        if (transitionInProgress)
            return
        if (appearanceDialog.visible) {
            if (modeSelectorController.appearanceSetupRunning)
                return
            if (action === "left" || action === "right" || action === "up" || action === "down") {
                appearanceDialogFocusIndex = (appearanceDialogFocusIndex + 1) % 4
                if (appearanceDialogFocusIndex === 0)
                    appearanceColorAButton.forceActiveFocus()
                else if (appearanceDialogFocusIndex === 1)
                    appearanceColorBButton.forceActiveFocus()
                else if (appearanceDialogFocusIndex === 2)
                    applyAppearanceButton.forceActiveFocus()
                else
                    keepAppearanceButton.forceActiveFocus()
            } else if (action === "confirm") {
                if (appearanceDialogFocusIndex === 0)
                    initialColorADialog.open()
                else if (appearanceDialogFocusIndex === 1)
                    initialColorBDialog.open()
                else if (appearanceDialogFocusIndex === 2)
                    activateDesktopAppearance()
                else
                    keepCurrentDesktopAppearance()
            } else if (action === "back") {
                appearanceDialog.close()
            }
            return
        }
        if (transitionDialog.visible) {
            if (action === "confirm") {
                transitionDialog.close()
                window.requestModeWithIntro("gaming")
            } else if (action === "back") {
                transitionDialog.close()
            }
            return
        }

        if (action === "left" || action === "right") {
            if (desktopCard.activeFocus)
                gamingCard.forceActiveFocus()
            else
                desktopCard.forceActiveFocus()
        } else if (action === "confirm") {
            if (gamingCard.activeFocus)
                transitionDialog.open()
            else
                window.requestDesktopMode()
        }
    }

    ColorDialog {
        id: initialColorADialog
        title: "Choisir librement la couleur A"
        selectedColor: Qt.color(window.draftColorA)
        onAccepted: {
            window.draftColorA = window.colorToHex(selectedColor)
            window.draftColorAChosen = true
        }
    }

    ColorDialog {
        id: initialColorBDialog
        title: "Choisir librement la couleur B"
        selectedColor: Qt.color(window.draftColorB)
        onAccepted: {
            window.draftColorB = window.colorToHex(selectedColor)
            window.draftColorBChosen = true
        }
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: window.currentDate = new Date()
    }

    Rectangle {
        id: modeSelectorContent
        anchors.fill: parent
        color: window.color
        focus: true

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
                    color: window.colorAText
                    font.pixelSize: 10
                    font.letterSpacing: 1.5
                    Layout.alignment: Qt.AlignHCenter
                    topPadding: 4
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 104
                visible: !modeSelectorController.onboardingComplete
                radius: 15
                color: "#101923"
                border.color: "#254253"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 16

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 5

                        Label {
                            text: "BIENVENUE DANS LEOS"
                            color: window.colorAText
                            font.pixelSize: 11
                            font.weight: Font.Bold
                            font.letterSpacing: 1.5
                        }
                        Label {
                            text: "Un seul système, deux expériences : Desktop pour le quotidien et Gaming pour jouer."
                            color: "white"
                            font.pixelSize: 13
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Label {
                            text: "Tes applications restent ouvertes. Aucun réglage KDE ni logiciel facultatif n'est modifié sans ton accord."
                            color: window.muted
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }

                    Button {
                        text: "COMPRIS"
                        Layout.minimumWidth: 112
                        onClicked: modeSelectorController.completeOnboarding()
                        background: Rectangle {
                            radius: 8
                            color: "#17313d"
                            border.color: window.colorA
                        }
                        contentItem: Label {
                            text: "COMPRIS"
                            color: "white"
                            font.pixelSize: 10
                            font.weight: Font.Bold
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
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
                    onClicked: window.requestDesktopMode()
                    background: Rectangle {
                        radius: 22
                        color: desktopCard.down ? "#1a2630" : "#111720"
                        border.width: desktopCard.activeFocus ? 2 : 1
                        border.color: desktopCard.activeFocus ? window.colorA : "#303a49"
                    }
                    contentItem: ColumnLayout {
                        spacing: 15
                        Item { Layout.fillHeight: true }
                        Image {
                            source: leosTheme.desktopLogoUrl
                            asynchronous: true
                            smooth: true
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
                        border.color: gamingCard.activeFocus ? window.colorB : "#3a2b43"
                    }
                    contentItem: ColumnLayout {
                        spacing: 15
                        Item { Layout.fillHeight: true }
                        Image {
                            source: leosTheme.gamingLogoUrl
                            asynchronous: true
                            smooth: true
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
                color: window.colorBText
                font.pixelSize: 12
                Layout.alignment: Qt.AlignHCenter
            }
            Label {
                text: "Bazzite KDE · Une seule session · Aucune application ne sera fermée automatiquement"
                color: "#667184"
                font.pixelSize: 10
                Layout.alignment: Qt.AlignHCenter
            }
            Label {
                text: modeSelectorController.gamepadStatus
                color: "#596779"
                font.pixelSize: 9
                Layout.alignment: Qt.AlignHCenter
            }
        }

        Keys.onPressed: function(event) {
            if (window.transitionInProgress) {
                event.accepted = true
                return
            }
            if (event.key === Qt.Key_G) {
                transitionDialog.open()
                event.accepted = true
            } else if (event.key === Qt.Key_D) {
                window.requestDesktopMode()
                event.accepted = true
            } else if (event.key === Qt.Key_Left || event.key === Qt.Key_Right) {
                if (desktopCard.activeFocus)
                    gamingCard.forceActiveFocus()
                else
                    desktopCard.forceActiveFocus()
                event.accepted = true
            } else if (event.key === Qt.Key_Escape && appearanceDialog.visible) {
                appearanceDialog.close()
                event.accepted = true
            } else if (event.key === Qt.Key_G && appearanceDialog.visible) {
                appearanceDialog.close()
                transitionDialog.open()
                event.accepted = true
            } else if (event.key === Qt.Key_Escape && transitionDialog.visible) {
                transitionDialog.close()
                event.accepted = true
            }
        }
    }

    MediaPlayer {
        id: introPlayer
        audioOutput: AudioOutput {
            id: introAudioOutput
            muted: true
        }
        videoOutput: introVideoOutput
        onMediaStatusChanged: {
            if (mediaStatus === MediaPlayer.EndOfMedia ||
                    mediaStatus === MediaPlayer.InvalidMedia)
                window.finishModeTransition()
        }
        onErrorOccurred: function(error, errorString) {
            window.finishModeTransition()
        }
    }

    Timer {
        id: introTimeout
        interval: 9000
        repeat: false
        onTriggered: window.finishModeTransition()
    }

    Rectangle {
        id: introOverlay
        anchors.fill: parent
        color: "#000000"
        visible: false
        z: 1000
        VideoOutput {
            id: introVideoOutput
            anchors.fill: parent
            fillMode: VideoOutput.PreserveAspectFit
        }
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
        }
    }

    Connections {
        target: modeSelectorController
        function onGamepadAction(action) {
            window.handleGamepadAction(action)
        }
        function onAppearanceSetupFinished(succeeded, message) {
            appearanceStatusText.text = message
            if (succeeded) {
                appearanceDialog.close()
                window.requestModeWithIntro("desktop")
            }
        }
    }

    Dialog {
        id: appearanceDialog
        title: "Activer l'apparence LEOS"
        modal: true
        anchors.centerIn: parent
        closePolicy: Popup.NoAutoClose
        width: 520

        ColumnLayout {
            width: parent.width
            spacing: 14

            Label {
                text: "LEOS va appliquer ton dégradé personnalisé A/B aux ressources de marque compatibles, créer un schéma KDE correspondant et installer le fond, le style et le dock. Une sauvegarde KDE sera créée avant toute modification. Aucun accent ne sera imposé."
                color: "white"
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Button {
                    id: appearanceColorAButton
                    Layout.fillWidth: true
                    text: window.draftColorAChosen ? "Couleur A · " + window.draftColorA : "CHOISIR LA COULEUR A"
                    onClicked: initialColorADialog.open()
                    background: Rectangle {
                        radius: 8
                        color: window.themeColors.surface
                        border.color: window.colorA
                        border.width: appearanceColorAButton.activeFocus ? 2 : 1
                    }
                    contentItem: Label {
                        text: appearanceColorAButton.text
                        color: window.themeColors.text
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
                Button {
                    id: appearanceColorBButton
                    Layout.fillWidth: true
                    text: window.draftColorBChosen ? "Couleur B · " + window.draftColorB : "CHOISIR LA COULEUR B"
                    onClicked: initialColorBDialog.open()
                    background: Rectangle {
                        radius: 8
                        color: window.themeColors.surface
                        border.color: window.colorB
                        border.width: appearanceColorBButton.activeFocus ? 2 : 1
                    }
                    contentItem: Label {
                        text: appearanceColorBButton.text
                        color: window.themeColors.text
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }
            Label {
                text: (!window.draftColorAChosen || !window.draftColorBChosen)
                      ? "Les couleurs visibles au départ sont un aperçu historique, pas une sélection. Choisis librement A et B."
                      : "Dégradé personnalisé LEOS · A vers B"
                color: window.muted
                font.pixelSize: 10
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 10
                radius: 5
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: window.draftColorA }
                    GradientStop { position: 1.0; color: window.draftColorB }
                }
            }
            Label {
                text: "Si les deux couleurs sont peu contrastées, LEOS adapte le texte sans modifier A ni B."
                color: window.muted
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                text: "Si la configuration actuelle comporte plusieurs panneaux ou ne peut pas être sauvegardée en sécurité, LEOS n'y touchera pas et expliquera pourquoi."
                color: window.muted
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                id: appearanceStatusText
                text: modeSelectorController.appearanceSetupRunning
                      ? "Préparation de l'apparence LEOS…"
                      : (window.draftColorAChosen && window.draftColorBChosen
                         ? "Tu pourras restaurer la disposition précédente depuis les sauvegardes Plasma."
                         : "Choisis une couleur A et une couleur B avant l’activation.")
                color: window.colorAText
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Button {
                id: applyAppearanceButton
                text: modeSelectorController.appearanceSetupRunning
                      ? "APPLICATION EN COURS…"
                      : "ACTIVER L'APPARENCE LEOS"
                enabled: !modeSelectorController.appearanceSetupRunning && window.draftColorAChosen && window.draftColorBChosen
                Layout.fillWidth: true
                onClicked: window.activateDesktopAppearance()
                background: Rectangle {
                    radius: 9
                    color: applyAppearanceButton.enabled ? "#17313d" : "#17212a"
                    border.color: applyAppearanceButton.activeFocus ? window.colorB : window.colorA
                }
                contentItem: Label {
                    text: applyAppearanceButton.text
                    color: "white"
                    font.weight: Font.Bold
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            Button {
                id: keepAppearanceButton
                text: "GARDER MON BUREAU ACTUEL"
                enabled: !modeSelectorController.appearanceSetupRunning
                Layout.fillWidth: true
                onClicked: window.keepCurrentDesktopAppearance()
                background: Rectangle {
                    radius: 9
                    color: "transparent"
                    border.color: keepAppearanceButton.activeFocus ? window.colorA : "#485366"
                }
                contentItem: Label {
                    text: keepAppearanceButton.text
                    color: "white"
                    horizontalAlignment: Text.AlignHCenter
                }
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
                id: continueGamingButton
                text: "CONTINUER VERS GAMING"
                Layout.fillWidth: true
                onClicked: {
                    transitionDialog.close()
                    window.requestModeWithIntro("gaming")
                }
                background: Rectangle { radius: 9; color: "#17313d"; border.color: window.colorA }
                contentItem: Label {
                    text: continueGamingButton.text
                    color: "white"
                    font.weight: Font.Bold
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }

}
