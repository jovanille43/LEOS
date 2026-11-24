import QtQuick 2.15

Rectangle {
    id: root
    gradient: Gradient {
        GradientStop { position: 0.0; color: "#090909" }
        GradientStop { position: 0.52; color: "#131313" }
        GradientStop { position: 1.0; color: "#080808" }
    }
    property int stage: 0

    Rectangle {
        width: Math.max(root.width, root.height) * 0.9
        height: width
        radius: width / 2
        anchors.centerIn: parent
        color: "#00D9FF"
        opacity: 0.045
    }

    Rectangle {
        width: Math.max(root.width, root.height) * 0.56
        height: width
        radius: width / 2
        x: -width * 0.38
        y: root.height * 0.52
        color: "#E33BFF"
        opacity: 0.032
    }

    Column {
        anchors.centerIn: parent
        spacing: 22

        Image {
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.min(root.width * 0.22, 236)
            height: width
            source: "file:///usr/share/leos/branding/desktop-logo.jpeg"
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            smooth: true
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "LEOS"
            color: "#F0F2F5"
            font.family: "Noto Sans"
            font.pixelSize: 32
            font.weight: Font.Bold
            font.letterSpacing: 7
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "DESKTOP ENVIRONMENT"
            color: "#00D9FF"
            font.family: "Noto Sans"
            font.pixelSize: 10
            font.weight: Font.DemiBold
            font.letterSpacing: 2.4
        }

        Rectangle {
            width: 140
            height: 3
            radius: 2
            anchors.horizontalCenter: parent.horizontalCenter
            color: "#292929"
            border.color: "#414141"
            border.width: 1
            clip: true

            Rectangle {
                width: parent.width * 0.36
                height: parent.height
                radius: 2
                gradient: Gradient {
                    GradientStop { position: 0; color: "#00D9FF" }
                    GradientStop { position: 1; color: "#E33BFF" }
                }
                x: 0
                SequentialAnimation on x {
                    loops: Animation.Infinite
                    NumberAnimation { from: 0; to: 89.6; duration: 1050; easing.type: Easing.InOutSine }
                    NumberAnimation { from: 89.6; to: 0; duration: 1050; easing.type: Easing.InOutSine }
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.stage < 1 ? "Initialisation de votre environnement" : "Bienvenue dans LEOS"
            color: "#A0A0A0"
            font.family: "Noto Sans"
            font.pixelSize: 12
        }
    }
}
