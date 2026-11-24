import QtQuick

Item {
    id: root

    property color colorA: "#6FB6E8"
    property color colorB: "#A58AD8"
    property real particleOpacity: 0.78
    property bool motionEnabled: true
    property int particleCount: 54
    property var particles: []
    property real phase: 0

    function seedParticles() {
        var seeded = []
        for (var i = 0; i < particleCount; ++i) {
            seeded.push({
                x: Math.random(),
                y: Math.random(),
                vx: (Math.random() - 0.5) * 0.00032,
                vy: -0.00008 - Math.random() * 0.00018,
                radius: 0.75 + Math.random() * 1.8,
                alpha: 0.10 + Math.random() * 0.25,
                phase: Math.random() * Math.PI * 2,
                secondary: Math.random() > 0.52
            })
        }
        particles = seeded
        canvas.requestPaint()
    }

    Component.onCompleted: seedParticles()
    onWidthChanged: canvas.requestPaint()
    onHeightChanged: canvas.requestPaint()

    Timer {
        interval: 40
        repeat: true
        running: root.visible && root.motionEnabled
        onTriggered: {
            var next = []
            for (var i = 0; i < root.particles.length; ++i) {
                var p = root.particles[i]
                var x = p.x + p.vx
                var y = p.y + p.vy
                if (y < -0.025) {
                    y = 1.025
                    x = Math.random()
                }
                if (x < -0.025) x = 1.025
                if (x > 1.025) x = -0.025
                next.push({
                    x: x, y: y, vx: p.vx, vy: p.vy,
                    radius: p.radius, alpha: p.alpha,
                    phase: p.phase, secondary: p.secondary
                })
            }
            root.particles = next
            root.phase += 0.045
            canvas.requestPaint()
        }
    }

    Canvas {
        id: canvas
        anchors.fill: parent
        antialiasing: true

        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)

            // Sparse connective filaments recall the PlayStation 5 ambient
            // particle field without competing with text or game artwork.
            for (var i = 0; i < root.particles.length; ++i) {
                var a = root.particles[i]
                for (var j = i + 1; j < root.particles.length; ++j) {
                    var b = root.particles[j]
                    var dx = (a.x - b.x) * width
                    var dy = (a.y - b.y) * height
                    var distance = Math.sqrt(dx * dx + dy * dy)
                    if (distance < 118 && ((i + j) % 4 === 0)) {
                        ctx.beginPath()
                        ctx.moveTo(a.x * width, a.y * height)
                        ctx.lineTo(b.x * width, b.y * height)
                        ctx.strokeStyle = a.secondary ? root.colorB : root.colorA
                        ctx.globalAlpha = (1 - distance / 118) * 0.075 * root.particleOpacity
                        ctx.lineWidth = 1
                        ctx.stroke()
                    }
                }
            }

            for (var k = 0; k < root.particles.length; ++k) {
                var p = root.particles[k]
                var pulse = 0.62 + 0.38 * Math.sin(root.phase + p.phase)
                var x = p.x * width
                var y = p.y * height
                var color = p.secondary ? root.colorB : root.colorA
                var radius = p.radius * (0.82 + pulse * 0.28)

                ctx.beginPath()
                ctx.arc(x, y, radius * 2.2, 0, Math.PI * 2)
                ctx.fillStyle = color
                ctx.globalAlpha = p.alpha * pulse * 0.10 * root.particleOpacity
                ctx.fill()

                ctx.beginPath()
                ctx.arc(x, y, radius, 0, Math.PI * 2)
                ctx.fillStyle = color
                ctx.globalAlpha = p.alpha * pulse * root.particleOpacity
                ctx.fill()
            }
            ctx.globalAlpha = 1
        }
    }
}
