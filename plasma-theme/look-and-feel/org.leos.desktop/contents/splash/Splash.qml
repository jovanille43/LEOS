import QtQuick 2.15

Rectangle {
    id: root
    color: "#090909"
    property int stage: 0

    Rectangle {
        width: Math.max(root.width, root.height) * 0.86
        height: width
        radius: width / 2
        anchors.centerIn: parent
        color: "#171717"
        opacity: 0.34
    }

    Rectangle {
        width: Math.min(root.width * 0.48, 520)
        height: width
        radius: width / 2
        anchors.centerIn: parent
        color: "transparent"
        border.color: "#383838"
        border.width: 1
        opacity: 0.34
    }

    Column {
        anchors.centerIn: parent
        spacing: 18

        Image {
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.min(root.width * 0.25, 270)
            height: width
            source: "file:///usr/share/leos/branding/desktop-logo.jpeg"
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            smooth: true
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "LEOS"
            color: "#F3F3F3"
            font.family: "Noto Sans"
            font.pixelSize: 30
            font.weight: Font.DemiBold
            font.letterSpacing: 7
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "DESKTOP  /  GAMING"
            color: "#B0B0B0"
            font.family: "Noto Sans"
            font.pixelSize: 9
            font.weight: Font.DemiBold
            font.letterSpacing: 3
        }

        Rectangle {
            width: 196
            height: 3
            radius: 2
            anchors.horizontalCenter: parent.horizontalCenter
            color: "#333333"
            clip: true

            Rectangle {
                width: parent.width * 0.34
                height: parent.height
                radius: 2
                color: "#D5D5D5"
                x: 0
                SequentialAnimation on x {
                    loops: Animation.Infinite
                    NumberAnimation { from: 0; to: 129.36; duration: 1250; easing.type: Easing.InOutSine }
                    NumberAnimation { from: 129.36; to: 0; duration: 1250; easing.type: Easing.InOutSine }
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.stage < 1 ? "Préparation de votre espace" : "Bienvenue dans LEOS"
            color: "#A6A6A6"
            font.family: "Noto Sans"
            font.pixelSize: 11
        }
    }
}
