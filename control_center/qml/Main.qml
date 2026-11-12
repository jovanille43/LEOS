import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1120
    height: 780
    minimumWidth: 820
    minimumHeight: 620
    visible: true
    title: "LEOS — Centre de contrôle"
    property var themeColors: controlCenter.themePalette
    color: themeColors.background

    property color cyan: themeColors.accent_primary
    property color magenta: themeColors.accent_secondary
    property color muted: themeColors.muted_text
    property int selectedPage: 0
    property string launchNotice: ""
    property string kdeThemeNotice: ""
    property string plasmaStyleNotice: ""
    property string wallpaperNotice: ""

    function formatRate(bytesPerSecond) {
        if (bytesPerSecond < 0)
            return "—"
        if (bytesPerSecond >= 1048576)
            return (bytesPerSecond / 1048576).toFixed(1) + " Mo/s"
        return (bytesPerSecond / 1024).toFixed(0) + " Ko/s"
    }

    Connections {
        target: controlCenter
        function onSettingsChanged() {
            const themes = ["leos-original", "light", "cyan", "magenta", "gaming"]
            themeBox.currentIndex = Math.max(0, themes.indexOf(controlCenter.theme))
            const layouts = ["leos-default", "minimal", "workspace", "custom"]
            desktopLayoutBox.currentIndex = Math.max(0, layouts.indexOf(controlCenter.desktopLayoutProfile))
            const positions = ["bottom", "top", "left", "right"]
            dockPositionBox.currentIndex = Math.max(0, positions.indexOf(controlCenter.dockPosition))
            const alignments = ["left", "center", "right"]
            dockAlignmentBox.currentIndex = Math.max(0, alignments.indexOf(controlCenter.dockAlignment))
            const profiles = ["performance", "balanced", "quiet", "battery-saver"]
            profileBox.currentIndex = Math.max(0, profiles.indexOf(controlCenter.performanceProfile))
            const durations = [3, 5, 8]
            notificationDurationBox.currentIndex = Math.max(0, durations.indexOf(controlCenter.notificationDuration))
            const priorities = ["all", "important", "critical"]
            notificationPriorityBox.currentIndex = Math.max(0, priorities.indexOf(controlCenter.notificationMinimumPriority))
        }
    }

    Dialog {
        id: kdeThemeConfirmation
        property string action: "apply"
        modal: true
        title: action === "apply" ? "Appliquer le thème LEOS à KDE ?" : "Restaurer le thème KDE précédent"
        standardButtons: Dialog.Yes | Dialog.No
        contentItem: Label {
            text: kdeThemeConfirmation.action === "apply"
                ? "LEOS va installer son schéma de couleurs dans ton espace utilisateur puis demander à KDE de l'appliquer. Tes panneaux, icônes, disposition et fichiers système ne seront pas modifiés."
                : "LEOS va réappliquer le schéma de couleurs KDE enregistré avant le premier changement LEOS."
            color: window.themeColors.text
            wrapMode: Text.WordWrap
            width: 420
            padding: 12
        }
        onAccepted: {
            if (action === "apply")
                window.kdeThemeNotice = controlCenter.applyKdeTheme()
            else
                window.kdeThemeNotice = controlCenter.restorePreviousKdeTheme()
        }
    }

    Dialog {
        id: plasmaStyleConfirmation
        property string action: "apply"
        modal: true
        title: action === "apply" ? "Appliquer le Plasma Style LEOS ?" : "Restaurer le style Plasma précédent"
        standardButtons: Dialog.Yes | Dialog.No
        contentItem: Label {
            text: plasmaStyleConfirmation.action === "apply"
                ? "LEOS va demander à Plasma d'utiliser son style de bureau. Cela modifie l'apparence des panneaux, widgets et fenêtres contextuelles Plasma, sans remplacer les icônes ni les réglages de disposition."
                : "LEOS va réappliquer le style Plasma enregistré avant le premier changement LEOS."
            color: window.themeColors.text
            wrapMode: Text.WordWrap
            width: 420
            padding: 12
        }
        onAccepted: {
            if (action === "apply")
                window.plasmaStyleNotice = controlCenter.applyPlasmaStyle()
            else
                window.plasmaStyleNotice = controlCenter.restorePreviousPlasmaStyle()
        }
    }

    Rectangle {
        anchors.fill: parent
        color: window.color

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 30
            spacing: 20

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    spacing: 2
                    Label {
                        text: "LEOS"
                        color: window.themeColors.text
                        font.pixelSize: 28
                        font.weight: Font.Black
                        font.letterSpacing: 5
                    }
                    Label {
                        text: "CENTRE DE CONTRÔLE"
                        color: window.cyan
                        font.pixelSize: 10
                        font.letterSpacing: 3
                    }
                }
                Item { Layout.fillWidth: true }
                Label {
                    text: "PRÉFÉRENCES UTILISATEUR"
                    color: window.muted
                    font.pixelSize: 10
                    font.letterSpacing: 2
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 18

                ColumnLayout {
                    Layout.preferredWidth: 220
                    Layout.minimumWidth: 185
                    Layout.fillHeight: true
                    spacing: 9

                    Repeater {
                        model: [
                            { label: "Vue d'ensemble", page: 0 },
                            { label: "Apparence", page: 1 },
                            { label: "Matériel & connexions", page: 2 },
                            { label: "Performances", page: 3 },
                            { label: "Paramètres KDE", page: 4 },
                            { label: "Mises à jour", page: 5 },
                            { label: "Notifications", page: 6 },
                            { label: "Diagnostic système", page: 7 },
                            { label: "Nettoyage", page: 8 },
                            { label: "Réseau", page: 9 }
                        ]
                        delegate: Button {
                            id: settingsNavigationButton
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 48
                            text: modelData.label
                            onClicked: {
                                window.selectedPage = modelData.page
                                window.launchNotice = ""
                            }
                            background: Rectangle {
                                radius: 10
                                color: window.selectedPage === modelData.page ? window.themeColors.surface_elevated : window.themeColors.surface
                                border.color: window.selectedPage === modelData.page ? window.cyan : window.themeColors.border
                            }
                            contentItem: Label {
                                text: settingsNavigationButton.text
                                color: window.themeColors.text
                                font.pixelSize: 12
                                verticalAlignment: Text.AlignVCenter
                                leftPadding: 8
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                    Label {
                        text: "LEOS • BUILD EN DÉVELOPPEMENT"
                        color: window.themeColors.muted_text
                        font.pixelSize: 9
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }

                StackLayout {
                    id: pages
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: window.selectedPage

                    ScrollView {
                        clip: true
                        ColumnLayout {
                            width: pages.width - 12
                            spacing: 14

                            Label {
                                text: "VUE D'ENSEMBLE"
                                color: window.themeColors.text
                                font.pixelSize: 20
                                font.weight: Font.Bold
                            }
                            Label {
                                text: "État en direct des ressources détectées sur cet appareil."
                                color: window.muted
                                font.pixelSize: 12
                                Layout.fillWidth: true
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 3
                                columnSpacing: 10
                                rowSpacing: 10

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 132
                                    radius: 13
                                    color: window.themeColors.surface
                                    border.color: window.themeColors.border
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 14
                                        spacing: 10
                                        Label {
                                            text: "UTILISATION CPU"
                                            color: window.cyan
                                            font.pixelSize: 10
                                            font.letterSpacing: 1
                                        }
                                        Label {
                                            text: systemMonitor.cpuUsage >= 0
                                                ? Math.round(systemMonitor.cpuUsage) + "%"
                                                : "—"
                                            color: window.themeColors.text
                                            font.pixelSize: 26
                                            font.weight: Font.Bold
                                        }
                                        Label {
                                            text: "Processeur"
                                            color: window.muted
                                            font.pixelSize: 10
                                        }
                                    }
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 132
                                    radius: 13
                                    color: window.themeColors.surface
                                    border.color: window.themeColors.border
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 14
                                        spacing: 10
                                        Label {
                                            text: "MÉMOIRE"
                                            color: window.cyan
                                            font.pixelSize: 10
                                            font.letterSpacing: 1
                                        }
                                        Label {
                                            text: systemMonitor.memoryUsage >= 0
                                                ? Math.round(systemMonitor.memoryUsage) + "%"
                                                : "—"
                                            color: window.themeColors.text
                                            font.pixelSize: 26
                                            font.weight: Font.Bold
                                        }
                                        Label {
                                            text: "RAM utilisée"
                                            color: window.muted
                                            font.pixelSize: 10
                                        }
                                    }
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 132
                                    radius: 13
                                    color: window.themeColors.surface
                                    border.color: window.themeColors.border
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 14
                                        spacing: 10
                                        Label {
                                            text: "TEMPÉRATURE CPU"
                                            color: window.cyan
                                            font.pixelSize: 10
                                            font.letterSpacing: 1
                                        }
                                        Label {
                                            text: systemMonitor.cpuTemperature >= 0
                                                ? Math.round(systemMonitor.cpuTemperature) + " °C"
                                                : "Indisponible"
                                            color: window.themeColors.text
                                            font.pixelSize: systemMonitor.cpuTemperature >= 0 ? 26 : 16
                                            font.weight: Font.Bold
                                        }
                                        Label {
                                            text: "Selon les capteurs Linux"
                                            color: window.muted
                                            font.pixelSize: 10
                                            wrapMode: Text.WordWrap
                                            Layout.fillWidth: true
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 132
                                radius: 13
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 14
                                    spacing: 10
                                    Label {
                                        text: "STOCKAGE SYSTÈME"
                                        color: window.cyan
                                        font.pixelSize: 10
                                        font.letterSpacing: 1
                                    }
                                    Label {
                                        text: systemMonitor.diskUsage >= 0
                                            ? Math.round(systemMonitor.diskUsage) + "%"
                                            : "Indisponible"
                                        color: window.themeColors.text
                                        font.pixelSize: systemMonitor.diskUsage >= 0 ? 26 : 16
                                        font.weight: Font.Bold
                                    }
                                    Label {
                                        text: "Occupation de la racine /"
                                        color: window.muted
                                        font.pixelSize: 10
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 132
                                radius: 13
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 14
                                    spacing: 8
                                    Label {
                                        text: "RÉSEAU"
                                        color: window.cyan
                                        font.pixelSize: 10
                                        font.letterSpacing: 1
                                    }
                                    Label {
                                        text: "↓  " + window.formatRate(systemMonitor.networkReceiveRate)
                                            + "    ↑  " + window.formatRate(systemMonitor.networkSendRate)
                                        color: window.themeColors.text
                                        font.pixelSize: 16
                                        font.weight: Font.Bold
                                        Layout.fillWidth: true
                                        wrapMode: Text.WordWrap
                                    }
                                    Label {
                                        text: "Débits agrégés des interfaces"
                                        color: window.muted
                                        font.pixelSize: 10
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 108
                                radius: 13
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 18
                                    spacing: 7
                                    Label {
                                        text: "SURVEILLANCE LEOS"
                                        color: window.cyan
                                        font.pixelSize: 10
                                        font.letterSpacing: 1
                                    }
                                    Label {
                                        text: systemMonitor.available
                                            ? "Actualisation automatique toutes les deux secondes. Les valeurs non exposées par le matériel restent indisponibles."
                                            : "Le module de mesure système n'est pas disponible sur cette installation."
                                        color: window.muted
                                        font.pixelSize: 11
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }

                    ScrollView {
                        clip: true
                        ColumnLayout {
                            width: pages.width - 12
                            spacing: 14

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 184
                                radius: 15
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    spacing: 12
                                    Label {
                                        text: "THÈME LEOS"
                                        color: window.cyan
                                        font.pixelSize: 11
                                        font.letterSpacing: 2
                                    }
                                    Label {
                                        text: "Choisis l'apparence générale de ton interface."
                                        color: window.muted
                                        font.pixelSize: 12
                                    }
                                    ComboBox {
                                        id: themeBox
                                        Layout.fillWidth: true
                                        model: ["LEOS Original", "Light", "Cyan", "Magenta", "Gaming"]
                                        Component.onCompleted: {
                                            const values = ["leos-original", "light", "cyan", "magenta", "gaming"]
                                            currentIndex = Math.max(0, values.indexOf(controlCenter.theme))
                                        }
                                        onActivated: {
                                            const values = ["leos-original", "light", "cyan", "magenta", "gaming"]
                                            controlCenter.setTheme(values[currentIndex])
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8
                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 6
                                            radius: 3
                                            color: window.themeColors.accent_primary
                                        }
                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 6
                                            radius: 3
                                            color: window.themeColors.accent_secondary
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 286
                                radius: 15
                                color: window.themeColors.surface
                                border.color: window.themeColors.border

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    spacing: 10

                                    Label {
                                        text: "FONDS D'ÉCRAN LEOS"
                                        color: window.cyan
                                        font.pixelSize: 11
                                        font.letterSpacing: 2
                                    }
                                    Label {
                                        text: "Deux fonds 4K assortis à chaque mode. Les aperçus utilisent les emblèmes officiels ; rien n'est appliqué sans ton choix dans KDE."
                                        color: window.muted
                                        font.pixelSize: 11
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 12

                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 5
                                            Rectangle {
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: 112
                                                radius: 8
                                                color: "#05070b"
                                                clip: true
                                                Image {
                                                    id: desktopWallpaperPreview
                                                    anchors.fill: parent
                                                    source: "../../branding/wallpapers/desktop-leos.svg"
                                                    fillMode: Image.PreserveAspectFit
                                                    asynchronous: true
                                                    visible: status === Image.Ready
                                                }
                                                Label {
                                                    anchors.centerIn: parent
                                                    visible: desktopWallpaperPreview.status !== Image.Ready
                                                    text: "APERÇU DESKTOP"
                                                    color: "#a9bacb"
                                                    font.pixelSize: 10
                                                }
                                            }
                                            Label {
                                                text: "DESKTOP · LION SEUL"
                                                color: window.themeColors.text
                                                font.pixelSize: 9
                                                font.weight: Font.DemiBold
                                                horizontalAlignment: Text.AlignHCenter
                                                Layout.fillWidth: true
                                            }
                                        }

                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 5
                                            Rectangle {
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: 112
                                                radius: 8
                                                color: "#05070b"
                                                clip: true
                                                Image {
                                                    id: gamingWallpaperPreview
                                                    anchors.fill: parent
                                                    source: "../../branding/wallpapers/gaming-leos.svg"
                                                    fillMode: Image.PreserveAspectFit
                                                    asynchronous: true
                                                    visible: status === Image.Ready
                                                }
                                                Label {
                                                    anchors.centerIn: parent
                                                    visible: gamingWallpaperPreview.status !== Image.Ready
                                                    text: "APERÇU GAMING"
                                                    color: "#a9bacb"
                                                    font.pixelSize: 10
                                                }
                                            }
                                            Label {
                                                text: "GAMING · LION + MANETTE"
                                                color: window.themeColors.text
                                                font.pixelSize: 9
                                                font.weight: Font.DemiBold
                                                horizontalAlignment: Text.AlignHCenter
                                                Layout.fillWidth: true
                                            }
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Button {
                                            text: "CHOISIR DANS LES PARAMÈTRES KDE"
                                            onClicked: {
                                                const opened = controlCenter.openSettingsModule("wallpaper")
                                                window.wallpaperNotice = opened
                                                    ? "Paramètres KDE ouverts. Dans le sélecteur, ouvre /usr/share/leos/branding/wallpapers/ puis choisis desktop-leos.svg ou gaming-leos.svg."
                                                    : "Le module de fond d'écran KDE n'est pas disponible sur cette session."
                                            }
                                        }
                                        Item { Layout.fillWidth: true }
                                    }
                                    Label {
                                        text: window.wallpaperNotice
                                        color: window.muted
                                        font.pixelSize: 10
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 190
                                radius: 15
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    spacing: 9
                                    Label {
                                        text: "THÈME KDE PLASMA"
                                        color: window.cyan
                                        font.pixelSize: 11
                                        font.letterSpacing: 2
                                    }
                                    Label {
                                        text: "Transfère la palette LEOS vers les applications KDE et les éléments Plasma compatibles. L'application demande toujours une confirmation."
                                        color: window.muted
                                        font.pixelSize: 11
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                    Label {
                                        text: "Schéma KDE actif : " + controlCenter.activeKdeColorScheme
                                        color: window.themeColors.text
                                        font.pixelSize: 10
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8
                                        Button {
                                            text: "Appliquer à KDE"
                                            enabled: controlCenter.kdeColorSchemeToolAvailable
                                            onClicked: {
                                                kdeThemeConfirmation.action = "apply"
                                                kdeThemeConfirmation.open()
                                            }
                                        }
                                        Button {
                                            text: "Restaurer le précédent"
                                            enabled: controlCenter.canRestoreKdeTheme
                                            onClicked: {
                                                kdeThemeConfirmation.action = "restore"
                                                kdeThemeConfirmation.open()
                                            }
                                        }
                                    }
                                    Label {
                                        text: !controlCenter.kdeColorSchemeToolAvailable
                                            ? "Outil plasma-apply-colorscheme indisponible sur cette session."
                                            : window.kdeThemeNotice
                                        color: window.muted
                                        font.pixelSize: 10
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 190
                                radius: 15
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    spacing: 9
                                    Label {
                                        text: "STYLE DE BUREAU LEOS"
                                        color: window.cyan
                                        font.pixelSize: 11
                                        font.letterSpacing: 2
                                    }
                                    Label {
                                        text: "Habillage Plasma : panneaux, widgets et fenêtres contextuelles. Les éléments non personnalisés conservent le style Breeze."
                                        color: window.muted
                                        font.pixelSize: 11
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                    Label {
                                        text: "Style actif : " + controlCenter.activePlasmaStyle
                                        color: window.themeColors.text
                                        font.pixelSize: 10
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8
                                        Button {
                                            text: "Appliquer le style LEOS"
                                            enabled: controlCenter.plasmaStyleToolAvailable && controlCenter.plasmaStyleInstalled
                                            onClicked: {
                                                plasmaStyleConfirmation.action = "apply"
                                                plasmaStyleConfirmation.open()
                                            }
                                        }
                                        Button {
                                            text: "Restaurer le précédent"
                                            enabled: controlCenter.canRestorePlasmaStyle
                                            onClicked: {
                                                plasmaStyleConfirmation.action = "restore"
                                                plasmaStyleConfirmation.open()
                                            }
                                        }
                                    }
                                    Label {
                                        text: !controlCenter.plasmaStyleInstalled
                                            ? "Paquet Plasma Style LEOS indisponible."
                                            : !controlCenter.plasmaStyleToolAvailable
                                                ? "Outil plasma-apply-desktoptheme indisponible."
                                                : window.plasmaStyleNotice
                                        color: window.muted
                                        font.pixelSize: 10
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 205
                                radius: 15
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    spacing: 10
                                    Label {
                                        text: "EXPÉRIENCE"
                                        color: window.cyan
                                        font.pixelSize: 11
                                        font.letterSpacing: 2
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Label { text: "Animations LEOS"; color: window.themeColors.text; Layout.fillWidth: true }
                                        Switch {
                                            checked: controlCenter.animationsEnabled
                                            onToggled: controlCenter.setAnimationsEnabled(checked)
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Label { text: "Sons LEOS"; color: window.themeColors.text; Layout.fillWidth: true }
                                        Switch {
                                            checked: controlCenter.soundsEnabled
                                            onToggled: controlCenter.setSoundsEnabled(checked)
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 390
                                radius: 15
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    spacing: 9
                                    Label {
                                        text: "BUREAU & DOCK"
                                        color: window.cyan
                                        font.pixelSize: 11
                                        font.letterSpacing: 2
                                    }
                                    Label {
                                        text: "Choisis un profil et prépare la disposition de ton bureau."
                                        color: window.muted
                                        font.pixelSize: 12
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                    ComboBox {
                                        id: desktopLayoutBox
                                        Layout.fillWidth: true
                                        model: ["LEOS par défaut", "Minimal", "Espace de travail", "Personnalisé"]
                                        Component.onCompleted: {
                                            const values = ["leos-default", "minimal", "workspace", "custom"]
                                            currentIndex = Math.max(0, values.indexOf(controlCenter.desktopLayoutProfile))
                                        }
                                        onActivated: {
                                            const values = ["leos-default", "minimal", "workspace", "custom"]
                                            if (values[currentIndex] !== "custom")
                                                controlCenter.applyDesktopLayout(values[currentIndex])
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Label { text: "Afficher le dock"; color: window.themeColors.text; Layout.fillWidth: true }
                                        Switch {
                                            checked: controlCenter.dockEnabled
                                            onToggled: { controlCenter.setDockEnabled(checked); desktopLayoutBox.currentIndex = 3 }
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Label { text: "Position du dock"; color: window.themeColors.text; Layout.fillWidth: true }
                                        ComboBox {
                                            id: dockPositionBox
                                            Layout.preferredWidth: 150
                                            model: ["Bas", "Haut", "Gauche", "Droite"]
                                            Component.onCompleted: {
                                                const values = ["bottom", "top", "left", "right"]
                                                currentIndex = Math.max(0, values.indexOf(controlCenter.dockPosition))
                                            }
                                            onActivated: {
                                                const values = ["bottom", "top", "left", "right"]
                                                controlCenter.setDockPosition(values[currentIndex]); desktopLayoutBox.currentIndex = 3
                                            }
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Label { text: "Alignement"; color: window.themeColors.text; Layout.fillWidth: true }
                                        ComboBox {
                                            id: dockAlignmentBox
                                            Layout.preferredWidth: 150
                                            model: ["Gauche", "Centre", "Droite"]
                                            Component.onCompleted: {
                                                const values = ["left", "center", "right"]
                                                currentIndex = Math.max(0, values.indexOf(controlCenter.dockAlignment))
                                            }
                                            onActivated: {
                                                const values = ["left", "center", "right"]
                                                controlCenter.setDockAlignment(values[currentIndex]); desktopLayoutBox.currentIndex = 3
                                            }
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Label { text: "Masquer automatiquement"; color: window.themeColors.text; Layout.fillWidth: true }
                                        Switch {
                                            checked: controlCenter.dockAutoHide
                                            onToggled: { controlCenter.setDockAutoHide(checked); desktopLayoutBox.currentIndex = 3 }
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Label { text: "Widgets du bureau"; color: window.themeColors.text; Layout.fillWidth: true }
                                        Switch {
                                            checked: controlCenter.desktopWidgetsEnabled
                                            onToggled: { controlCenter.setDesktopWidgetsEnabled(checked); desktopLayoutBox.currentIndex = 3 }
                                        }
                                    }
                                    Label {
                                        text: "Préférences enregistrées localement. KDE Plasma ne sera pas modifié tant que l’application du profil avec sauvegarde/restauration n’est pas prête."
                                        color: window.muted
                                        font.pixelSize: 10
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 195
                                radius: 15
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    spacing: 10
                                    Label {
                                        text: "SAUVEGARDE PLASMA"
                                        color: window.cyan
                                        font.pixelSize: 11
                                        font.letterSpacing: 2
                                    }
                                    Label {
                                        text: "Crée une copie privée de la disposition actuelle avant toute future personnalisation du bureau."
                                        color: window.muted
                                        font.pixelSize: 11
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                    Button {
                                        text: "Créer une sauvegarde"
                                        enabled: controlCenter.plasmaConfigAvailable
                                        onClicked: plasmaBackupNotice.text = controlCenter.createPlasmaBackup()
                                    }
                                    Label {
                                        id: plasmaBackupNotice
                                        text: controlCenter.hasPlasmaBackup ? "Une sauvegarde LEOS existe déjà." : "Aucune sauvegarde LEOS pour le moment."
                                        color: window.muted
                                        font.pixelSize: 10
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 300
                                radius: 15
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    spacing: 10
                                    Label {
                                        text: "INSPECTION DU BUREAU KDE"
                                        color: window.cyan
                                        font.pixelSize: 11
                                        font.letterSpacing: 2
                                    }
                                    Label {
                                        text: "Analyse les panneaux et les composants Plasma existants. Cette opération est strictement en lecture seule."
                                        color: window.muted
                                        font.pixelSize: 11
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                    Button {
                                        text: "Analyser la configuration Plasma"
                                        onClicked: plasmaInspectionReport.text = controlCenter.inspectPlasmaLayout()
                                    }
                                    Label {
                                        id: plasmaInspectionReport
                                        text: "Aucune analyse effectuée. LEOS ne modifiera pas ton bureau pendant cette inspection."
                                        color: window.themeColors.text
                                        font.pixelSize: 10
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }

                    ScrollView {
                        clip: true
                        ColumnLayout {
                            width: pages.width - 12
                            spacing: 14
                            Label {
                                text: "MATÉRIEL & CONNEXIONS"
                                color: window.themeColors.text
                                font.pixelSize: 20
                                font.weight: Font.Bold
                            }
                            Label {
                                text: "Inventaire réel du matériel et des périphériques connectés. Les détections sont en lecture seule ; les réglages avancés restent accessibles dans KDE."
                                color: window.muted
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                columnSpacing: 12
                                rowSpacing: 12

                                Repeater {
                                    model: [
                                        { title: "Bluetooth", description: "Manettes, casques, claviers et souris", section: "bluetooth" },
                                        { title: "Réseau", description: "Wi-Fi, Ethernet et connexions", section: "network" },
                                        { title: "Audio", description: "Sortie, entrée et périphériques audio", section: "audio" },
                                        { title: "Écrans", description: "Résolution, fréquence et disposition", section: "display" },
                                        { title: "Énergie", description: "Gestion de l'alimentation et autonomie", section: "power" },
                                        { title: "Clavier", description: "Disposition et comportement du clavier", section: "keyboard" },
                                        { title: "Souris & pavé tactile", description: "Vitesse, clics et défilement", section: "mouse" }
                                    ]
                                    delegate: Rectangle {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 132
                                        radius: 12
                                        color: window.themeColors.surface
                                        border.color: window.themeColors.border
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 14
                                            spacing: 7
                                            Label {
                                                text: modelData.title
                                                color: window.themeColors.text
                                                font.pixelSize: 14
                                                font.weight: Font.DemiBold
                                            }
                                            Label {
                                                text: modelData.description
                                                color: window.muted
                                                font.pixelSize: 10
                                                wrapMode: Text.WordWrap
                                                Layout.fillWidth: true
                                                Layout.fillHeight: true
                                            }
                                            Button {
                                                text: "Ouvrir les réglages"
                                                onClicked: {
                                                    window.launchNotice = controlCenter.openSettingsModule(modelData.section)
                                                        ? ""
                                                        : "Impossible d'ouvrir ce module KDE sur cette session."
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Button {
                                    text: "ACTUALISER LE MATÉRIEL"
                                    onClicked: controlCenter.scanHardwareNow()
                                }
                                Item { Layout.fillWidth: true }
                                Label {
                                    text: "Actualisation automatique · 10 s"
                                    color: window.muted
                                    font.pixelSize: 10
                                }
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                columnSpacing: 12
                                rowSpacing: 12
                                Repeater {
                                    model: [
                                        { title: "PROCESSEUR", value: controlCenter.hardwareSnapshot.cpu, detail: controlCenter.hardwareSnapshot.cpuCores + " · " + controlCenter.hardwareSnapshot.cpuThreads },
                                        { title: "ARCHITECTURE", value: controlCenter.hardwareSnapshot.architecture, detail: "Architecture de l'image Bazzite ciblée : x86_64" },
                                        { title: "MICROLOGICIEL", value: controlCenter.hardwareSnapshot.firmware, detail: "Le démarrage UEFI est requis par la base Bazzite" },
                                        { title: "RAM TOTALE", value: controlCenter.hardwareSnapshot.memoryTotal, detail: "Référence Gaming Bazzite : 8 Go minimum" },
                                        { title: "PRÉCONTRÔLE GAMING", value: controlCenter.hardwareSnapshot.gamingBaseline, detail: "Références : 4 cœurs, 8 Go, 50 Go libres et Vulkan 1.3+. Certains critères ne peuvent pas être certifiés automatiquement." },
                                        { title: "MÉMOIRE VIVE", value: controlCenter.hardwareSnapshot.memory, detail: "RAM détectée par Linux" },
                                        { title: "CARTE GRAPHIQUE", value: controlCenter.hardwareSnapshot.gpu, detail: "Contrôleur graphique détecté" },
                                        { title: "ÉCRANS CONNECTÉS", value: controlCenter.hardwareSnapshot.displayCount, detail: controlCenter.hardwareSnapshot.displays + " · Modes proposés par le pilote, pas nécessairement la résolution active." },
                                        { title: "VULKAN", value: controlCenter.hardwareSnapshot.vulkan, detail: "Version exposée par chaque GPU, si le pilote la fournit" },
                                        { title: "STOCKAGE", value: controlCenter.hardwareSnapshot.storage, detail: "Espace libre sur / ; le type SSD et la destination d'installation ne sont pas vérifiés" },
                                        { title: "SYSTÈME", value: controlCenter.hardwareSnapshot.operatingSystem, detail: "Noyau " + controlCenter.hardwareSnapshot.kernel },
                                        { title: "BLUETOOTH", value: controlCenter.hardwareSnapshot.bluetooth, detail: controlCenter.hardwareSnapshot.bluetoothDevices },
                                        { title: "SERVEUR AUDIO", value: controlCenter.hardwareSnapshot.audioServer, detail: "Sortie : " + controlCenter.hardwareSnapshot.audioOutput },
                                        { title: "ENTRÉES AUDIO", value: controlCenter.hardwareSnapshot.audioInputs, detail: "Sources exposées par PipeWire / PulseAudio" },
                                        { title: "MANETTES", value: controlCenter.hardwareSnapshot.controllers, detail: "Périphériques d’entrée reconnus comme contrôleurs" },
                                        { title: "BATTERIE", value: controlCenter.hardwareSnapshot.battery, detail: "État exposé par le noyau Linux" },
                                        { title: "PÉRIPHÉRIQUES USB", value: controlCenter.hardwareSnapshot.usbDevices, detail: "Liste des périphériques USB identifiés" },
                                        { title: "RÉSEAU", value: controlCenter.hardwareSnapshot.network, detail: "Interfaces locales et adresses IP" }
                                    ]
                                    delegate: Rectangle {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 116
                                        radius: 13
                                        color: window.themeColors.surface
                                        border.color: window.themeColors.border
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 14
                                            spacing: 6
                                            Label {
                                                text: modelData.title
                                                color: window.cyan
                                                font.pixelSize: 10
                                                font.letterSpacing: 1
                                            }
                                            Label {
                                                text: modelData.value || "Indisponible"
                                                color: window.themeColors.text
                                                font.pixelSize: 13
                                                font.weight: Font.DemiBold
                                                wrapMode: Text.WordWrap
                                                Layout.fillWidth: true
                                            }
                                            Label {
                                                text: modelData.detail || ""
                                                color: window.muted
                                                font.pixelSize: 10
                                                wrapMode: Text.WordWrap
                                                Layout.fillWidth: true
                                            }
                                        }
                                    }
                                }
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                columnSpacing: 12
                                rowSpacing: 12
                                Repeater {
                                    model: [
                                        { title: "Bluetooth", description: "Appairage et gestion des appareils", section: "bluetooth" },
                                        { title: "Réseau", description: "Wi-Fi, Ethernet et connexions", section: "network" },
                                        { title: "Audio", description: "Sortie, entrée et périphériques audio", section: "audio" },
                                        { title: "Écrans", description: "Résolution, fréquence et disposition", section: "display" },
                                        { title: "Énergie", description: "Gestion de l'alimentation et autonomie", section: "power" },
                                        { title: "Clavier", description: "Disposition et comportement du clavier", section: "keyboard" },
                                        { title: "Souris & pavé tactile", description: "Vitesse, clics et défilement", section: "mouse" }
                                    ]
                                    delegate: Rectangle {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 118
                                        radius: 12
                                        color: window.themeColors.surface
                                        border.color: window.themeColors.border
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 14
                                            spacing: 7
                                            Label {
                                                text: modelData.title
                                                color: window.themeColors.text
                                                font.pixelSize: 14
                                                font.weight: Font.DemiBold
                                            }
                                            Label {
                                                text: modelData.description
                                                color: window.muted
                                                font.pixelSize: 10
                                                wrapMode: Text.WordWrap
                                                Layout.fillWidth: true
                                                Layout.fillHeight: true
                                            }
                                            Button {
                                                text: "Ouvrir les réglages"
                                                onClicked: {
                                                    window.launchNotice = controlCenter.openSettingsModule(modelData.section)
                                                        ? ""
                                                        : "Impossible d'ouvrir ce module KDE sur cette session."
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            Label {
                                text: window.launchNotice
                                visible: text.length > 0
                                color: window.magenta
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }

                    ScrollView {
                        clip: true
                        ColumnLayout {
                            width: pages.width - 12
                            spacing: 14
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 190
                                radius: 15
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    spacing: 10
                                    Label {
                                        text: "PROFIL DE PERFORMANCES"
                                        color: window.cyan
                                        font.pixelSize: 11
                                        font.letterSpacing: 2
                                    }
                                    Label {
                                        text: "Le choix est enregistré localement. L'application réelle des profils CPU/GPU reste à intégrer et à valider sur le matériel."
                                        color: window.muted
                                        font.pixelSize: 11
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                    ComboBox {
                                        id: profileBox
                                        Layout.fillWidth: true
                                        model: ["Performance", "Balanced", "Quiet", "Battery Saver"]
                                        Component.onCompleted: {
                                            const values = ["performance", "balanced", "quiet", "battery-saver"]
                                            currentIndex = Math.max(0, values.indexOf(controlCenter.performanceProfile))
                                        }
                                        onActivated: {
                                            const values = ["performance", "balanced", "quiet", "battery-saver"]
                                            controlCenter.setPerformanceProfile(values[currentIndex])
                                        }
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 105
                                radius: 15
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    Label {
                                        text: "Overlay de performances en jeu"
                                        color: window.themeColors.text
                                        Layout.fillWidth: true
                                    }
                                    Switch {
                                        checked: controlCenter.gamingOverlayEnabled
                                        onToggled: controlCenter.setGamingOverlayEnabled(checked)
                                    }
                                }
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }

                    ColumnLayout {
                        spacing: 14
                        Label {
                            text: "PARAMÈTRES KDE"
                            color: window.themeColors.text
                            font.pixelSize: 20
                            font.weight: Font.Bold
                        }
                        Label {
                            text: "Les paramètres avancés restent ceux de KDE et de Bazzite. LEOS ne remplace pas les outils natifs du système."
                            color: window.muted
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Button {
                            text: "OUVRIR TOUS LES PARAMÈTRES KDE"
                            onClicked: {
                                window.launchNotice = controlCenter.openAdvancedSettings()
                                    ? ""
                                    : "System Settings KDE est introuvable sur cette session."
                            }
                        }
                        Label {
                            text: window.launchNotice
                            visible: text.length > 0
                            color: window.magenta
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Item { Layout.fillHeight: true }
                    }

                    ScrollView {
                        clip: true
                        ColumnLayout {
                            width: pages.width - 12
                            spacing: 16
                            Label {
                                text: "MISES À JOUR DU SYSTÈME"
                                color: window.themeColors.text
                                font.pixelSize: 20
                                font.weight: Font.Bold
                            }
                            Label {
                                text: "LEOS suit les déploiements préparés par Bazzite et vérifie leur état localement, sans lancer de téléchargement ni d’installation."
                                color: window.muted
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 230
                                radius: 15
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    spacing: 14
                                    Label {
                                        text: "ÉTAT DU SYSTÈME"
                                        color: window.cyan
                                        font.pixelSize: 11
                                        font.letterSpacing: 2
                                    }
                                    Label {
                                        text: controlCenter.systemUpdateStatus
                                        color: window.themeColors.text
                                        font.pixelSize: 13
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Button {
                                            text: controlCenter.systemUpdateCheckRunning ? "VÉRIFICATION…" : "VÉRIFIER MAINTENANT"
                                            enabled: !controlCenter.systemUpdateCheckRunning
                                            onClicked: controlCenter.checkForSystemUpdates()
                                        }
                                        Item { Layout.fillWidth: true }
                                        BusyIndicator {
                                            running: controlCenter.systemUpdateCheckRunning
                                            visible: running
                                            implicitWidth: 28
                                            implicitHeight: 28
                                        }
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 210
                                radius: 15
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    spacing: 12
                                    Label {
                                        text: "INSTALLATION MANUELLE"
                                        color: window.magenta
                                        font.pixelSize: 11
                                        font.letterSpacing: 2
                                    }
                                    Label {
                                        text: "Lorsqu'une mise à jour est disponible, Bazzite Updater permet de consulter les détails, les changements et les options de retour arrière. L'installation reste une action volontaire dans cet outil."
                                        color: window.muted
                                        font.pixelSize: 11
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                    Button {
                                        text: "OUVRIR BAZZITE UPDATER"
                                        enabled: controlCenter.systemUpdaterAvailable
                                        onClicked: {
                                            if (!controlCenter.openSystemUpdater())
                                                window.launchNotice = "Bazzite Updater est introuvable ou n'a pas pu être lancé."
                                            else
                                                window.launchNotice = ""
                                        }
                                    }
                                    Label {
                                        text: controlCenter.systemUpdaterAvailable
                                              ? "Bazzite Updater est disponible."
                                              : "Bazzite Updater n'est pas détecté sur cette image."
                                        color: window.muted
                                        font.pixelSize: 10
                                        wrapMode: Text.WordWrap
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                            Label {
                                text: "Bazzite effectue ses vérifications automatiques selon la politique native de l’image. LEOS observe périodiquement les déploiements préparés avec rpm-ostree, sans démarrer de transaction. L’application d’une version préparée se fait au redémarrage."
                                color: window.muted
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }

                    ScrollView {
                        clip: true
                        ColumnLayout {
                            width: pages.width - 12
                            spacing: 16
                            Label {
                                text: "NOTIFICATIONS"
                                color: window.themeColors.text
                                font.pixelSize: 20
                                font.weight: Font.Bold
                            }
                            Label {
                                text: "Choisis comment LEOS te prévient. Les événements restent dans l’historique même si les fenêtres contextuelles sont désactivées ou filtrées."
                                color: window.muted
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 82
                                radius: 14
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 18
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Label { text: "Notifications système"; color: window.themeColors.text; font.weight: Font.DemiBold }
                                        Label { text: "Autoriser les fenêtres natives du bureau"; color: window.muted; font.pixelSize: 11 }
                                    }
                                    Switch {
                                        checked: controlCenter.notificationsEnabled
                                        onToggled: controlCenter.setNotificationsEnabled(checked)
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 112
                                radius: 14
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 18
                                    Label { text: "DURÉE D’AFFICHAGE"; color: window.cyan; font.pixelSize: 11; font.letterSpacing: 1.5 }
                                    ComboBox {
                                        id: notificationDurationBox
                                        Layout.fillWidth: true
                                        model: ["Courte — 3 secondes", "Normale — 5 secondes", "Longue — 8 secondes"]
                                        Component.onCompleted: currentIndex = controlCenter.notificationDuration === 3 ? 0 : (controlCenter.notificationDuration === 8 ? 2 : 1)
                                        onActivated: controlCenter.setNotificationDuration([3, 5, 8][currentIndex])
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 112
                                radius: 14
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 18
                                    Label { text: "NIVEAU DE PRIORITÉ"; color: window.cyan; font.pixelSize: 11; font.letterSpacing: 1.5 }
                                    ComboBox {
                                        id: notificationPriorityBox
                                        Layout.fillWidth: true
                                        model: ["Toutes les notifications", "Importantes et critiques", "Critiques uniquement"]
                                        Component.onCompleted: currentIndex = ["all", "important", "critical"].indexOf(controlCenter.notificationMinimumPriority)
                                        onActivated: controlCenter.setNotificationMinimumPriority(["all", "important", "critical"][currentIndex])
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 82
                                radius: 14
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 18
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Label { text: "Sons de notification"; color: window.themeColors.text; font.weight: Font.DemiBold }
                                        Label { text: "Utilise le son configuré par KDE lorsqu’il est pris en charge"; color: window.muted; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                    }
                                    Switch {
                                        checked: controlCenter.notificationSoundsEnabled
                                        onToggled: controlCenter.setNotificationSoundsEnabled(checked)
                                    }
                                }
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 82
                                radius: 14
                                color: window.themeColors.surface
                                border.color: window.themeColors.border
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 18
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Label { text: "Mode silencieux en Gaming Mode"; color: window.themeColors.text; font.weight: Font.DemiBold }
                                        Label { text: "Conserve les événements dans l’historique sans interrompre le jeu"; color: window.muted; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                    }
                                    Switch {
                                        checked: controlCenter.silentNotificationsInGaming
                                        onToggled: controlCenter.setSilentNotificationsInGaming(checked)
                                    }
                                }
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }

                    ScrollView {
                        clip: true
                        ColumnLayout {
                            width: pages.width - 12
                            spacing: 14
                            Label {
                                text: "DIAGNOSTIC SYSTÈME"
                                color: window.themeColors.text
                                font.pixelSize: 20
                                font.weight: Font.Bold
                            }
                            Label {
                                text: "Contrôles de santé en lecture seule. LEOS signale les anomalies détectables sans réparer, redémarrer ou modifier les services."
                                color: window.muted
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 112
                                radius: 14
                                color: window.themeColors.surface
                                border.color: controlCenter.diagnosticsSnapshot.severity === "Critique" ? window.magenta : (controlCenter.diagnosticsSnapshot.severity === "Attention" ? window.cyan : window.themeColors.border)
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 18
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Label {
                                            text: "ÉTAT GÉNÉRAL · " + (controlCenter.diagnosticsSnapshot.severity || "Inconnu").toUpperCase()
                                            color: controlCenter.diagnosticsSnapshot.severity === "Critique" ? window.magenta : window.cyan
                                            font.pixelSize: 11
                                            font.letterSpacing: 1.4
                                        }
                                        Label {
                                            text: controlCenter.diagnosticsSnapshot.summary || "Analyse en cours…"
                                            color: window.themeColors.text
                                            font.pixelSize: 12
                                            wrapMode: Text.WordWrap
                                            Layout.fillWidth: true
                                        }
                                    }
                                    Button {
                                        text: "ANALYSER"
                                        onClicked: controlCenter.scanDiagnostics()
                                    }
                                    Button {
                                        text: "MONITEUR SYSTÈME"
                                        onClicked: window.launchNotice = controlCenter.openSystemMonitor()
                                            ? ""
                                            : "Le Moniteur système KDE n'est pas disponible sur cette image."
                                    }
                                }
                            }
                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                columnSpacing: 12
                                rowSpacing: 12
                                Repeater {
                                    model: [
                                        { title: "STOCKAGE", value: controlCenter.diagnosticsSnapshot.storage, detail: "Occupation de /" },
                                        { title: "MÉMOIRE", value: controlCenter.diagnosticsSnapshot.memory, detail: "Mémoire utilisée" },
                                        { title: "TEMPÉRATURE", value: controlCenter.diagnosticsSnapshot.temperature, detail: "Maximum des capteurs exposés" },
                                        { title: "SERVICES", value: controlCenter.diagnosticsSnapshot.failedServices, detail: "Unités systemd en échec" },
                                        { title: "CHARGE CPU", value: controlCenter.diagnosticsSnapshot.loadAverage, detail: "Charge système moyenne" },
                                        { title: "TEMPS DE FONCTIONNEMENT", value: controlCenter.diagnosticsSnapshot.uptime, detail: "Depuis le dernier démarrage" },
                                        { title: "JOURNAUX", value: controlCenter.diagnosticsSnapshot.recentErrors, detail: "Erreurs sur la dernière heure, aperçu limité" }
                                    ]
                                    delegate: Rectangle {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 108
                                        radius: 13
                                        color: window.themeColors.surface
                                        border.color: window.themeColors.border
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 14
                                            spacing: 6
                                            Label { text: modelData.title; color: window.cyan; font.pixelSize: 10; font.letterSpacing: 1 }
                                            Label {
                                                text: modelData.value || "Indisponible"
                                                color: window.themeColors.text
                                                font.pixelSize: 12
                                                font.weight: Font.DemiBold
                                                wrapMode: Text.WordWrap
                                                Layout.fillWidth: true
                                            }
                                            Label {
                                                text: modelData.detail
                                                color: window.muted
                                                font.pixelSize: 10
                                                wrapMode: Text.WordWrap
                                                Layout.fillWidth: true
                                            }
                                        }
                                    }
                                }
                            }
                            Label {
                                text: "POINTS À VÉRIFIER"
                                color: window.cyan
                                font.pixelSize: 11
                                font.letterSpacing: 1.4
                            }
                            Repeater {
                                model: controlCenter.diagnosticsSnapshot.findings || []
                                delegate: Rectangle {
                                    required property string modelData
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: findingText.implicitHeight + 28
                                    radius: 10
                                    color: window.themeColors.surface
                                    border.color: window.themeColors.border
                                    Label {
                                        id: findingText
                                        anchors.fill: parent
                                        anchors.margins: 14
                                        text: modelData
                                        color: window.themeColors.text
                                        font.pixelSize: 12
                                        wrapMode: Text.WordWrap
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                            Label {
                                text: "PROCESSUS LES PLUS ACTIFS"
                                color: window.cyan
                                font.pixelSize: 11
                                font.letterSpacing: 1.4
                            }
                            Repeater {
                                model: controlCenter.diagnosticsSnapshot.topProcesses || []
                                delegate: Rectangle {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 66
                                    radius: 10
                                    color: window.themeColors.surface
                                    border.color: window.themeColors.border
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 12
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 3
                                            Label {
                                                text: modelData.name + " · PID " + modelData.pid
                                                color: window.themeColors.text
                                                font.pixelSize: 12
                                                font.weight: Font.DemiBold
                                                elide: Text.ElideRight
                                                Layout.fillWidth: true
                                            }
                                            Label {
                                                text: "CPU " + modelData.cpu + "  ·  RAM " + modelData.memory + "  ·  " + modelData.resident
                                                color: window.muted
                                                font.pixelSize: 10
                                            }
                                        }
                                    }
                                }
                            }
                            Label {
                                text: "Les journaux ne sont pas affichés dans LEOS : seule une quantité d’entrées d’erreur est indiquée. Les contrôles peuvent être incomplets si les outils ou permissions système ne sont pas disponibles."
                                color: window.muted
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }

                    ScrollView {
                        clip: true
                        ColumnLayout {
                            width: pages.width - 12
                            spacing: 14
                            Label {
                                text: "CENTRE DE NETTOYAGE"
                                color: window.themeColors.text
                                font.pixelSize: 20
                                font.weight: Font.Bold
                            }
                            Label {
                                text: "Prévisualise l’espace occupé par quelques éléments régénérables ou déjà placés dans ta corbeille. Cette analyse ne supprime et ne déplace aucun fichier."
                                color: window.muted
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 100
                                radius: 14
                                color: window.themeColors.surface
                                border.color: window.cyan
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 18
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Label { text: "ESPACE REPÉRÉ"; color: window.cyan; font.pixelSize: 10; font.letterSpacing: 1.5 }
                                        Label {
                                            text: controlCenter.cleanupPreview.totalSize || "Analyse en cours…"
                                            color: window.themeColors.text
                                            font.pixelSize: 22
                                            font.weight: Font.Bold
                                        }
                                        Label { text: "Sur les deux emplacements inspectés"; color: window.muted; font.pixelSize: 10 }
                                    }
                                    Button {
                                        text: "ANALYSER"
                                        onClicked: controlCenter.scanCleanupPreview()
                                    }
                                }
                            }
                            Repeater {
                                model: [
                                    {
                                        title: "CACHE DE MINIATURES",
                                        detail: "Miniatures générées par KDE et les applications. Elles peuvent être recréées après suppression.",
                                        data: controlCenter.cleanupPreview.thumbnails
                                    },
                                    {
                                        title: "CORBEILLE UTILISATEUR",
                                        detail: "Fichiers déjà déplacés dans la corbeille. Les supprimer définitivement nécessite une confirmation distincte.",
                                        data: controlCenter.cleanupPreview.trash
                                    }
                                ]
                                delegate: Rectangle {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 138
                                    radius: 13
                                    color: window.themeColors.surface
                                    border.color: window.themeColors.border
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 16
                                        spacing: 7
                                        Label { text: modelData.title; color: window.cyan; font.pixelSize: 10; font.letterSpacing: 1.2 }
                                        Label {
                                            text: modelData.data.size || "Non disponible"
                                            color: window.themeColors.text
                                            font.pixelSize: 18
                                            font.weight: Font.DemiBold
                                        }
                                        Label {
                                            text: (modelData.data.files || 0) + " fichier(s) · " + modelData.detail
                                            color: window.muted
                                            font.pixelSize: 10
                                            wrapMode: Text.WordWrap
                                            Layout.fillWidth: true
                                        }
                                    }
                                }
                            }
                            Label {
                                text: controlCenter.cleanupPreview.note || ""
                                color: window.muted
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Label {
                                text: "LEOS n’inspecte pas l’ensemble de ~/.cache, les données des applications, les fichiers personnels, les journaux système ni les composants Bazzite. Aucun nettoyage automatique n’est activé."
                                color: window.muted
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }


                    ScrollView {
                        clip: true
                        ColumnLayout {
                            width: pages.width - 12
                            spacing: 14
                            Label {
                                text: "RÉSEAU & CONNECTIVITÉ"
                                color: window.themeColors.text
                                font.pixelSize: 20
                                font.weight: Font.Bold
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Label {
                                    text: controlCenter.networkSnapshot.status || "Analyse en cours…"
                                    color: window.cyan
                                    font.pixelSize: 14
                                    font.weight: Font.DemiBold
                                }
                                Item { Layout.fillWidth: true }
                                Button {
                                    text: "ACTUALISER"
                                    onClicked: controlCenter.scanNetwork()
                                }
                            }
                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                columnSpacing: 10
                                rowSpacing: 10
                                Repeater {
                                    model: [
                                        { title: "INTERFACE PAR DÉFAUT", value: controlCenter.networkSnapshot.defaultInterface },
                                        { title: "PASSERELLE", value: controlCenter.networkSnapshot.gateway },
                                        { title: "SERVEURS DNS", value: controlCenter.networkSnapshot.dns },
                                        { title: "RÉSEAU WI-FI", value: controlCenter.networkSnapshot.wifiSsid },
                                        { title: "SIGNAL WI-FI", value: controlCenter.networkSnapshot.wifiSignal }
                                    ]
                                    delegate: Rectangle {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 86
                                        radius: 11
                                        color: window.themeColors.surface
                                        border.color: window.themeColors.border
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 13
                                            spacing: 6
                                            Label {
                                                text: modelData.title
                                                color: window.cyan
                                                font.pixelSize: 9
                                                font.letterSpacing: 1
                                            }
                                            Label {
                                                text: modelData.value || "Non détecté"
                                                color: window.themeColors.text
                                                font.pixelSize: 13
                                                font.weight: Font.DemiBold
                                                elide: Text.ElideRight
                                                Layout.fillWidth: true
                                            }
                                        }
                                    }
                                }
                            }
                            Label {
                                text: "INTERFACES DÉTECTÉES"
                                color: window.cyan
                                font.pixelSize: 11
                                font.letterSpacing: 1.4
                            }
                            Repeater {
                                model: controlCenter.networkSnapshot.interfaces || []
                                delegate: Rectangle {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 126
                                    radius: 12
                                    color: window.themeColors.surface
                                    border.color: modelData.isDefault === "true" ? window.cyan : window.themeColors.border
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 14
                                        spacing: 6
                                        RowLayout {
                                            Layout.fillWidth: true
                                            Label {
                                                text: modelData.name + " · " + modelData.type
                                                color: window.themeColors.text
                                                font.pixelSize: 13
                                                font.weight: Font.DemiBold
                                            }
                                            Item { Layout.fillWidth: true }
                                            Label {
                                                text: modelData.state + (modelData.isDefault === "true" ? " · PRINCIPALE" : "")
                                                color: modelData.state === "Connectée" ? window.cyan : window.muted
                                                font.pixelSize: 9
                                            }
                                        }
                                        Label {
                                            text: modelData.addresses
                                            color: window.muted
                                            font.pixelSize: 10
                                        }
                                        Label {
                                            text: "↓ " + modelData.downloadRate + "     ↑ " + modelData.uploadRate
                                            color: window.themeColors.text
                                            font.pixelSize: 12
                                            font.weight: Font.DemiBold
                                        }
                                    }
                                }
                            }
                            Label {
                                text: "Les débits sont calculés à partir des compteurs locaux du noyau entre deux relevés. LEOS ne lance aucun test de débit, aucune requête Internet et ne modifie pas la configuration réseau."
                                color: window.muted
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }

                }
            }
        }
    }
}
