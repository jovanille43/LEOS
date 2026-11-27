import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtMultimedia
import "../../branding/qml" as Branding

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
    property bool gamingHandoffPending: false
    // The recommended LEOS profile action is focused first for keyboard and gamepad users.
    property int appearanceDialogFocusIndex: 2
    property int identityDialogFocusIndex: 0
    property var firstRunSteps: [
        {
            name: "IDENTITÉ A/B",
            detail: leosTheme.themeColorsConfigured ? "DÉFINIE" : "À CONFIGURER",
            complete: leosTheme.themeColorsConfigured
        },
        {
            name: "GUIDE DE BIENVENUE",
            detail: modeSelectorController.onboardingComplete ? "TERMINÉ" : "À DÉCOUVRIR",
            complete: modeSelectorController.onboardingComplete
        },
        {
            name: "PROFIL DESKTOP",
            detail: modeSelectorController.desktopAppearanceStatus === "applied"
                ? "ACTIVÉ"
                : modeSelectorController.desktopAppearanceStatus === "skipped"
                    ? "IGNORÉE À TA DEMANDE" : "À CHOISIR",
            complete: modeSelectorController.desktopAppearanceStatus === "applied"
                || modeSelectorController.desktopAppearanceStatus === "skipped"
        }
    ]
    property int firstRunCompletedCount: firstRunSteps.filter(function(step) {
        return step.complete
    }).length


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
            appearanceDialogFocusIndex = 2
            appearanceDialog.open()
            applyAppearanceButton.forceActiveFocus()
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
        modeSelectorController.completeOnboarding()
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
        gamingHandoffPending = false
        introHandoffCrossfade.stop()
        introHandoffScreen.visible = false
        introHandoffScreen.opacity = 0
        introVideoOutput.visible = true
        introVideoOutput.opacity = 1
        introOverlay.visible = true
        introOverlay.opacity = 1
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
        introTimeout.stop()
        introPlayer.stop()
        if (mode === "gaming") {
            // Keep a branded cover over Plasma until Gaming confirms that its
            // fullscreen QML surface has rendered a frame.
            const canCrossfade = introOverlay.visible && introVideoOutput.visible
            transitionInProgress = true
            gamingHandoffPending = true
            introOverlay.visible = true
            introOverlay.opacity = 1
            introHandoffScreen.visible = true
            introHandoffScreen.opacity = canCrossfade ? 0 : 1
            if (canCrossfade) {
                introVideoOutput.opacity = 1
                introHandoffCrossfade.start()
            } else {
                introVideoOutput.visible = false
                introVideoOutput.opacity = 1
            }
            modeManager.requestMode(mode)
            return
        }
        transitionInProgress = false
        gamingHandoffPending = false
        introHandoffCrossfade.stop()
        introHandoffScreen.visible = false
        introHandoffScreen.opacity = 0
        introVideoOutput.visible = true
        introVideoOutput.opacity = 1
        introOverlay.opacity = 1
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

        Branding.ParticleBackdrop {
            anchors.fill: parent
            z: 0
            colorA: window.colorA
            colorB: window.colorB
            particleOpacity: 0.70
            motionEnabled: modeSelectorController.animationsEnabled
        }

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
                    font.pixelSize: 13
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
                    font.pixelSize: 12
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
                            font.pixelSize: 13
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
                            font.pixelSize: 12
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
                            font.pixelSize: 12
                            font.weight: Font.Bold
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 82
                radius: 14
                color: window.themeColors.surface
                border.color: window.themeColors.border
                Accessible.role: Accessible.Grouping
                Accessible.name: "État du premier démarrage : "
                    + window.firstRunCompletedCount + " étapes sur 3 terminées."

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 7

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: "ÉTAT DU PREMIER DÉMARRAGE"
                            color: window.themeColors.text
                            font.pixelSize: 12
                            font.weight: Font.Bold
                            font.letterSpacing: 1.1
                        }
                        Item { Layout.fillWidth: true }
                        Label {
                            text: window.firstRunCompletedCount + "/3 ÉTAPES"
                            color: window.colorAText
                            font.pixelSize: 11
                            font.weight: Font.Bold
                            font.letterSpacing: 0.8
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 8
                        Repeater {
                            model: window.firstRunSteps
                            delegate: Rectangle {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: 8
                                color: window.themeColors.surface_elevated
                                border.width: 1
                                border.color: modelData.complete
                                    ? window.colorA : window.themeColors.border
                                Accessible.role: Accessible.Grouping
                                Accessible.name: modelData.name + " : " + modelData.detail

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 10
                                    anchors.rightMargin: 8
                                    spacing: 1
                                    Label {
                                        text: modelData.name
                                        color: window.muted
                                        font.pixelSize: 10
                                        font.weight: Font.DemiBold
                                        font.letterSpacing: 0.4
                                        Layout.fillWidth: true
                                        elide: Text.ElideRight
                                    }
                                    Label {
                                        text: modelData.detail
                                        color: modelData.complete
                                            ? window.colorAText : window.muted
                                        font.pixelSize: 12
                                        font.weight: Font.Bold
                                        Layout.fillWidth: true
                                        elide: Text.ElideRight
                                    }
                                }
                            }
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
                        clip: true
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
                                GradientStop { position: 1; color: window.colorA }
                            }
                        }
                        Rectangle {
                            anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                            width: 3
                            radius: 2
                            opacity: desktopCard.activeFocus ? 0.92 : 0.45
                            color: window.colorA
                        }

                    }
                    contentItem: Item {
                        implicitWidth: window.width < 980 ? 280 : 520
                        implicitHeight: window.height < 760 ? 300 : 340
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: window.width < 980 ? 18 : 27
                            spacing: 12
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 9
                                Rectangle {
                                    Layout.preferredWidth: 31
                                    Layout.preferredHeight: 27
                                    radius: 8
                                    color: Qt.rgba(window.colorA.r, window.colorA.g, window.colorA.b, 0.13)
                                    border.color: window.colorA
                                    border.width: 1
                                    Label {
                                        anchors.centerIn: parent
                                        text: "01"
                                        color: window.colorAText
                                        font.pixelSize: 12
                                        font.weight: Font.Bold
                                        font.letterSpacing: 0.8
                                    }
                                }
                                ColumnLayout {
                                    spacing: 1
                                    Label {
                                        text: "MODE 01 · QUOTIDIEN"
                                        color: window.colorAText
                                        font.pixelSize: 12
                                        font.weight: Font.DemiBold
                                        font.letterSpacing: 1.35
                                    }
                                    Label {
                                        text: "ESPACE DE TRAVAIL"
                                        color: window.muted
                                        font.pixelSize: 10
                                        font.letterSpacing: 1.5
                                    }
                                }
                                Item { Layout.fillWidth: true }
                                Label {
                                    text: "DESKTOP"
                                    color: window.muted
                                    font.pixelSize: 11
                                    font.weight: Font.DemiBold
                                    font.letterSpacing: 1.2
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 1
                                color: window.themeColors.border
                                opacity: 0.8
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 8
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    spacing: 7
                                    Label {
                                        text: "LEOS DESKTOP"
                                        color: window.themeColors.text
                                        font.pixelSize: window.width < 980 ? 21 : 29
                                        font.weight: Font.Bold
                                        font.letterSpacing: 1.0
                                        Layout.fillWidth: true
                                        wrapMode: Text.WordWrap
                                    }
                                    Label {
                                        text: "Un bureau KDE personnalisé, fluide et élégant."
                                        color: window.muted
                                        font.pixelSize: window.width < 980 ? 11 : 13
                                        Layout.fillWidth: true
                                        wrapMode: Text.WordWrap
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 1
                                        color: window.colorA
                                        opacity: 0.28
                                    }
                                    RowLayout {
                                        spacing: 8
                                        Rectangle { Layout.preferredWidth: 5; Layout.preferredHeight: 5; radius: 3; color: window.colorA }
                                        Label {
                                            text: "PERSONNALISATION KDE"
                                            color: window.themeColors.text
                                            font.pixelSize: 11
                                            font.weight: Font.DemiBold
                                            font.letterSpacing: 0.6
                                            Layout.fillWidth: true
                                            wrapMode: Text.WordWrap
                                        }
                                    }
                                    RowLayout {
                                        spacing: 8
                                        Rectangle { Layout.preferredWidth: 5; Layout.preferredHeight: 5; radius: 3; color: window.colorA }
                                        Label {
                                            text: "MULTITÂCHE & FENÊTRES"
                                            color: window.themeColors.text
                                            font.pixelSize: 11
                                            font.weight: Font.DemiBold
                                            font.letterSpacing: 0.6
                                            Layout.fillWidth: true
                                            wrapMode: Text.WordWrap
                                        }
                                    }
                                    RowLayout {
                                        spacing: 8
                                        Rectangle { Layout.preferredWidth: 5; Layout.preferredHeight: 5; radius: 3; color: window.colorA }
                                        Label {
                                            text: "CRÉATION & QUOTIDIEN"
                                            color: window.themeColors.text
                                            font.pixelSize: 11
                                            font.weight: Font.DemiBold
                                            font.letterSpacing: 0.6
                                            Layout.fillWidth: true
                                            wrapMode: Text.WordWrap
                                        }
                                    }
                                    Item { Layout.fillHeight: true }
                                }
                                Item {
                                    Layout.preferredWidth: window.width < 980 ? 116 : 196
                                    Layout.minimumWidth: 104
                                    Layout.fillHeight: true
                                    Rectangle {
                                        width: Math.min(parent.width * 0.94, parent.height * 0.90)
                                        height: width
                                        radius: width / 2
                                        anchors.centerIn: parent
                                        color: window.colorA
                                        opacity: desktopCard.activeFocus ? 0.13 : 0.055
                                        Behavior on opacity {
                                            enabled: modeSelectorController.animationsEnabled
                                            NumberAnimation { duration: 220; easing.type: Easing.OutCubic }
                                        }
                                    }
                                    Rectangle {
                                        width: Math.min(parent.width * 0.94, parent.height * 0.90)
                                        height: width
                                        radius: width / 2
                                        anchors.centerIn: parent
                                        color: "transparent"
                                        border.width: 1
                                        border.color: window.colorA
                                        opacity: desktopCard.activeFocus || desktopCard.hovered ? 0.36 : 0.18
                                    }
                                    Label {
                                        anchors.centerIn: parent
                                        text: "01"
                                        color: window.colorA
                                        opacity: desktopCardLogo.status === Image.Ready ? 0 : 0.22
                                        font.pixelSize: window.width < 980 ? 56 : 78
                                        font.weight: Font.Light
                                        font.letterSpacing: -3
                                    }
                                    Image {
                                        id: desktopCardLogo
                                        anchors.centerIn: parent
                                        source: leosTheme.desktopLogoUrl
                                        asynchronous: true
                                        smooth: true
                                        fillMode: Image.PreserveAspectFit
                                        width: parent.width * 1.02
                                        height: parent.height * 0.92
                                        visible: status === Image.Ready
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 46
                                radius: 11
                                color: desktopCard.activeFocus || desktopCard.hovered ? window.themeColors.surface_elevated : window.themeColors.surface
                                border.width: desktopCard.activeFocus ? 1.5 : 1
                                border.color: desktopCard.activeFocus || desktopCard.hovered ? window.colorA : window.themeColors.border
                                Behavior on color {
                                    enabled: modeSelectorController.animationsEnabled
                                    ColorAnimation { duration: 160; easing.type: Easing.OutCubic }
                                }
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 15
                                    anchors.rightMargin: 13
                                    Label {
                                        text: "OUVRIR DESKTOP"
                                        color: window.colorAText
                                        font.pixelSize: 12
                                        font.weight: Font.Bold
                                        font.letterSpacing: 1.1
                                    }
                                    Item { Layout.fillWidth: true }
                                    Label { text: "ACCÉDER"; color: window.muted; font.pixelSize: 8; font.weight: Font.DemiBold; font.letterSpacing: 1 }
                                    Label { text: "→"; color: window.colorAText; font.pixelSize: 18; font.weight: Font.DemiBold }
                                }
                            }
                        }
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
                        clip: true
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
                        Rectangle {
                            anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                            width: 3
                            radius: 2
                            opacity: gamingCard.activeFocus ? 1 : 0.65
                            gradient: Gradient { GradientStop { position: 0; color: window.colorA } GradientStop { position: 1; color: window.colorB } }
                        }

                    }
                    contentItem: Item {
                        implicitWidth: window.width < 980 ? 280 : 520
                        implicitHeight: window.height < 760 ? 300 : 340
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: window.width < 980 ? 18 : 27
                            spacing: 12
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 9
                                Rectangle {
                                    Layout.preferredWidth: 31
                                    Layout.preferredHeight: 27
                                    radius: 8
                                    color: Qt.rgba(window.colorB.r, window.colorB.g, window.colorB.b, 0.13)
                                    border.color: window.colorB
                                    border.width: 1
                                    Label {
                                        anchors.centerIn: parent
                                        text: "02"
                                        color: window.colorBText
                                        font.pixelSize: 12
                                        font.weight: Font.Bold
                                        font.letterSpacing: 0.8
                                    }
                                }
                                ColumnLayout {
                                    spacing: 1
                                    Label {
                                        text: "MODE 02 · JEUX"
                                        color: window.colorBText
                                        font.pixelSize: 12
                                        font.weight: Font.DemiBold
                                        font.letterSpacing: 1.35
                                    }
                                    Label {
                                        text: "EXPÉRIENCE IMMERSIVE"
                                        color: window.muted
                                        font.pixelSize: 10
                                        font.letterSpacing: 1.5
                                    }
                                }
                                Item { Layout.fillWidth: true }
                                Label {
                                    text: "GAMING"
                                    color: window.muted
                                    font.pixelSize: 11
                                    font.weight: Font.DemiBold
                                    font.letterSpacing: 1.2
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 1
                                gradient: Gradient {
                                    GradientStop { position: 0; color: window.colorA }
                                    GradientStop { position: 1; color: window.colorB }
                                }
                                opacity: 0.65
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 8
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    spacing: 7
                                    Label {
                                        text: "LEOS GAMING"
                                        color: window.themeColors.text
                                        font.pixelSize: window.width < 980 ? 21 : 29
                                        font.weight: Font.Bold
                                        font.letterSpacing: 1.0
                                        Layout.fillWidth: true
                                        wrapMode: Text.WordWrap
                                    }
                                    Label {
                                        text: "Tes jeux au même endroit, prêts à être lancés."
                                        color: window.muted
                                        font.pixelSize: window.width < 980 ? 11 : 13
                                        Layout.fillWidth: true
                                        wrapMode: Text.WordWrap
                                    }
                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 1
                                        gradient: Gradient {
                                            GradientStop { position: 0; color: window.colorA }
                                            GradientStop { position: 1; color: window.colorB }
                                        }
                                        opacity: 0.45
                                    }
                                    RowLayout {
                                        spacing: 8
                                        Rectangle {
                                            Layout.preferredWidth: 5; Layout.preferredHeight: 5; radius: 3
                                            gradient: Gradient { GradientStop { position: 0; color: window.colorA } GradientStop { position: 1; color: window.colorB } }
                                        }
                                        Label {
                                            text: "JEUX PC & LANCEURS"
                                            color: window.themeColors.text
                                            font.pixelSize: 11
                                            font.weight: Font.DemiBold
                                            font.letterSpacing: 0.6
                                            Layout.fillWidth: true
                                            wrapMode: Text.WordWrap
                                        }
                                    }
                                    RowLayout {
                                        spacing: 8
                                        Rectangle {
                                            Layout.preferredWidth: 5; Layout.preferredHeight: 5; radius: 3
                                            gradient: Gradient { GradientStop { position: 0; color: window.colorA } GradientStop { position: 1; color: window.colorB } }
                                        }
                                        Label {
                                            text: "ÉMULATION CENTRALISÉE"
                                            color: window.themeColors.text
                                            font.pixelSize: 11
                                            font.weight: Font.DemiBold
                                            font.letterSpacing: 0.6
                                            Layout.fillWidth: true
                                            wrapMode: Text.WordWrap
                                        }
                                    }
                                    RowLayout {
                                        spacing: 8
                                        Rectangle {
                                            Layout.preferredWidth: 5; Layout.preferredHeight: 5; radius: 3
                                            gradient: Gradient { GradientStop { position: 0; color: window.colorA } GradientStop { position: 1; color: window.colorB } }
                                        }
                                        Label {
                                            text: "NAVIGATION À LA MANETTE"
                                            color: window.themeColors.text
                                            font.pixelSize: 11
                                            font.weight: Font.DemiBold
                                            font.letterSpacing: 0.6
                                            Layout.fillWidth: true
                                            wrapMode: Text.WordWrap
                                        }
                                    }
                                    Item { Layout.fillHeight: true }
                                }
                                Item {
                                    Layout.preferredWidth: window.width < 980 ? 116 : 196
                                    Layout.minimumWidth: 104
                                    Layout.fillHeight: true
                                    Rectangle {
                                        width: Math.min(parent.width * 0.94, parent.height * 0.90)
                                        height: width
                                        radius: width / 2
                                        anchors.centerIn: parent
                                        color: window.colorB
                                        opacity: gamingCard.activeFocus ? 0.14 : 0.07
                                        Behavior on opacity {
                                            enabled: modeSelectorController.animationsEnabled
                                            NumberAnimation { duration: 220; easing.type: Easing.OutCubic }
                                        }
                                    }
                                    Rectangle {
                                        width: Math.min(parent.width * 0.94, parent.height * 0.90)
                                        height: width
                                        radius: width / 2
                                        anchors.centerIn: parent
                                        color: "transparent"
                                        border.width: 1
                                        border.color: window.colorB
                                        opacity: gamingCard.activeFocus || gamingCard.hovered ? 0.42 : 0.22
                                    }
                                    Rectangle {
                                        width: Math.min(parent.width * 0.79, parent.height * 0.76)
                                        height: width
                                        radius: width / 2
                                        anchors.centerIn: parent
                                        color: "transparent"
                                        border.width: 1
                                        border.color: window.colorA
                                        opacity: 0.17
                                    }
                                    Label {
                                        anchors.centerIn: parent
                                        text: "02"
                                        color: window.colorB
                                        opacity: gamingCardLogo.status === Image.Ready ? 0 : 0.22
                                        font.pixelSize: window.width < 980 ? 56 : 78
                                        font.weight: Font.Light
                                        font.letterSpacing: -3
                                    }
                                    Image {
                                        id: gamingCardLogo
                                        anchors.centerIn: parent
                                        source: leosTheme.gamingLogoUrl
                                        asynchronous: true
                                        smooth: true
                                        fillMode: Image.PreserveAspectFit
                                        width: parent.width * 1.02
                                        height: parent.height * 0.92
                                        visible: status === Image.Ready
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 46
                                radius: 11
                                color: gamingCard.activeFocus || gamingCard.hovered ? window.themeColors.surface_elevated : window.themeColors.surface
                                border.width: gamingCard.activeFocus ? 1.5 : 1
                                border.color: gamingCard.activeFocus || gamingCard.hovered ? window.colorB : window.themeColors.border
                                Behavior on color {
                                    enabled: modeSelectorController.animationsEnabled
                                    ColorAnimation { duration: 160; easing.type: Easing.OutCubic }
                                }
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 15
                                    anchors.rightMargin: 13
                                    Label {
                                        text: "OUVRIR GAMING"
                                        color: window.colorBText
                                        font.pixelSize: 12
                                        font.weight: Font.Bold
                                        font.letterSpacing: 1.1
                                    }
                                    Item { Layout.fillWidth: true }
                                    Label { text: "JOUER"; color: window.muted; font.pixelSize: 8; font.weight: Font.DemiBold; font.letterSpacing: 1 }
                                    Label { text: "→"; color: window.colorBText; font.pixelSize: 18; font.weight: Font.DemiBold }
                                }
                            }
                        }
                    }
                }
            }

            Label {
                text: modeManager.status
                color: window.colorBText
                font.pixelSize: 14
                Layout.alignment: Qt.AlignHCenter
            }
            Label {
                text: "LEOS · Une seule session Desktop/Gaming · Aucune application ne sera fermée automatiquement"
                color: window.themeColors.muted_text
                font.pixelSize: 12
                Layout.alignment: Qt.AlignHCenter
            }
            Label {
                text: modeSelectorController.gamepadStatus
                color: window.themeColors.muted_text
                font.pixelSize: 11
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
            opacity: 1
        }
        ParallelAnimation {
            id: introHandoffCrossfade
            NumberAnimation {
                target: introVideoOutput
                property: "opacity"
                from: 1
                to: 0
                duration: 260
                easing.type: Easing.InOutCubic
            }
            NumberAnimation {
                target: introHandoffScreen
                property: "opacity"
                from: 0
                to: 1
                duration: 260
                easing.type: Easing.InOutCubic
            }
            onFinished: introVideoOutput.visible = false
        }
        Rectangle {
            id: introHandoffScreen
            opacity: 0
            anchors.fill: parent
            visible: false
            color: "#080808"
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#1A1A1A" }
                GradientStop { position: 0.52; color: "#080808" }
                GradientStop { position: 1.0; color: "#202020" }
            }
            Rectangle {
                width: 620
                height: width
                radius: width / 2
                x: parent.width * 0.62
                y: -height * 0.48
                color: window.colorA
                opacity: 0.055
            }
            Rectangle {
                width: 520
                height: width
                radius: width / 2
                x: -width * 0.46
                y: parent.height * 0.55
                color: window.colorB
                opacity: 0.05
            }
            ColumnLayout {
                anchors.centerIn: parent
                spacing: 18
                Image {
                    source: leosTheme.gamingLogoUrl
                    asynchronous: false
                    smooth: true
                    fillMode: Image.PreserveAspectFit
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: 320
                    Layout.preferredHeight: 270
                    visible: status === Image.Ready
                }
                Label {
                    text: "LEOS GAMING"
                    color: window.themeColors.text
                    font.pixelSize: 30
                    font.weight: Font.Black
                    font.letterSpacing: 5
                    Layout.alignment: Qt.AlignHCenter
                }
                Label {
                    text: "PRÉPARATION DE VOTRE ESPACE DE JEU"
                    color: window.muted
                    font.pixelSize: 14
                    font.letterSpacing: 2
                    Layout.alignment: Qt.AlignHCenter
                }
                BusyIndicator {
                    running: modeSelectorController.animationsEnabled && introHandoffScreen.visible
                    visible: modeSelectorController.animationsEnabled
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
        }
    }

    Connections {
        target: modeManager
        function onModeLaunchFailed(message) {
            window.transitionInProgress = false
            window.gamingHandoffPending = false
            window.pendingMode = ""
            introTimeout.stop()
            introPlayer.stop()
            introHandoffCrossfade.stop()
            introHandoffScreen.visible = false
            introHandoffScreen.opacity = 0
            introVideoOutput.visible = true
            introVideoOutput.opacity = 1
            introOverlay.opacity = 1
            introOverlay.visible = false
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
                font.pixelSize: 12
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
                text: "Conseillé : active le profil LEOS pour retrouver dès cette session le fond graphite, le style et le dock de la distribution. Le choix alternatif conserve volontairement ton bureau KDE actuel."
                color: window.colorAText
                font.pixelSize: 13
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
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
                      : "ACTIVER L'APPARENCE LEOS · RECOMMANDÉ"
                Accessible.description: "Appliquer l'apparence graphite LEOS, le schéma A/B, le style Plasma, les icônes et le dock après sauvegarde du bureau actuel."
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
