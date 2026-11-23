import QtQuick

// Lightweight, GPU-composited LEOS particle field for the fullscreen Gaming shell.
// Each point drifts slowly and pulses between the user's live A/B accent colours.
Item {
    id: root

    property color colorA: "#A0A0A0"
    property color colorB: "#D0D0D0"
    property bool active: true
    property int particleCount: 44

    clip: true

    Repeater {
        model: root.particleCount

        delegate: Item {
            id: particle

            required property int index

            readonly property real particleRadius: 1.2 + (index % 4) * 0.48
            readonly property real blend: ((index * 29) % 101) / 100.0
            readonly property color tint: Qt.rgba(
                root.colorA.r * (1.0 - blend) + root.colorB.r * blend,
                root.colorA.g * (1.0 - blend) + root.colorB.g * blend,
                root.colorA.b * (1.0 - blend) + root.colorB.b * blend,
                1.0
            )
            readonly property real startX: root.width * (((index * 71) % 101) / 100.0)
            readonly property real startY: root.height * (0.08 + (((index * 37) % 83) / 100.0))
            readonly property real driftX: (index % 2 === 0 ? 1 : -1)
                                         * root.width * (0.012 + (index % 5) * 0.004)
            readonly property real driftY: -root.height * (0.035 + (index % 6) * 0.009)
            readonly property int travelDuration: 23000 + (index % 9) * 2100
            readonly property real haloLow: index % 3 === 0 ? 0.065 : 0.025
            readonly property real haloHigh: index % 3 === 0 ? 0.17 : 0.105

            x: startX
            y: startY
            width: particleRadius * 8
            height: width

            Rectangle {
                id: halo
                anchors.centerIn: parent
                width: particle.particleRadius * (5.5 + particle.index % 5)
                height: width
                radius: width / 2
                color: particle.tint
                opacity: particle.haloLow
            }

            Rectangle {
                anchors.centerIn: parent
                width: particle.particleRadius
                height: width
                radius: width / 2
                color: particle.tint
                opacity: 0.52
            }

            SequentialAnimation {
                running: root.active
                loops: Animation.Infinite

                ParallelAnimation {
                    NumberAnimation {
                        target: particle
                        property: "x"
                        from: particle.startX
                        to: particle.startX + particle.driftX
                        duration: particle.travelDuration
                        easing.type: Easing.InOutSine
                    }
                    NumberAnimation {
                        target: particle
                        property: "y"
                        from: particle.startY
                        to: particle.startY + particle.driftY
                        duration: particle.travelDuration
                        easing.type: Easing.InOutSine
                    }
                }
            }

            SequentialAnimation {
                running: root.active
                loops: Animation.Infinite

                NumberAnimation {
                    target: halo
                    property: "opacity"
                    from: particle.haloLow
                    to: particle.haloHigh
                    duration: 2500 + (particle.index % 6) * 650
                    easing.type: Easing.InOutSine
                }
                NumberAnimation {
                    target: halo
                    property: "opacity"
                    from: particle.haloHigh
                    to: particle.haloLow
                    duration: 2900 + (particle.index % 5) * 700
                    easing.type: Easing.InOutSine
                }
            }
        }
    }
}
