import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtMultimedia

ApplicationWindow {
    id: window
    width: 1440
    height: 900
    visible: true
    visibility: Window.FullScreen
    title: "LEOS Gaming"
    property var themeColors: leos.themePalette
    color: themeColors.background

    property color cyan: themeColors.accent_primary
    property color magenta: themeColors.accent_secondary
    property color muted: themeColors.muted_text
    property int selectedIndex: -1
    property string selectedTitle: ""
    property string selectedPlatform: ""
    property string selectedSource: ""
    property string selectedArtwork: ""
    property string selectedInstallStatus: ""
    property string selectedAppId: ""
    property int selectedDuplicateCount: 1
    property string selectedDuplicateSources: ""
    property bool selectedArtworkFailed: false
    property string selectedCategory: "Accueil"
    property bool selectedIsFavorite: false
    property var categoryNames: ["Accueil", "PC Gaming", "Nintendo", "PlayStation", "SEGA", "Arcade", "Favoris", "Récemment joués"]
    property int selectedCategoryIndex: 0
    property string navigationArea: "categories"
    property string pendingPowerProfile: ""
    property bool returningToDesktop: false
    property int quickPanelFocusIndex: 0
    property int toolbarFocusIndex: 0
    property int detailsActionIndex: 0

    function requestDesktopReturn() {
        if (returningToDesktop)
            return
        if (!leos.animationsEnabled) {
            leos.returnToDesktop()
            return
        }
        returningToDesktop = true
        desktopIntroOverlay.visible = true
        desktopIntroPlayer.source = leosTheme.desktopIntroUrl
        desktopIntroAudio.muted = !leos.soundsEnabled
        desktopIntroTimeout.start()
        desktopIntroPlayer.play()
    }

    function finishDesktopReturn() {
        if (!returningToDesktop)
            return
        returningToDesktop = false
        desktopIntroTimeout.stop()
        desktopIntroPlayer.stop()
        desktopIntroOverlay.visible = false
        leos.returnToDesktop()
    }

    function gameMonogram(title) {
        const words = String(title || "").trim().split(/\s+/).filter(Boolean)
        if (words.length === 0)
            return "LE"
        return words.slice(0, 2).map(word => word.charAt(0)).join("").toUpperCase()
    }

    function powerProfileLabel(profile) {
        if (profile === "performance") return "PERFORMANCE"
        if (profile === "balanced") return "ÉQUILIBRÉ"
        if (profile === "power-saver") return "ÉCONOMIE D’ÉNERGIE"
        return profile.toUpperCase()
    }

    function selectGame(row, title, platform, source, favorite, artwork, installStatus, appId, duplicateCount, duplicateSources) {
        navigationArea = "games"
        selectedIndex = row
        selectedTitle = title
        selectedPlatform = platform
        selectedSource = source
        selectedIsFavorite = favorite
        selectedArtwork = artwork || ""
        selectedInstallStatus = installStatus || ""
        selectedAppId = appId || ""
        selectedDuplicateCount = duplicateCount || 1
        selectedDuplicateSources = (duplicateSources || []).join(" · ")
        selectedArtworkFailed = false
    }

    function selectGameAt(row) {
        const info = gameLibrary.gameInfo(row)
        if (info && info.title)
            selectGame(row, info.title, info.platform, info.source, info.favorite,
                       info.artwork, info.installStatus, info.appId,
                       info.duplicateCount, info.duplicateSources)
    }

    function clearSelection() {
        selectedIndex = -1
        selectedTitle = ""
        selectedPlatform = ""
        selectedSource = ""
        selectedArtwork = ""
        selectedInstallStatus = ""
        selectedAppId = ""
        selectedDuplicateCount = 1
        selectedDuplicateSources = ""
        selectedArtworkFailed = false
        selectedIsFavorite = false
    }

    function chooseCategory(index) {
        if (index < 0 || index >= categoryNames.length)
            return
        selectedCategoryIndex = index
        selectedCategory = categoryNames[index]
        gameLibrary.setCategory(selectedCategory)
        clearSelection()
        navigationArea = "games"
    }

    function moveCategory(direction) {
        let next = selectedCategoryIndex
        if (direction === "up")
            next -= 1
        else if (direction === "down")
            next += 1
        selectedCategoryIndex = Math.max(0, Math.min(categoryNames.length - 1, next))
    }

    function moveSelection(direction) {
        if (gameGrid.count < 1)
            return
        const columns = Math.max(1, Math.floor(gameGrid.width / gameGrid.cellWidth))
        let next = selectedIndex < 0 ? 0 : selectedIndex
        if (direction === "left")
            next -= 1
        else if (direction === "right")
            next += 1
        else if (direction === "up")
            next -= columns
        else if (direction === "down")
            next += columns
        next = Math.max(0, Math.min(gameGrid.count - 1, next))
        selectGameAt(next)
        gameGrid.positionViewAtIndex(next, GridView.Contain)
    }

    function focusToolbar(index) {
        toolbarFocusIndex = Math.max(0, Math.min(2, index))
        navigationArea = "toolbar"
        if (toolbarFocusIndex === 0)
            searchField.forceActiveFocus()
        else if (toolbarFocusIndex === 1)
            refreshLibraryButton.forceActiveFocus()
        else
            addGameButton.forceActiveFocus()
    }

    function focusDetailsAction(index) {
        if (selectedIndex < 0)
            return
        detailsActionIndex = Math.max(0, Math.min(1, index))
        navigationArea = "details"
        if (detailsActionIndex === 0)
            favoriteGameButton.forceActiveFocus()
        else
            launchSelectedGameButton.forceActiveFocus()
    }

    function activateToolbarFocus() {
        if (toolbarFocusIndex === 0) {
            searchField.forceActiveFocus()
        } else if (toolbarFocusIndex === 1) {
            clearSelection()
            leos.refreshLibrary()
            navigationArea = "games"
            gameGrid.forceActiveFocus()
        } else {
            addDialog.open()
        }
    }

    function toggleSelectedFavorite() {
        if (selectedIndex < 0)
            return
        const row = selectedIndex
        const wasFavorite = selectedIsFavorite
        const nowFavorite = gameLibrary.toggleFavorite(row)
        if (selectedCategory === "Favoris" && wasFavorite && !nowFavorite) {
            clearSelection()
            navigationArea = "games"
            gameGrid.forceActiveFocus()
        } else {
            selectGameAt(row)
            focusDetailsAction(0)
        }
    }

    function launchSelectedGame() {
        if (selectedIndex < 0)
            return
        leos.launchGame(selectedIndex, leos.mangoHudEnabled)
        statusText.text = leos.lastLaunchStatus
        navigationArea = "details"
        detailsActionIndex = 1
    }

    function navigateDirection(action) {
        if (navigationArea === "toolbar") {
            if (action === "left") {
                if (toolbarFocusIndex === 0) {
                    navigationArea = "categories"
                    selectedCategoryIndex = categoryNames.indexOf(selectedCategory)
                } else {
                    focusToolbar(toolbarFocusIndex - 1)
                }
            } else if (action === "right") {
                focusToolbar(toolbarFocusIndex + 1)
            } else if (action === "down") {
                navigationArea = "games"
                const target = selectedIndex >= 0 ? selectedIndex : 0
                if (gameGrid.count > 0) {
                    selectGameAt(target)
                    gameGrid.positionViewAtIndex(target, GridView.Contain)
                }
                gameGrid.forceActiveFocus()
            }
            return
        }
        if (navigationArea === "details") {
            if (action === "left") {
                navigationArea = "games"
                gameGrid.forceActiveFocus()
            } else if (action === "up") {
                focusDetailsAction(detailsActionIndex - 1)
            } else if (action === "down") {
                focusDetailsAction(detailsActionIndex + 1)
            }
            return
        }
        if (navigationArea === "categories") {
            if (action === "up" || action === "down")
                moveCategory(action)
            else if (action === "right") {
                chooseCategory(selectedCategoryIndex)
                if (gameGrid.count > 0)
                    selectGameAt(0)
                gameGrid.forceActiveFocus()
            }
            return
        }
        const columns = Math.max(1, Math.floor(gameGrid.width / gameGrid.cellWidth))
        if (action === "up" && (selectedIndex < 0 || selectedIndex < columns)) {
            focusToolbar(0)
            return
        }
        if (action === "right" && selectedIndex >= 0 &&
                gameGrid.count > 0 &&
                (selectedIndex % columns === columns - 1 ||
                 selectedIndex === gameGrid.count - 1)) {
            focusDetailsAction(0)
            return
        }
        if (action === "left" && (selectedIndex < 0 || selectedIndex % columns === 0)) {
            navigationArea = "categories"
            selectedCategoryIndex = categoryNames.indexOf(selectedCategory)
            return
        }
        moveSelection(action)
    }

    function quickPanelActionCount() {
        return leos.availablePowerProfiles.length + 4
    }

    function moveQuickPanelFocus(direction) {
        const count = quickPanelActionCount()
        if (count < 1)
            return
        const delta = (direction === "left" || direction === "up") ? -1 : 1
        quickPanelFocusIndex = (quickPanelFocusIndex + delta + count) % count
    }

    function activateQuickPanelFocus() {
        const profileCount = leos.availablePowerProfiles.length
        if (quickPanelFocusIndex === 0) {
            if (leos.mangoHudAvailable)
                leos.setMangoHudEnabled(!leos.mangoHudEnabled)
            else
                statusText.text = "MangoHud n'est pas installé sur cet hôte."
        } else if (quickPanelFocusIndex <= profileCount) {
            pendingPowerProfile = leos.availablePowerProfiles[quickPanelFocusIndex - 1]
            powerProfileDialog.open()
        } else if (quickPanelFocusIndex === profileCount + 1) {
            if (leos.openControllerCenter())
                quickPanel.visible = false
            else
                statusText.text = "Impossible d’ouvrir le Centre des manettes LEOS."
        } else if (quickPanelFocusIndex === profileCount + 2) {
            returnDialog.open()
        } else {
            quickPanel.visible = false
        }
    }

    function handleGamepadAction(action) {
        if (returningToDesktop)
            return
        if (returnDialog.visible) {
            if (action === "confirm") {
                returnDialog.close()
                window.requestDesktopReturn()
            } else if (action === "back") {
                returnDialog.close()
            }
            return
        }
        if (powerProfileDialog.visible) {
            if (action === "confirm") {
                powerProfileDialog.close()
                leos.applyPowerProfile(pendingPowerProfile)
                statusText.text = leos.powerProfileStatus
            } else if (action === "back") {
                powerProfileDialog.close()
            }
            return
        }
        if (addDialog.visible) {
            if (action === "back")
                addDialog.close()
            else if (action === "confirm")
                addDialog.accept()
            return
        }
        if (action === "menu") {
            quickPanel.visible = !quickPanel.visible
            quickPanelFocusIndex = 0
            return
        }
        if (quickPanel.visible) {
            if (action === "back") {
                quickPanel.visible = false
            } else if (action === "up" || action === "down" ||
                       action === "left" || action === "right") {
                moveQuickPanelFocus(action)
            } else if (action === "confirm") {
                activateQuickPanelFocus()
            }
            return
        }
        if (action === "up" || action === "down" ||
                action === "left" || action === "right") {
            navigateDirection(action)
        } else if (action === "confirm") {
            if (navigationArea === "categories") {
                chooseCategory(selectedCategoryIndex)
                if (gameGrid.count > 0)
                    selectGameAt(0)
                gameGrid.forceActiveFocus()
            } else if (navigationArea === "toolbar") {
                activateToolbarFocus()
            } else if (navigationArea === "details") {
                if (detailsActionIndex === 0)
                    toggleSelectedFavorite()
                else
                    launchSelectedGame()
            } else if (selectedIndex >= 0) {
                launchSelectedGame()
            } else {
                moveSelection("right")
            }
        } else if (action === "back") {
            if (navigationArea === "details" || navigationArea === "toolbar") {
                navigationArea = "games"
                gameGrid.forceActiveFocus()
            } else if (navigationArea === "games" && selectedIndex >= 0) {
                clearSelection()
            } else {
                returnDialog.open()
            }
        }
    }

    function metric(value, suffix) {
        return value < 0 ? "—" : Math.round(value) + suffix
    }

    Rectangle {
        id: gamingContent
        anchors.fill: parent
        color: window.color
        focus: true

        Rectangle {
            width: 620; height: 620; radius: 310
            x: parent.width - width * 0.55; y: -height * 0.48
            color: "#102331"; opacity: 0.20
        }
        Rectangle {
            width: 520; height: 520; radius: 260
            x: -width * 0.5; y: parent.height - height * 0.45
            color: "#2a1232"; opacity: 0.15
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 34
            spacing: 22

            RowLayout {
                Layout.fillWidth: true
                spacing: 18

                ColumnLayout {
                    spacing: 1
                    Image {
                        id: gamingHeaderLogo
                        source: leosTheme.gamingLogoUrl
                        asynchronous: true
                        smooth: true
                        fillMode: Image.PreserveAspectFit
                        Layout.preferredWidth: 118
                        Layout.preferredHeight: 58
                        visible: status === Image.Ready
                    }
                    Label {
                        text: "LEOS"
                        color: "white"
                        font.pixelSize: 29
                        font.weight: Font.Black
                        font.letterSpacing: 5
                        visible: gamingHeaderLogo.status !== Image.Ready
                    }
                    Label {
                        text: "GAMING MODE"
                        color: window.cyan
                        font.pixelSize: 10
                        font.letterSpacing: 3
                    }
                }

                Item { Layout.fillWidth: true }

                Label {
                    text: leos.gamepadStatus
                    color: window.muted
                    font.pixelSize: 10
                    elide: Text.ElideRight
                }

                Button {
                    id: notificationCenterButton
                    text: leos.unreadNotificationCount > 0
                          ? "NOTIFICATIONS · " + leos.unreadNotificationCount
                          : "NOTIFICATIONS"
                    onClicked: {
                        if (!leos.openNotificationCentre())
                            statusText.text = "Centre de notifications indisponible."
                    }
                    background: Rectangle {
                        radius: 10
                        color: notificationCenterButton.down ? "#26313e" : "#171d28"
                        border.color: "#344052"
                    }
                    contentItem: Label {
                        text: notificationCenterButton.text
                        color: "white"
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Button {
                    id: notificationSilenceButton
                    text: leos.silentNotificationsInGaming ? "SILENCE ACTIVÉ" : "ALERTES AUTORISÉES"
                    onClicked: leos.toggleSilentNotifications()
                    background: Rectangle {
                        radius: 10
                        color: notificationSilenceButton.down ? "#26313e" : "#171d28"
                        border.color: leos.silentNotificationsInGaming ? window.cyan : "#344052"
                    }
                    contentItem: Label {
                        text: notificationSilenceButton.text
                        color: leos.silentNotificationsInGaming ? window.cyan : "white"
                        font.pixelSize: 10
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Button {
                    id: quickPanelButton
                    text: "PANNEAU RAPIDE  ☰"
                    onClicked: {
                        quickPanel.visible = !quickPanel.visible
                        quickPanelFocusIndex = 0
                    }
                    background: Rectangle {
                        radius: 10
                        color: quickPanelButton.down ? "#26313e" : "#171d28"
                        border.color: "#344052"
                    }
                    contentItem: Label {
                        text: quickPanelButton.text
                        color: "white"
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }

            Rectangle {
                id: quickPanel
                Layout.fillWidth: true
                visible: false
                implicitHeight: 230
                radius: 15
                color: "#ee111722"
                border.color: "#354052"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 22

                    ColumnLayout {
                        Label { text: "PERFORMANCES"; color: window.cyan; font.pixelSize: 10; font.letterSpacing: 2 }
                        Label { text: "CPU  " + window.metric(systemMonitor.cpuUsage, "%"); color: "white"; font.pixelSize: 15 }
                        Label { text: "RAM  " + window.metric(systemMonitor.memoryUsage, "%"); color: "white"; font.pixelSize: 15 }
                        Label { text: "GPU  " + window.metric(systemMonitor.gpuUsage, "%"); color: "white"; font.pixelSize: 15 }
                        Label { text: systemMonitor.gpuName; color: window.muted; font.pixelSize: 9; elide: Text.ElideRight; Layout.maximumWidth: 210 }
                        Label { text: systemMonitor.gpuMemoryTotal > 0 && systemMonitor.gpuMemoryUsed >= 0 ? "VRAM  " + Math.round(systemMonitor.gpuMemoryUsed / 1048576) + " / " + Math.round(systemMonitor.gpuMemoryTotal / 1048576) + " Mo" : "VRAM  —"; color: window.muted; font.pixelSize: 10 }
                    }
                    Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: "#374253" }
                    ColumnLayout {
                        Label { text: "TEMPÉRATURE"; color: window.cyan; font.pixelSize: 10; font.letterSpacing: 2 }
                        Label { text: "CPU  " + window.metric(systemMonitor.cpuTemperature, " °C"); color: "white"; font.pixelSize: 15 }
                        Label { text: "GPU  " + window.metric(systemMonitor.gpuTemperature, " °C"); color: "white"; font.pixelSize: 15 }
                    }
                    Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: "#374253" }
                    ColumnLayout {
                        Label { text: "JEUX"; color: window.cyan; font.pixelSize: 10; font.letterSpacing: 2 }
                        CheckBox {
                            text: "Overlay FPS · MangoHud"
                            checked: leos.mangoHudEnabled
                            enabled: leos.mangoHudAvailable
                            onToggled: leos.setMangoHudEnabled(checked)
                            palette.text: "white"
                            background: Rectangle {
                                radius: 6
                                color: "transparent"
                                border.width: quickPanel.visible && window.quickPanelFocusIndex === 0 ? 2 : 0
                                border.color: window.cyan
                            }
                        }
                        Label {
                            text: leos.mangoHudAvailable
                                  ? "Actif sur les lancements directs compatibles."
                                  : "MangoHud n'est pas installé sur cet hôte."
                            color: window.muted
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                            Layout.maximumWidth: 190
                        }
                        Label {
                            text: "Steam : ajouter « mangohud %command% » aux options de lancement du jeu."
                            color: window.muted
                            font.pixelSize: 9
                            wrapMode: Text.WordWrap
                            Layout.maximumWidth: 190
                        }
                        Repeater {
                            model: leos.launcherStatuses
                            delegate: Label {
                                required property string modelData
                                text: modelData
                                color: modelData.indexOf("DISPONIBLE") >= 0 ? window.cyan : window.muted
                                font.pixelSize: 9
                            }
                        }
                    }
                    ColumnLayout {
                        Layout.preferredWidth: 220
                        spacing: 6
                        Label { text: "PROFIL ÉNERGIE"; color: window.cyan; font.pixelSize: 10; font.letterSpacing: 2 }
                        Label {
                            text: leos.powerProfileStatus
                            color: window.muted
                            font.pixelSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Label {
                            text: leos.activePowerProfile.length > 0
                                  ? "ACTIF · " + window.powerProfileLabel(leos.activePowerProfile)
                                  : "Aucun profil actif identifié"
                            color: "white"
                            font.pixelSize: 10
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Repeater {
                                model: leos.availablePowerProfiles
                                delegate: Button {
                                    id: powerProfileButton
                                    required property string modelData
                                    text: window.powerProfileLabel(modelData)
                                    onClicked: {
                                        window.quickPanelFocusIndex = index + 1
                                        window.pendingPowerProfile = modelData
                                        powerProfileDialog.open()
                                    }
                                    background: Rectangle {
                                        radius: 6
                                        color: leos.activePowerProfile === modelData ? "#123847" : "#202630"
                                        border.width: window.quickPanelFocusIndex === index + 1 ? 2 : 1
                                        border.color: window.quickPanelFocusIndex === index + 1 ? window.cyan : (leos.activePowerProfile === modelData ? window.cyan : "#344052")
                                    }
                                    contentItem: Label {
                                        text: powerProfileButton.text
                                        color: "white"
                                        font.pixelSize: 8
                                        horizontalAlignment: Text.AlignHCenter
                                    }
                                }
                            }
                        }
                    }
                    Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: "#374253" }
                    Item { Layout.fillWidth: true }
                    Button {
                        text: "CONFIGURER MANETTE"
                        onClicked: {
                            if (leos.openControllerCenter())
                                quickPanel.visible = false
                            else
                                statusText.text = "Impossible d’ouvrir le Centre des manettes LEOS."
                        }
                        background: Rectangle {
                            radius: 7
                            color: "#202630"
                            border.width: window.quickPanelFocusIndex === leos.availablePowerProfiles.length + 1 ? 2 : 1
                            border.color: window.quickPanelFocusIndex === leos.availablePowerProfiles.length + 1 ? window.cyan : "#344052"
                        }
                    }
                    Button {
                        text: "RETOUR DESKTOP"
                        onClicked: {
                            window.quickPanelFocusIndex = leos.availablePowerProfiles.length + 2
                            returnDialog.open()
                        }
                        background: Rectangle {
                            radius: 7
                            color: "#202630"
                            border.width: window.quickPanelFocusIndex === leos.availablePowerProfiles.length + 2 ? 2 : 1
                            border.color: window.quickPanelFocusIndex === leos.availablePowerProfiles.length + 2 ? window.cyan : "#344052"
                        }
                    }
                    Button {
                        text: "FERMER"
                        onClicked: quickPanel.visible = false
                        background: Rectangle {
                            radius: 7
                            color: "#202630"
                            border.width: window.quickPanelFocusIndex === leos.availablePowerProfiles.length + 3 ? 2 : 1
                            border.color: window.quickPanelFocusIndex === leos.availablePowerProfiles.length + 3 ? window.cyan : "#344052"
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 26

                ColumnLayout {
                    Layout.preferredWidth: 190
                    Layout.fillHeight: true
                    spacing: 10

                    Label {
                        text: "BIBLIOTHÈQUE"
                        color: window.muted
                        font.pixelSize: 11
                        font.letterSpacing: 2
                    }

                    Repeater {
                        model: window.categoryNames
                        delegate: Button {
                            id: categoryButton
                            required property string modelData
                            Layout.fillWidth: true
                            text: modelData
                            onActiveFocusChanged: {
                                if (activeFocus) {
                                    window.navigationArea = "categories"
                                    window.selectedCategoryIndex = window.categoryNames.indexOf(modelData)
                                }
                            }
                            background: Rectangle {
                                radius: 9
                                color: modelData === window.selectedCategory ? "#202b38" : "transparent"
                                border.width: modelData === window.categoryNames[window.selectedCategoryIndex] && window.navigationArea === "categories" ? 2 : 1
                                border.color: modelData === window.categoryNames[window.selectedCategoryIndex] && window.navigationArea === "categories" ? window.magenta : (modelData === window.selectedCategory ? window.cyan : "transparent")
                            }
                            contentItem: Label {
                                text: categoryButton.text
                                color: "white"
                                leftPadding: 9
                                verticalAlignment: Text.AlignVCenter
                                font.pixelSize: 13
                            }
                            onClicked: {
                                window.chooseCategory(window.categoryNames.indexOf(modelData))
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                    Label {
                        text: "UNE EXPÉRIENCE. DEUX MODES."
                        color: "#626c7e"
                        font.pixelSize: 9
                        wrapMode: Text.WordWrap
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 16

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: window.selectedCategory
                            color: "white"
                            font.pixelSize: 25
                            font.weight: Font.Bold
                        }
                        Label {
                            text: gameGrid.count + (gameGrid.count > 1 ? " JEUX" : " JEU")
                            color: window.muted
                            font.pixelSize: 10
                            font.letterSpacing: 1
                        }
                        Item { Layout.fillWidth: true }
                        TextField {
                            id: searchField
                            Layout.preferredWidth: 270
                            placeholderText: "Rechercher un jeu…"
                            color: "white"
                            selectByMouse: true
                            onActiveFocusChanged: {
                                if (activeFocus) {
                                    window.navigationArea = "toolbar"
                                    window.toolbarFocusIndex = 0
                                }
                            }
                            background: Rectangle {
                                radius: 8
                                color: "#121822"
                                border.width: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 0 ? 2 : 1
                                border.color: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 0 ? window.cyan : "#2a3444"
                            }
                            onTextChanged: {
                                gameLibrary.setSearchQuery(text)
                                window.clearSelection()
                                window.navigationArea = "toolbar"
                                window.toolbarFocusIndex = 0
                            }
                        }
                        Button {
                            id: refreshLibraryButton
                            text: "ACTUALISER"
                            onActiveFocusChanged: {
                                if (activeFocus) {
                                    window.navigationArea = "toolbar"
                                    window.toolbarFocusIndex = 1
                                }
                            }
                            onClicked: {
                                window.clearSelection()
                                leos.refreshLibrary()
                                window.navigationArea = "games"
                                gameGrid.forceActiveFocus()
                            }
                            background: Rectangle {
                                radius: 8
                                color: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 1 ? "#1a2c38" : "#151a24"
                                border.width: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 1 ? 2 : 1
                                border.color: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 1 ? window.cyan : "#2a3444"
                            }
                            contentItem: Label {
                                text: refreshLibraryButton.text
                                color: "white"
                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                        Button {
                            id: addGameButton
                            text: "+ AJOUTER UN JEU"
                            onActiveFocusChanged: {
                                if (activeFocus) {
                                    window.navigationArea = "toolbar"
                                    window.toolbarFocusIndex = 2
                                }
                            }
                            onClicked: {
                                window.navigationArea = "toolbar"
                                window.toolbarFocusIndex = 2
                                addDialog.open()
                            }
                            background: Rectangle {
                                radius: 9
                                color: "#17313d"
                                border.width: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 2 ? 2 : 1
                                border.color: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 2 ? "white" : window.cyan
                            }
                            contentItem: Label {
                                text: addGameButton.text
                                color: "white"
                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 18

                        GridView {
                            id: gameGrid
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            cellWidth: 230
                            cellHeight: 150
                            clip: true
                            model: gameLibrary
                            currentIndex: window.selectedIndex

                            delegate: Button {
                                id: gameCard
                                required property int index
                                required property string title
                                required property string platform
                                required property string source
                                required property bool favorite
                                required property string artwork
                                width: gameGrid.cellWidth - 12
                                height: gameGrid.cellHeight - 12
                                onClicked: window.selectGameAt(index)
                                background: Rectangle {
                                    radius: 13
                                    color: window.selectedIndex === gameCard.index ? "#1a2c38" : "#151a24"
                                    border.width: window.selectedIndex === gameCard.index ? 2 : 1
                                    border.color: window.selectedIndex === gameCard.index ? window.cyan : "#2a3444"
                                    Behavior on color { ColorAnimation { duration: 150 } }
                                    Behavior on border.color { ColorAnimation { duration: 150 } }
                                }
                                contentItem: ColumnLayout {
                                    spacing: 7
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        spacing: 10
                                        Rectangle {
                                            Layout.preferredWidth: 70
                                            Layout.preferredHeight: 100
                                            Layout.alignment: Qt.AlignVCenter
                                            radius: 8
                                            visible: gameCard.artwork.length === 0 || gameArtwork.status !== Image.Ready
                                            clip: true
                                            color: "#101b29"
                                            border.color: "#294455"
                                            Rectangle {
                                                width: parent.width * 1.5
                                                height: parent.width * 1.5
                                                radius: width / 2
                                                x: -parent.width * 0.55
                                                y: parent.height * 0.25
                                                color: "#123b4b"
                                                opacity: 0.55
                                            }
                                            Column {
                                                anchors.centerIn: parent
                                                spacing: 4
                                                Label {
                                                    anchors.horizontalCenter: parent.horizontalCenter
                                                    text: window.gameMonogram(gameCard.title)
                                                    color: "white"
                                                    font.pixelSize: 23
                                                    font.weight: Font.Black
                                                    font.letterSpacing: 1
                                                }
                                                Label {
                                                    anchors.horizontalCenter: parent.horizontalCenter
                                                    text: "LEOS"
                                                    color: window.cyan
                                                    font.pixelSize: 7
                                                    font.letterSpacing: 2
                                                }
                                            }
                                        }
                                        Image {
                                            id: gameArtwork
                                            Layout.preferredWidth: 70
                                            Layout.preferredHeight: 100
                                            Layout.alignment: Qt.AlignVCenter
                                            source: gameCard.artwork
                                            visible: gameCard.artwork.length > 0
                                            fillMode: Image.PreserveAspectCrop
                                            asynchronous: true
                                            cache: true
                                            sourceSize.width: 140
                                            sourceSize.height: 210
                                            opacity: status === Image.Ready ? 1 : 0
                                            Behavior on opacity { NumberAnimation { duration: 180 } }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            spacing: 5
                                            Label {
                                                text: gameCard.title
                                                color: "white"
                                                font.pixelSize: 15
                                                font.weight: Font.DemiBold
                                                wrapMode: Text.WordWrap
                                                Layout.fillWidth: true
                                            }
                                            Label {
                                                text: gameCard.favorite ? "★ FAVORI" : ""
                                                color: window.magenta
                                                font.pixelSize: 9
                                                font.weight: Font.Bold
                                            }
                                        }
                                    }
                                    Label {
                                        text: gameCard.platform + "  •  " + gameCard.source
                                        color: window.muted
                                        font.pixelSize: 10
                                    }
                                }
                            }

                            Label {
                                anchors.centerIn: parent
                                width: parent.width - 50
                                visible: gameGrid.count === 0
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.WordWrap
                                text: searchField.text.length > 0
                                    ? "Aucun résultat pour « " + searchField.text + " »."
                                    : window.selectedCategory === "Favoris"
                                        ? "Aucun favori pour le moment. Sélectionne un jeu et ajoute-le à tes favoris."
                                        : window.selectedCategory === "Récemment joués"
                                            ? "Aucun jeu lancé récemment."
                                            : "Aucun jeu détecté dans cette catégorie.\\n\\nInstalle un jeu dans Steam, Heroic ou Lutris, puis sélectionne ACTUALISER. Tu peux aussi ajouter un jeu manuellement."
                                color: window.muted
                                font.pixelSize: 14
                            }
                        }

                        Rectangle {
                            Layout.preferredWidth: 280
                            Layout.fillHeight: true
                            radius: 16
                            color: "#111720"
                            border.color: "#293342"

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 20
                                spacing: 12

                                Label {
                                    text: "JEU SÉLECTIONNÉ"
                                    color: window.cyan
                                    font.pixelSize: 10
                                    font.letterSpacing: 2
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 172
                                    radius: 11
                                    clip: true
                                    color: "#0b1018"
                                    border.color: "#293849"
                                    Image {
                                        id: selectedGameArtwork
                                        anchors.fill: parent
                                        source: window.selectedArtwork
                                        visible: window.selectedArtwork.length > 0
                                        fillMode: Image.PreserveAspectCrop
                                        asynchronous: true
                                        cache: true
                                        sourceSize.width: 560
                                        sourceSize.height: 344
                                        opacity: status === Image.Ready ? 1 : 0
                                        Behavior on opacity { NumberAnimation { duration: 220 } }
                                        onStatusChanged: window.selectedArtworkFailed = status === Image.Error
                                    }
                                    Column {
                                        anchors.centerIn: parent
                                        spacing: 6
                                        visible: window.selectedArtwork.length === 0 || window.selectedArtworkFailed || selectedGameArtwork.status !== Image.Ready
                                        Label {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            text: "LEOS"
                                            color: "#617184"
                                            font.pixelSize: 25
                                            font.weight: Font.Black
                                            font.letterSpacing: 5
                                        }
                                        Label {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            text: window.selectedTitle ? "ARTWORK NON DISPONIBLE" : "SÉLECTIONNE UN JEU"
                                            color: window.muted
                                            font.pixelSize: 9
                                            font.letterSpacing: 1
                                        }
                                    }
                                }
                                Label {
                                    text: window.selectedTitle || "Choisis un jeu"
                                    color: "white"
                                    font.pixelSize: 22
                                    font.weight: Font.Bold
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }
                                Label {
                                    text: window.selectedTitle ? window.selectedPlatform + " • " + window.selectedSource : "Les détails apparaîtront ici."
                                    color: window.muted
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    implicitHeight: 1
                                    color: "#293849"
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    Label {
                                        text: "STATUT"
                                        color: window.muted
                                        font.pixelSize: 9
                                        font.letterSpacing: 1
                                    }
                                    Item { Layout.fillWidth: true }
                                    Label {
                                        text: window.selectedInstallStatus || "—"
                                        color: window.selectedInstallStatus === "Installé" ? window.cyan :
                                               window.selectedInstallStatus === "Fichiers absents" ? window.magenta : "white"
                                        font.pixelSize: 10
                                        font.weight: Font.DemiBold
                                    }
                                }
                                Label {
                                    Layout.fillWidth: true
                                    visible: window.selectedAppId.length > 0
                                    text: "IDENTIFIANT  ·  " + window.selectedAppId
                                    color: "#697789"
                                    font.pixelSize: 9
                                    elide: Text.ElideMiddle
                                }
                                Label {
                                    Layout.fillWidth: true
                                    visible: window.selectedDuplicateCount > 1
                                    text: "DOUBLON POTENTIEL · " + window.selectedDuplicateCount + " entrées (" + window.selectedDuplicateSources + ")"
                                    color: "#d5a45d"
                                    font.pixelSize: 9
                                    wrapMode: Text.WordWrap
                                }
                                Item { Layout.fillHeight: true }
                                Button {
                                    id: favoriteGameButton
                                    Layout.fillWidth: true
                                    enabled: window.selectedIndex >= 0
                                    text: window.selectedIsFavorite ? "RETIRER DES FAVORIS" : "AJOUTER AUX FAVORIS"
                                    onActiveFocusChanged: {
                                        if (activeFocus) {
                                            window.navigationArea = "details"
                                            window.detailsActionIndex = 0
                                        }
                                    }
                                    onClicked: window.toggleSelectedFavorite()
                                    background: Rectangle {
                                        radius: 9
                                        color: "#191d2a"
                                        border.width: window.navigationArea === "details" && window.detailsActionIndex === 0 ? 2 : 1
                                        border.color: window.navigationArea === "details" && window.detailsActionIndex === 0 ? "white" : window.magenta
                                    }
                                    contentItem: Label {
                                        text: favoriteGameButton.text
                                        color: "white"
                                        font.pixelSize: 11
                                        font.weight: Font.DemiBold
                                        horizontalAlignment: Text.AlignHCenter
                                    }
                                }
                                Button {
                                    id: launchSelectedGameButton
                                    Layout.fillWidth: true
                                    enabled: window.selectedIndex >= 0
                                    text: "JOUER"
                                    onActiveFocusChanged: {
                                        if (activeFocus) {
                                            window.navigationArea = "details"
                                            window.detailsActionIndex = 1
                                        }
                                    }
                                    onClicked: window.launchSelectedGame()
                                    background: Rectangle {
                                        radius: 10
                                        color: launchSelectedGameButton.enabled ? "#103847" : "#202630"
                                        border.width: window.navigationArea === "details" && window.detailsActionIndex === 1 ? 2 : 1
                                        border.color: window.navigationArea === "details" && window.detailsActionIndex === 1 ? "white" : launchSelectedGameButton.enabled ? window.cyan : "#344052"
                                    }
                                    contentItem: Label {
                                        text: launchSelectedGameButton.text
                                        color: launchSelectedGameButton.enabled ? "white" : "#778091"
                                        font.pixelSize: 13
                                        font.weight: Font.Bold
                                        horizontalAlignment: Text.AlignHCenter
                                    }
                                }
                                Label {
                                    id: statusText
                                    Layout.fillWidth: true
                                    color: window.muted
                                    font.pixelSize: 10
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }
                }
            }
        }
        Keys.onPressed: function(event) {
            if (window.returningToDesktop) {
                event.accepted = true
                return
            }
            if (event.key === Qt.Key_Left) {
                window.navigateDirection("left")
                event.accepted = true
            } else if (event.key === Qt.Key_Right) {
                window.navigateDirection("right")
                event.accepted = true
            } else if (event.key === Qt.Key_Up) {
                window.navigateDirection("up")
                event.accepted = true
            } else if (event.key === Qt.Key_Down) {
                window.navigateDirection("down")
                event.accepted = true
            } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter ||
                       event.key === Qt.Key_Space) {
                window.handleGamepadAction("confirm")
                event.accepted = true
            } else if (event.key === Qt.Key_F1) {
                window.handleGamepadAction("menu")
                event.accepted = true
            } else if (event.key === Qt.Key_F2) {
                addDialog.open()
                event.accepted = true
            } else if (event.key === Qt.Key_Escape || event.key === Qt.Key_Backspace) {
                window.handleGamepadAction("back")
                event.accepted = true
            }
        }
    }


    MediaPlayer {
        id: desktopIntroPlayer
        audioOutput: AudioOutput {
            id: desktopIntroAudio
            muted: true
        }
        videoOutput: desktopIntroVideoOutput
        onMediaStatusChanged: {
            if (mediaStatus === MediaPlayer.EndOfMedia ||
                    mediaStatus === MediaPlayer.InvalidMedia)
                window.finishDesktopReturn()
        }
        onErrorOccurred: function(error, errorString) {
            window.finishDesktopReturn()
        }
    }

    Timer {
        id: desktopIntroTimeout
        interval: 9000
        repeat: false
        onTriggered: window.finishDesktopReturn()
    }

    Rectangle {
        id: desktopIntroOverlay
        anchors.fill: parent
        color: "#000000"
        visible: false
        z: 1000
        VideoOutput {
            id: desktopIntroVideoOutput
            anchors.fill: parent
            fillMode: VideoOutput.PreserveAspectFit
        }
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
        }
    }

    Dialog {
        id: returnDialog
        title: "Retourner à Desktop Mode ?"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Cancel
        width: 430
        ColumnLayout {
            width: parent.width
            spacing: 14
            Label {
                text: "Gaming va se fermer et le bureau KDE réapparaître. Les applications déjà ouvertes resteront en arrière-plan ; aucune ne sera fermée automatiquement."
                color: "white"
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Button {
                id: returnToDesktopButton
                text: "CONFIRMER LE RETOUR AU DESKTOP"
                Layout.fillWidth: true
                onClicked: {
                    returnDialog.close()
                    window.requestDesktopReturn()
                }
                background: Rectangle { radius: 9; color: "#17313d"; border.color: window.cyan }
                contentItem: Label {
                    text: returnToDesktopButton.text
                    color: "white"
                    font.weight: Font.Bold
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }


    Dialog {
        id: powerProfileDialog
        title: "Confirmer le profil d’énergie"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Cancel
        width: 440
        ColumnLayout {
            width: parent.width
            spacing: 12
            Label {
                text: "LEOS va demander au service natif de gestion d’énergie de passer sur « " +
                      window.powerProfileLabel(window.pendingPowerProfile) + " ». Ce réglage peut modifier la consommation et les performances selon le matériel. Il ne contrôle pas directement les ventilateurs."
                color: "white"
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Button {
                id: confirmPowerProfileButton
                text: "CONFIRMER LE CHANGEMENT"
                Layout.fillWidth: true
                onClicked: {
                    powerProfileDialog.close()
                    leos.applyPowerProfile(window.pendingPowerProfile)
                    statusText.text = leos.powerProfileStatus
                }
                background: Rectangle { radius: 9; color: "#17313d"; border.color: window.cyan }
                contentItem: Label {
                    text: confirmPowerProfileButton.text
                    color: "white"
                    font.weight: Font.Bold
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }

    Dialog {
        id: addDialog
        title: "Ajouter un jeu à LEOS"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        width: 440

        ColumnLayout {
            width: parent.width
            spacing: 12
            Label { text: "Nom du jeu"; color: "white" }
            TextField {
                id: gameName
                Layout.fillWidth: true
                placeholderText: "Ex. : Mon jeu"
                maximumLength: 256
            }
            Label { text: "Plateforme"; color: "white" }
            ComboBox {
                id: gamePlatform
                Layout.fillWidth: true
                model: ["PC", "Nintendo", "PlayStation", "SEGA", "Arcade", "Autre"]
            }
            Label { text: "Commande de lancement"; color: "white" }
            TextField {
                id: launchCommand
                Layout.fillWidth: true
                placeholderText: "Ex. : steam steam://rungameid/123456"
                maximumLength: 8192
            }
            Label {
                text: "La commande est enregistrée dans ton profil et exécutée sans passer par un shell."
                color: window.muted
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                font.pixelSize: 10
            }
        }

        onAccepted: {
            if (leos.addGame(gameName.text, gamePlatform.currentText, launchCommand.text)) {
                gameName.clear()
                launchCommand.clear()
                statusText.text = "Jeu ajouté. Sélectionne-le dans la bibliothèque."
            } else {
                statusText.text = "Impossible d'ajouter ce jeu. Vérifie les champs."
            }
        }
        onRejected: {
            gameName.clear()
            launchCommand.clear()
        }
    }

    Connections {
        target: leos
        function onMessageChanged(message) {
            statusText.text = message
        }
        function onGamepadAction(action) {
            window.handleGamepadAction(action)
        }
    }

}
