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
    property date currentDate: new Date()
    property string pendingMode: ""
    property string themeColorNotice: ""
    property bool transitionInProgress: false

    function accentSurface(accentColor, strength) {
        const base = Qt.color(themeColors.surface)
        const tint = accentColor
        const amount = Math.max(0.0, Math.min(1.0, strength))
        return Qt.rgba(
            base.r * (1.0 - amount) + tint.r * amount,
            base.g * (1.0 - amount) + tint.g * amount,
            base.b * (1.0 - amount) + tint.b * amount,
            1.0
        )
    }

    function colorToHex(color) {
        function byteHex(value) {
            const valueHex = Math.max(0, Math.min(255, Math.round(value * 255))).toString(16).toUpperCase()
            return valueHex.length === 1 ? "0" + valueHex : valueHex
        }
        return "#" + byteHex(color.r) + byteHex(color.g) + byteHex(color.b)
    }

    function commitThemeColors(colorA, colorB) {
        themeColorNotice = leosTheme.setThemeColors(colorA, colorB)
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
        if (transitionInProgress) {
            if (action === "back")
                finishModeTransition()
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
                window.requestModeWithIntro("desktop")
        }
    }

    ColorDialog {
        id: initialColorADialog
        title: "Choisir la couleur A"
        selectedColor: Qt.color(leosTheme.themeColorA)
        onAccepted: window.commitThemeColors(
            window.colorToHex(selectedColor),
            leosTheme.themeColorB
        )
    }

    ColorDialog {
        id: initialColorBDialog
        title: "Choisir la couleur B"
        selectedColor: Qt.color(leosTheme.themeColorB)
        onAccepted: window.commitThemeColors(
            leosTheme.themeColorA,
            window.colorToHex(selectedColor)
        )
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
            color: window.colorA; opacity: 0.12
        }
        Rectangle {
            width: 560; height: 560; radius: 280
            x: -width * 0.4; y: parent.height * 0.55
            color: window.colorB; opacity: 0.10
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
                    color: window.colorAText
                    font.pixelSize: 10
                    font.letterSpacing: 1.5
                    Layout.alignment: Qt.AlignHCenter
                    topPadding: 4
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 190
                visible: !modeSelectorController.onboardingComplete
                radius: 15
                color: window.themeColors.surface_elevated
                border.color: window.accentSurface(window.colorA, 0.30)

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 16

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: 390
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
                            text: "Personnalise ton dégradé maintenant ou plus tard dans le Centre de contrôle, et choisis aussi ton apparence."
                            color: window.muted
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 250
                        spacing: 7

                        Label {
                            text: "TES COULEURS LEOS"
                            color: window.themeColors.text
                            font.pixelSize: 9
                            font.letterSpacing: 1.3
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Button {
                                text: "A · " + leosTheme.themeColorA
                                Layout.fillWidth: true
                                onClicked: initialColorADialog.open()
                                background: Rectangle {
                                    radius: 8
                                    color: window.themeColors.surface
                                    border.color: leosTheme.themeColorA
                                }
                                contentItem: Label {
                                    text: parent.text
                                    color: window.themeColors.text
                                    font.pixelSize: 10
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                            Button {
                                text: "B · " + leosTheme.themeColorB
                                Layout.fillWidth: true
                                onClicked: initialColorBDialog.open()
                                background: Rectangle {
                                    radius: 8
                                    color: window.themeColors.surface
                                    border.color: leosTheme.themeColorB
                                }
                                contentItem: Label {
                                    text: parent.text
                                    color: window.themeColors.text
                                    font.pixelSize: 10
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 9
                            radius: 5
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0.0; color: Qt.color(leosTheme.themeColorA) }
                                GradientStop { position: 1.0; color: Qt.color(leosTheme.themeColorB) }
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Label {
                                text: "APPARENCE"
                                color: window.themeColors.text
                                font.pixelSize: 9
                                font.letterSpacing: 1
                            }
                            Item { Layout.fillWidth: true }
                            ComboBox {
                                id: initialAppearanceBox
                                Layout.preferredWidth: 170
                                model: ["Sombre", "Clair", "Automatique"]
                                currentIndex: Math.max(0, ["dark", "light", "auto"].indexOf(leosTheme.appearanceMode))
                                onActivated: function(index) {
                                    leosTheme.setAppearanceMode(["dark", "light", "auto"][index])
                                }
                            }
                        }
                        Label {
                            text: window.themeColorNotice
                            visible: text.length > 0
                            color: window.muted
                            font.pixelSize: 9
                        }
                    }

                    Button {
                        text: "COMPRIS"
                        Layout.minimumWidth: 112
                        onClicked: modeSelectorController.completeOnboarding()
                        background: Rectangle {
                            radius: 8
                            color: window.accentSurface(window.colorA, 0.24)
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
                    onClicked: window.requestModeWithIntro("desktop")
                    background: Rectangle {
                        radius: 22
                        color: desktopCard.down ? window.accentSurface(window.colorA, 0.24) : window.themeColors.surface
                        border.width: desktopCard.activeFocus ? 2 : 1
                        border.color: desktopCard.activeFocus ? window.colorA : window.accentSurface(window.colorA, 0.24)
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
                        color: gamingCard.down ? window.accentSurface(window.colorB, 0.24) : window.themeColors.surface
                        border.width: gamingCard.activeFocus ? 2 : 1
                        border.color: gamingCard.activeFocus ? window.colorB : window.accentSurface(window.colorB, 0.24)
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
                            text: "Vos jeux et lanceurs réunis au même endroit"
                            color: window.themeColors.muted_text
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
            if (event.key === Qt.Key_G) {
                transitionDialog.open()
                event.accepted = true
            } else if (event.key === Qt.Key_D) {
                window.requestModeWithIntro("desktop")
                event.accepted = true
            } else if (event.key === Qt.Key_Left || event.key === Qt.Key_Right) {
                if (desktopCard.activeFocus)
                    gamingCard.forceActiveFocus()
                else
                    desktopCard.forceActiveFocus()
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

    // Escape only skips a mode intro while the transition is active.
    Shortcut {
        sequence: "Esc"
        context: Qt.ApplicationShortcut
        enabled: window.transitionInProgress
        onActivated: window.finishModeTransition()
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
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 42
            radius: 18
            color: "#B8000000"
            border.color: "#55FFFFFF"
            width: skipModeIntroLabel.implicitWidth + 34
            height: skipModeIntroLabel.implicitHeight + 22
            Label {
                id: skipModeIntroLabel
                anchors.centerIn: parent
                text: "ÉCHAP, RETOUR MANETTE OU CLIC POUR PASSER"
                color: window.themeColors.text
                font.pixelSize: 13
                font.weight: Font.DemiBold
            }
        }
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
            onClicked: window.finishModeTransition()
        }
    }

    Connections {
        target: modeSelectorController
        function onGamepadAction(action) {
            window.handleGamepadAction(action)
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
                background: Rectangle { radius: 9; color: window.accentSurface(window.colorA, 0.24); border.color: window.colorA }
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
