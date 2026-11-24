import QtQuick 2.15

Rectangle {
    id: root
    gradient: Gradient {
        GradientStop { position: 0.0; color: "#090B10" }
        GradientStop { position: 0.52; color: "#10151D" }
        GradientStop { position: 1.0; color: "#080A0E" }
    }
    property int stage: 0

    Rectangle {
        width: Math.max(root.width, root.height) * 0.9
        height: width
        radius: width / 2
        anchors.centerIn: parent
        color: "#252D38"
        opacity: 0.14
    }

    Rectangle {
        width: Math.max(root.width, root.height) * 0.56
        height: width
        radius: width / 2
        x: -width * 0.38
        y: root.height * 0.52
        color: "#424A55"
        opacity: 0.065
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
            color: "#B9C2CE"
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
            color: "#343D49"
            border.color: "#4B5664"
            border.width: 1
            clip: true

            Rectangle {
                width: parent.width * 0.36
                height: parent.height
                radius: 2
                color: "#C9CFD7"
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
            color: "#9CA6B3"
            font.family: "Noto Sans"
            font.pixelSize: 12
        }
    }
}
