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
            const layouts = ["leos-default", "minimal", "workspace", "custom"]
            desktopLayoutBox.currentIndex = Math.max(0, layouts.indexOf(controlCenter.desktopLayoutProfile))
            const positions = ["bottom", "top", "left", "right"]
            dockPositionBox.currentIndex = Math.max(0, positions.indexOf(controlCenter.dockPosition))
            const alignments = ["left", "center", "right"]
            dockAlignmentBox.currentIndex = Math.max(0, alignments.indexOf(controlCenter.dockAlignment))
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
            Layout.preferredWidth: 420
            padding: 12
        }
        onAccepted: {
            if (action === "apply")
                window.kdeThemeNotice = controlCenter.applyKdeTheme()
            else
                window.kdeThemeNotice = controlCenter.restorePreviousKdeTheme()
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
                            { label: "Paramètres KDE", page: 4 }
                        ]
                        delegate: Button {
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
                                text: parent.text
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
                                text: "Accède directement aux réglages KDE. LEOS ne modifie aucun périphérique sans ton action."
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
                }
            }
        }
    }
}
