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
    property bool firstRunIdentityPromptVisible: identityDialog.visible
    color: themeColors.background

    property color colorA: Qt.color(draftColorA)
    property color colorB: Qt.color(draftColorB)
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
    property int identityDialogFocusIndex: 0

    Component.onCompleted: {
        if (!leosTheme.themeColorsConfigured) {
            Qt.callLater(function() {
                identityDialog.open()
                identityColorAButton.forceActiveFocus()
            })
        }
    }

    function requestDesktopMode() {
        if (!leosTheme.themeColorsConfigured) {
            identityDialog.open()
            identityColorAButton.forceActiveFocus()
            return
        }
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

    function requestGamingMode() {
        if (!leosTheme.themeColorsConfigured) {
            identityDialog.open()
            identityColorAButton.forceActiveFocus()
            return
        }
        transitionDialog.open()
    }

    function applyIdentityColors() {
        if (!draftColorAChosen || !draftColorBChosen) {
            identityStatusText.text = "Choisis les deux couleurs A et B pour définir l'identité de LEOS."
            return false
        }
        themeColorNotice = leosTheme.setThemeColors(draftColorA, draftColorB)
        if (leosTheme.themeColorsConfigured) {
            identityDialog.close()
            return true
        }
        identityStatusText.text = themeColorNotice
        return false
    }

    function requestModeWithIntro(mode) {
        if (transitionInProgress)
            return
        pendingMode = mode
        if (!modeSelectorController.animationsEnabled) {
            finishModeTransition()
            return
        }
        const introUrl = mode === "gaming"
            ? leosTheme.gamingIntroUrl
            : leosTheme.desktopIntroUrl
        // On a fresh profile the custom intro may still be generated in the
        // background. Never leave the user on a black overlay while waiting.
        if (!introUrl) {
            finishModeTransition()
            return
        }
        transitionInProgress = true
        introOverlay.visible = true
        introPlayer.source = introUrl
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
        if (identityDialog.visible) {
            if (action === "left" || action === "right" || action === "up" || action === "down") {
                identityDialogFocusIndex = (identityDialogFocusIndex + 1) % 3
                if (identityDialogFocusIndex === 0)
                    identityColorAButton.forceActiveFocus()
                else if (identityDialogFocusIndex === 1)
                    identityColorBButton.forceActiveFocus()
                else
                    identityApplyButton.forceActiveFocus()
            } else if (action === "confirm") {
                if (identityDialogFocusIndex === 0)
                    initialColorADialog.open()
                else if (identityDialogFocusIndex === 1)
                    initialColorBDialog.open()
                else
                    applyIdentityColors()
            }
            return
        }
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
                window.requestGamingMode()
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
            color: window.colorA; opacity: 0.14
        }
        Rectangle {
            width: 560; height: 560; radius: 280
            x: -width * 0.4; y: parent.height * 0.55
            color: window.colorB; opacity: 0.12
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: window.width < 1120 ? 24 : 48
            spacing: window.height < 760 ? 14 : 20

            ColumnLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 5

                Label {
                    text: "LEOS"
                    color: window.themeColors.text
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
                    color: window.themeColors.text
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
                    color: modeManager.lastMode === "gaming" ? window.colorBText : window.colorAText
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
                color: window.themeColors.surface
                border.color: window.colorA

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
                            color: window.themeColors.text
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
                            color: window.themeColors.surface_elevated
                            border.color: window.colorA
                        }
                        contentItem: Label {
                            text: "COMPRIS"
                            color: window.themeColors.text
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
                    Accessible.role: Accessible.Button
                    Accessible.name: "LEOS Desktop"
                    Accessible.description: "Bureau, création et quotidien dans un environnement KDE personnalisé."
                    onClicked: window.requestDesktopMode()
                    background: Rectangle {
                        radius: 22
                        color: desktopCard.down || desktopCard.activeFocus || desktopCard.hovered
                               ? window.themeColors.surface_elevated : window.themeColors.surface
                        border.width: desktopCard.activeFocus ? 2 : (desktopCard.hovered ? 1.5 : 1)
                        border.color: desktopCard.activeFocus ? window.colorA
                                      : desktopCard.hovered ? window.colorAText
                                      : window.themeColors.border
                        Behavior on color {
                            enabled: modeSelectorController.animationsEnabled
                            ColorAnimation { duration: 180; easing.type: Easing.OutCubic }
                        }
                        Behavior on border.color {
                            enabled: modeSelectorController.animationsEnabled
                            ColorAnimation { duration: 180; easing.type: Easing.OutCubic }
                        }
                        Behavior on border.width {
                            enabled: modeSelectorController.animationsEnabled
                            NumberAnimation { duration: 150; easing.type: Easing.OutCubic }
                        }

                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 1
                            radius: parent.radius - 1
                            color: window.colorA
                            opacity: desktopCard.activeFocus ? 0.10 : (desktopCard.hovered ? 0.055 : 0)
                            Behavior on opacity {
                                enabled: modeSelectorController.animationsEnabled
                                NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
                            }
                        }
                        Rectangle {
                            anchors { left: parent.left; right: parent.right; top: parent.top }
                            anchors.leftMargin: 30
                            anchors.rightMargin: 30
                            height: 2
                            radius: 1
                            visible: desktopCard.activeFocus || desktopCard.hovered
                            gradient: Gradient {
                                GradientStop { position: 0; color: window.colorA }
                                GradientStop { position: 1; color: window.colorB }
                            }
                        }
                    }
                    contentItem: ColumnLayout {
                        spacing: 13
                        Item { Layout.fillHeight: true }
                        RowLayout {
                            Layout.alignment: Qt.AlignHCenter
                            spacing: 8
                            Rectangle {
                                Layout.preferredWidth: 22
                                Layout.preferredHeight: 2
                                radius: 1
                                color: window.colorA
                            }
                            Label {
                                text: "MODE 01 · QUOTIDIEN"
                                color: window.colorAText
                                font.pixelSize: 10
                                font.weight: Font.DemiBold
                                font.letterSpacing: 1.4
                            }
                        }
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
                            color: window.themeColors.text
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
                            color: window.themeColors.muted_text
                            font.pixelSize: 10
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Rectangle {
                            Layout.preferredWidth: 220
                            Layout.preferredHeight: 38
                            Layout.alignment: Qt.AlignHCenter
                            radius: 9
                            color: window.themeColors.surface
                            border.width: desktopCard.activeFocus ? 1.5 : 1
                            border.color: desktopCard.activeFocus || desktopCard.hovered ? window.colorA : window.themeColors.border
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 13
                                anchors.rightMargin: 13
                                Label {
                                    text: "OUVRIR DESKTOP"
                                    color: window.colorAText
                                    font.pixelSize: 10
                                    font.weight: Font.Bold
                                    font.letterSpacing: 1
                                }
                                Item { Layout.fillWidth: true }
                                Label {
                                    text: "→"
                                    color: window.colorAText
                                    font.pixelSize: 16
                                }
                            }
                        }
                        Item { Layout.fillHeight: true }
                    }
                }

                Button {
                    id: gamingCard
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Accessible.role: Accessible.Button
                    Accessible.name: "LEOS Gaming"
                    Accessible.description: "Bibliothèque de jeux, émulation et navigation à la manette."
                    onClicked: window.requestGamingMode()
                    background: Rectangle {
                        radius: 22
                        color: gamingCard.down || gamingCard.activeFocus || gamingCard.hovered
                               ? window.themeColors.surface_elevated : window.themeColors.surface
                        border.width: gamingCard.activeFocus ? 2 : (gamingCard.hovered ? 1.5 : 1)
                        border.color: gamingCard.activeFocus ? window.colorB
                                      : gamingCard.hovered ? window.colorBText
                                      : window.themeColors.border
                        Behavior on color {
                            enabled: modeSelectorController.animationsEnabled
                            ColorAnimation { duration: 180; easing.type: Easing.OutCubic }
                        }
                        Behavior on border.color {
                            enabled: modeSelectorController.animationsEnabled
                            ColorAnimation { duration: 180; easing.type: Easing.OutCubic }
                        }
                        Behavior on border.width {
                            enabled: modeSelectorController.animationsEnabled
                            NumberAnimation { duration: 150; easing.type: Easing.OutCubic }
                        }

                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 1
                            radius: parent.radius - 1
                            color: window.colorB
                            opacity: gamingCard.activeFocus ? 0.10 : (gamingCard.hovered ? 0.055 : 0)
                            Behavior on opacity {
                                enabled: modeSelectorController.animationsEnabled
                                NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
                            }
                        }
                        Rectangle {
                            anchors { left: parent.left; right: parent.right; top: parent.top }
                            anchors.leftMargin: 30
                            anchors.rightMargin: 30
                            height: 2
                            radius: 1
                            visible: gamingCard.activeFocus || gamingCard.hovered
                            gradient: Gradient {
                                GradientStop { position: 0; color: window.colorA }
                                GradientStop { position: 1; color: window.colorB }
                            }
                        }
                    }
                    contentItem: ColumnLayout {
                        spacing: 13
                        Item { Layout.fillHeight: true }
                        RowLayout {
                            Layout.alignment: Qt.AlignHCenter
                            spacing: 8
                            Rectangle {
                                Layout.preferredWidth: 22
                                Layout.preferredHeight: 2
                                radius: 1
                                color: window.colorB
                            }
                            Label {
                                text: "MODE 02 · JEUX"
                                color: window.colorBText
                                font.pixelSize: 10
                                font.weight: Font.DemiBold
                                font.letterSpacing: 1.4
                            }
                        }
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
                            color: window.themeColors.text
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
                            text: "Tes jeux et lanceurs réunis au même endroit"
                            color: window.themeColors.muted_text
                            font.pixelSize: 10
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Rectangle {
                            Layout.preferredWidth: 220
                            Layout.preferredHeight: 38
                            Layout.alignment: Qt.AlignHCenter
                            radius: 9
                            color: window.themeColors.surface
                            border.width: gamingCard.activeFocus ? 1.5 : 1
                            border.color: gamingCard.activeFocus || gamingCard.hovered ? window.colorB : window.themeColors.border
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 13
                                anchors.rightMargin: 13
                                Label {
                                    text: "OUVRIR GAMING"
                                    color: window.colorBText
                                    font.pixelSize: 10
                                    font.weight: Font.Bold
                                    font.letterSpacing: 1
                                }
                                Item { Layout.fillWidth: true }
                                Label {
                                    text: "→"
                                    color: window.colorBText
                                    font.pixelSize: 16
                                }
                            }
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
                text: "LEOS · Une seule session Desktop/Gaming · Aucune application ne sera fermée automatiquement"
                color: window.themeColors.muted_text
                font.pixelSize: 10
                Layout.alignment: Qt.AlignHCenter
            }
            Label {
                text: modeSelectorController.gamepadStatus
                color: window.themeColors.muted_text
                font.pixelSize: 9
                Layout.alignment: Qt.AlignHCenter
            }
        }

        Keys.onPressed: function(event) {
            if (window.transitionInProgress) {
                event.accepted = true
                return
            }
            if (identityDialog.visible) {
                event.accepted = true
            } else if (event.key === Qt.Key_G) {
                window.requestGamingMode()
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
        id: identityDialog
        title: "Bienvenue dans LEOS — identité visuelle"
        modal: true
        anchors.centerIn: parent
        closePolicy: Popup.NoAutoClose
        width: 580

        ColumnLayout {
            width: parent.width
            spacing: 14
            Label {
                text: "Avant de choisir ton environnement, définis les deux couleurs qui signeront LEOS. Elles seront reprises dans les logos, fonds, interfaces, icônes et le style du bureau. Tu gardes le contrôle : aucune couleur n'est présélectionnée comme identité."
                color: window.themeColors.text
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Button {
                    id: identityColorAButton
                    Layout.fillWidth: true
                    text: window.draftColorAChosen ? "COULEUR A · " + window.draftColorA : "CHOISIR LA COULEUR A"
                    onClicked: initialColorADialog.open()
                    background: Rectangle { radius: 8; color: window.themeColors.surface; border.color: window.colorA }
                    contentItem: Label { text: identityColorAButton.text; color: window.themeColors.text; horizontalAlignment: Text.AlignHCenter }
                }
                Button {
                    id: identityColorBButton
                    Layout.fillWidth: true
                    text: window.draftColorBChosen ? "COULEUR B · " + window.draftColorB : "CHOISIR LA COULEUR B"
                    onClicked: initialColorBDialog.open()
                    background: Rectangle { radius: 8; color: window.themeColors.surface; border.color: window.colorB }
                    contentItem: Label { text: identityColorBButton.text; color: window.themeColors.text; horizontalAlignment: Text.AlignHCenter }
                }
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 12
                radius: 6
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: window.draftColorA }
                    GradientStop { position: 1.0; color: window.draftColorB }
                }
            }
            Label {
                id: identityStatusText
                text: (!window.draftColorAChosen || !window.draftColorBChosen)
                      ? "Choisis une couleur A et une couleur B. Les tons métalliques visibles ici sont de simples repères neutres."
                      : "Ton dégradé LEOS est prêt. Tu peux maintenant choisir Desktop ou Gaming."
                color: window.colorAText
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Button {
                id: identityApplyButton
                text: "VALIDER L'IDENTITÉ LEOS"
                enabled: window.draftColorAChosen && window.draftColorBChosen
                Layout.fillWidth: true
                onClicked: window.applyIdentityColors()
                background: Rectangle {
                    radius: 9
                    color: identityApplyButton.enabled ? window.themeColors.surface_elevated : window.themeColors.surface
                    border.color: identityApplyButton.activeFocus ? window.colorB : window.colorA
                }
                contentItem: Label { text: identityApplyButton.text; color: window.themeColors.text; font.weight: Font.Bold; horizontalAlignment: Text.AlignHCenter }
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
                color: window.themeColors.text
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
                      ? "L'aperçu initial reste métallique et neutre. Choisis librement A et B : aucune paire de couleurs n'est imposée."
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
                    color: applyAppearanceButton.enabled ? window.themeColors.surface_elevated : window.themeColors.surface
                    border.color: applyAppearanceButton.activeFocus ? window.colorB : window.colorA
                }
                contentItem: Label {
                    text: applyAppearanceButton.text
                    color: window.themeColors.text
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
                    border.color: keepAppearanceButton.activeFocus ? window.colorA : window.themeColors.border
                }
                contentItem: Label {
                    text: keepAppearanceButton.text
                    color: window.themeColors.text
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
                color: window.themeColors.text
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
                background: Rectangle { radius: 9; color: window.themeColors.surface_elevated; border.color: window.colorA }
                contentItem: Label {
                    text: continueGamingButton.text
                    color: window.themeColors.text
                    font.weight: Font.Bold
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }

}
