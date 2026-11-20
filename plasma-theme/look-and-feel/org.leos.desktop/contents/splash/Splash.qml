import QtQuick 2.15

Rectangle {
    id: root
    color: "#090B10"
    property int stage: 0

    Rectangle {
        width: Math.max(root.width, root.height) * 0.9
        height: width
        radius: width / 2
        anchors.centerIn: parent
        color: "#252D38"
        opacity: 0.16
    }

    Column {
        anchors.centerIn: parent
        spacing: 22

        Image {
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.min(root.width * 0.26, 280)
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
            font.pixelSize: 30
            font.weight: Font.DemiBold
            font.letterSpacing: 6
        }

        Rectangle {
            width: 140
            height: 3
            radius: 2
            anchors.horizontalCenter: parent.horizontalCenter
            color: "#343D49"
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
            text: root.stage < 1 ? "Préparation de votre espace" : "Bienvenue dans LEOS"
            color: "#9CA6B3"
            font.family: "Noto Sans"
            font.pixelSize: 12
        }
    }
}
