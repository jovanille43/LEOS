import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    width: 1920
    height: 1080
    property string statusMessage: ""
    property bool authenticating: false

    gradient: Gradient {
        GradientStop { position: 0.0; color: "#090B10" }
        GradientStop { position: 0.52; color: "#10151D" }
        GradientStop { position: 1.0; color: "#080A0E" }
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

    Rectangle {
        width: Math.max(root.width, root.height) * 0.72
        height: width
        radius: width / 2
        x: root.width * 0.58
        y: -height * 0.56
        color: "#222A34"
        opacity: 0.18
    }

    Rectangle {
        width: Math.max(root.width, root.height) * 0.62
        height: width
        radius: width / 2
        x: -width * 0.42
        y: root.height * 0.55
        color: "#424A55"
        opacity: 0.12
    }

    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(420, root.width - 48)
        spacing: 16

        Image {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 206
            Layout.preferredHeight: 206
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
            font.pixelSize: 34
            font.weight: Font.DemiBold
            font.letterSpacing: 7
        }

        Label {
            Layout.alignment: Qt.AlignHCenter
            text: "Bienvenue"
            color: "#AEB6C1"
            font.family: "Noto Sans"
            font.pixelSize: 15
        }

        TextField {
            id: userField
            Layout.fillWidth: true
            Layout.preferredHeight: 52
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
                border.color: userField.activeFocus ? "#C6CDD6" : "#343D49"
                border.width: userField.activeFocus ? 2 : 1
            }
            onAccepted: passwordField.forceActiveFocus()
        }

        TextField {
            id: passwordField
            Layout.fillWidth: true
            Layout.preferredHeight: 52
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
                border.color: passwordField.activeFocus ? "#C6CDD6" : "#343D49"
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
        }

        Button {
            id: loginButton
            Layout.fillWidth: true
            Layout.preferredHeight: 52
            text: root.authenticating ? "Connexion…" : "Se connecter"
            enabled: !root.authenticating
            font.family: "Noto Sans"
            font.pixelSize: 15
            font.weight: Font.DemiBold
            onClicked: root.attemptLogin()
            background: Rectangle {
                radius: 12
                color: loginButton.enabled
                    ? (loginButton.down ? "#B8C0CA" : "#D8DDE3")
                    : "#777F89"
                border.color: "#F3F5F7"
                border.width: 1
            }
            contentItem: Text {
                text: loginButton.text
                color: "#11161D"
                font: loginButton.font
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        Label {
            Layout.fillWidth: true
            Layout.minimumHeight: 24
            text: root.statusMessage
            color: "#D0D5DC"
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
