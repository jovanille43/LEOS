import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Shared brand signature for the two LEOS experiences.
// Host screens provide the official emblem and the user's selected A/B pair.
RowLayout {
    id: root
    property url logoSource: ""
    property string modeLabel: "DESKTOP MODE"
    property color titleColor: "#F1F1F1"
    property color labelColor: "#A0A0A0"
    property color accentA: "#A0A0A0"
    property color accentB: "#D0D0D0"
    property int logoWidth: 96
    property int logoHeight: 52
    property int titlePixelSize: 26
    property int labelPixelSize: 11
    property real titleLetterSpacing: 4
    property real labelLetterSpacing: 2.4
    spacing: 10

    Image {
        id: emblem
        source: root.logoSource
        asynchronous: true
        smooth: true
        fillMode: Image.PreserveAspectFit
        Layout.preferredWidth: root.logoWidth
        Layout.preferredHeight: root.logoHeight
        visible: status === Image.Ready
        Accessible.ignored: true
    }
    ColumnLayout {
        spacing: 3
        Label {
            text: "LEOS"
            color: root.titleColor
            font.pixelSize: root.titlePixelSize
            font.weight: Font.Black
            font.letterSpacing: root.titleLetterSpacing
            visible: emblem.status !== Image.Ready
        }
        Label {
            text: root.modeLabel
            color: root.labelColor
            font.pixelSize: root.labelPixelSize
            font.weight: Font.DemiBold
            font.letterSpacing: root.labelLetterSpacing
        }
        Rectangle {
            Layout.preferredWidth: 46
            Layout.preferredHeight: 2
            radius: 1
            opacity: 0.82
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: root.accentA }
                GradientStop { position: 1.0; color: root.accentB }
            }
        }
    }
    Accessible.role: Accessible.Grouping
    Accessible.name: "LEOS " + modeLabel
}
