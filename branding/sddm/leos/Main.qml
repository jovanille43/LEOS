import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

Rectangle {
    id: root
    width: Screen.width
    height: Screen.height
    property string statusMessage: ""
    property bool authenticating: false
    property var clockNow: new Date()

    gradient: Gradient {
        GradientStop { position: 0.0; color: "#090909" }
        GradientStop { position: 0.48; color: "#141414" }
        GradientStop { position: 1.0; color: "#080808" }
    }

    function attemptLogin() {
        if (authenticating)
            return
        if (userField.text.trim().length === 0) {
            statusMessage = "Saisis ton identifiant."
            userField.forceActiveFocus()
            return
        }
        if (passwordField.text.length === 0) {
            statusMessage = "Saisis ton mot de passe."
            passwordField.forceActiveFocus()
            return
        }
        statusMessage = "Connexion en cours…"
        authenticating = true
        var selectedSession = sessionSelector.currentIndex
        if (selectedSession < 0)
            selectedSession = sessionModel.lastIndex
        if (selectedSession < 0)
            selectedSession = 0
        sddm.login(userField.text.trim(), passwordField.text, selectedSession)
    }

    function requestPowerAction(action) {
        powerConfirmation.operation = action
        powerConfirmation.open()
    }

    Timer {
        interval: 1000
        repeat: true
        running: true
        onTriggered: root.clockNow = new Date()
    }

    Dialog {
        id: powerConfirmation
        property string operation: ""
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(390, root.width - 40)
        title: operation === "poweroff" ? "Éteindre LEOS ?"
             : operation === "reboot" ? "Redémarrer LEOS ?"
             : "Mettre LEOS en veille ?"
        standardButtons: Dialog.Yes | Dialog.No

        contentItem: Label {
            text: powerConfirmation.operation === "poweroff"
                ? "L’ordinateur va s’éteindre."
                : powerConfirmation.operation === "reboot"
                    ? "L’ordinateur va redémarrer."
                    : "La session sera suspendue en mémoire."
            color: "#D0D5DC"
            wrapMode: Text.WordWrap
            padding: 12
        }

        onAccepted: {
            if (operation === "poweroff")
                sddm.powerOff()
            else if (operation === "reboot")
                sddm.reboot()
            else if (operation === "suspend")
                sddm.suspend()
        }
    }

    Rectangle {
        width: Math.max(root.width, root.height) * 0.72
        height: width
        radius: width / 2
        x: root.width * 0.58
        y: -height * 0.56
        color: "#00D9FF"
        opacity: 0.045
    }

    Rectangle {
        width: Math.max(root.width, root.height) * 0.62
        height: width
        radius: width / 2
        x: -width * 0.42
        y: root.height * 0.55
        color: "#E33BFF"
        opacity: 0.035
    }

    Rectangle {
        id: utilityBar
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 24
        height: 62
        radius: 16
        clip: true
        color: "#141414"
        border.color: "#343434"
        border.width: 1
        opacity: 0.97

        Rectangle {
            anchors { left: parent.left; right: parent.right; top: parent.top }
            height: 2
            gradient: Gradient {
                GradientStop { position: 0; color: "#00D9FF" }
                GradientStop { position: 1; color: "#E33BFF" }
            }
            opacity: 0.62
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 18
            anchors.rightMargin: 14
            spacing: 10

            ColumnLayout {
                spacing: 1

                Label {
                    text: Qt.formatDateTime(root.clockNow, "HH:mm")
                    color: "#F1F3F6"
                    font.family: "Noto Sans"
                    font.pixelSize: 19
                    font.weight: Font.DemiBold
                }

                Label {
                    text: Qt.formatDateTime(root.clockNow, "dddd d MMMM")
                    color: "#A5AFBB"
                    font.family: "Noto Sans"
                    font.pixelSize: 10
                }
            }

            Item { Layout.fillWidth: true }

            Label {
                visible: keyboard.enabled && keyboard.layouts.length > 0
                text: "CLAVIER"
                color: "#909BA8"
                font.family: "Noto Sans"
                font.pixelSize: 10
                font.weight: Font.DemiBold
            }

            ComboBox {
                id: keyboardSelector
                visible: keyboard.enabled && keyboard.layouts.length > 0
                Layout.preferredWidth: 82
                Layout.preferredHeight: 38
                model: keyboard.layouts
                textRole: "shortName"
                currentIndex: keyboard.currentLayout
                font.family: "Noto Sans"
                font.pixelSize: 12
                onActivated: keyboard.currentLayout = currentIndex
            }

            Button {
                visible: sddm.canSuspend
                text: "Veille"
                onClicked: root.requestPowerAction("suspend")
                font.family: "Noto Sans"
                font.pixelSize: 11
                background: Rectangle {
                    radius: 9
                    color: parent.down ? "#303B49" : "#1A232E"
                    border.color: "#3A4654"
                }
                contentItem: Text {
                    text: parent.text
                    color: "#D8DDE3"
                    font: parent.font
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            Button {
                visible: sddm.canReboot
                text: "Redémarrer"
                onClicked: root.requestPowerAction("reboot")
                font.family: "Noto Sans"
                font.pixelSize: 11
                background: Rectangle {
                    radius: 9
                    color: parent.down ? "#303B49" : "#1A232E"
                    border.color: "#3A4654"
                }
                contentItem: Text {
                    text: parent.text
                    color: "#D8DDE3"
                    font: parent.font
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            Button {
                visible: sddm.canPowerOff
                text: "Éteindre"
                onClicked: root.requestPowerAction("poweroff")
                font.family: "Noto Sans"
                font.pixelSize: 11
                background: Rectangle {
                    radius: 9
                    color: parent.down ? "#46343A" : "#2B2026"
                    border.color: "#5A4149"
                }
                contentItem: Text {
                    text: parent.text
                    color: "#E4D9DC"
                    font: parent.font
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }

    Rectangle {
        id: loginCard
        width: Math.min(472, root.width - 32)
        height: loginContent.implicitHeight + 56
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 30
        radius: 22
        color: "#131313"
        border.color: "#343434"
        border.width: 1
        opacity: 0.985
        clip: true

        Rectangle {
            anchors { left: parent.left; right: parent.right; top: parent.top }
            height: 2
            gradient: Gradient {
                GradientStop { position: 0; color: "#00D9FF" }
                GradientStop { position: 1; color: "#E33BFF" }
            }
            opacity: 0.78
        }
        Rectangle {
            anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
            width: 3
            gradient: Gradient {
                GradientStop { position: 0; color: "#00D9FF" }
                GradientStop { position: 1; color: "#E33BFF" }
            }
            opacity: 0.28
        }
    }

    ColumnLayout {
        id: loginContent
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 30
        width: Math.min(420, loginCard.width - 56)
        spacing: 13

        Image {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: Math.min(178, root.height * 0.17)
            Layout.preferredHeight: Layout.preferredWidth
            source: "file:///usr/share/leos/branding/desktop-logo.jpeg"
            fillMode: Image.PreserveAspectFit
            smooth: true
            asynchronous: true
        }

        Label {
            Layout.alignment: Qt.AlignHCenter
            text: "LEOS"
            color: "#F1F3F6"
            font.family: "Noto Sans"
            font.pixelSize: 32
            font.weight: Font.Bold
            font.letterSpacing: 7
        }

        Label {
            Layout.alignment: Qt.AlignHCenter
            text: "Bienvenue"
            color: "#AEB6C1"
            font.family: "Noto Sans"
            font.pixelSize: 15
        }

        Label {
            Layout.alignment: Qt.AlignHCenter
            text: "ACCÈS À VOTRE ENVIRONNEMENT"
            color: "#00D9FF"
            font.family: "Noto Sans"
            font.pixelSize: 10
            font.weight: Font.DemiBold
            font.letterSpacing: 1.7
        }

        Label {
            Layout.fillWidth: true
            text: "IDENTIFIANT"
            color: "#929292"
            font.family: "Noto Sans"
            font.pixelSize: 10
            font.weight: Font.DemiBold
            font.letterSpacing: 1.1
        }

        TextField {
            id: userField
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            text: userModel.lastUser
            placeholderText: "Nom d’utilisateur"
            selectByMouse: true
            font.family: "Noto Sans"
            font.pixelSize: 15
            color: "#F4F6F8"
            leftPadding: 18
            rightPadding: 18
            background: Rectangle {
                radius: 12
                color: "#171D26"
                border.color: userField.activeFocus ? "#00D9FF" : "#373737"
                border.width: userField.activeFocus ? 2 : 1
            }
            onAccepted: passwordField.forceActiveFocus()
        }

        Label {
            Layout.fillWidth: true
            text: "MOT DE PASSE"
            color: "#929292"
            font.family: "Noto Sans"
            font.pixelSize: 10
            font.weight: Font.DemiBold
            font.letterSpacing: 1.1
        }

        TextField {
            id: passwordField
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            placeholderText: "Mot de passe"
            echoMode: TextInput.Password
            selectByMouse: true
            font.family: "Noto Sans"
            font.pixelSize: 15
            color: "#F4F6F8"
            leftPadding: 18
            rightPadding: 18
            background: Rectangle {
                radius: 12
                color: "#171D26"
                border.color: passwordField.activeFocus ? "#E33BFF" : "#373737"
                border.width: passwordField.activeFocus ? 2 : 1
            }
            onAccepted: root.attemptLogin()
        }

        ComboBox {
            id: sessionSelector
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            model: sessionModel
            textRole: "name"
            currentIndex: sessionModel.lastIndex
            font.family: "Noto Sans"
            font.pixelSize: 14
            contentItem: Text {
                leftPadding: 16
                rightPadding: 30
                text: sessionSelector.displayText
                color: "#E4E7EB"
                font: sessionSelector.font
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }
            background: Rectangle {
                radius: 11
                color: "#171717"
                border.width: sessionSelector.activeFocus ? 2 : 1
                border.color: sessionSelector.activeFocus ? "#00D9FF" : "#373737"
            }
        }

        Button {
            id: loginButton
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            text: root.authenticating ? "Connexion…" : "Se connecter"
            enabled: !root.authenticating
            font.family: "Noto Sans"
            font.pixelSize: 15
            font.weight: Font.DemiBold
            onClicked: root.attemptLogin()
            background: Rectangle {
                radius: 12
                gradient: Gradient {
                    GradientStop { position: 0; color: loginButton.down ? "#00B7D8" : "#00D9FF" }
                    GradientStop { position: 1; color: loginButton.down ? "#C62DDC" : "#E33BFF" }
                }
                border.color: "#F1F1F1"
                border.width: 1
                opacity: loginButton.enabled ? 1 : 0.42
            }
            contentItem: Text {
                text: loginButton.text
                color: "#101010"
                font: loginButton.font
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        Label {
            Layout.fillWidth: true
            Layout.minimumHeight: 24
            text: root.statusMessage
            color: root.authenticating ? "#00D9FF" : "#E33BFF"
            font.family: "Noto Sans"
            font.pixelSize: 12
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            root.authenticating = false
            root.statusMessage = "Identifiant ou mot de passe incorrect."
            passwordField.clear()
            passwordField.forceActiveFocus()
        }
    }

    Component.onCompleted: {
        if (userField.text.length > 0)
            passwordField.forceActiveFocus()
        else
            userField.forceActiveFocus()
    }
}
