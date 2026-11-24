import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtMultimedia
import "../../branding/qml" as Branding

ApplicationWindow {
    id: window
    width: 1440
    height: 900
    visible: true
    visibility: Window.FullScreen
    title: "LEOS Gaming"
    property var themeColors: leosTheme.themePalette
    color: themeColors.background

    property color cyan: themeColors.accent_primary_text
    property color magenta: themeColors.accent_secondary_text
    property color accentA: themeColors.accent_primary
    property color accentB: themeColors.accent_secondary
    property color muted: themeColors.muted_text
    property color focusColor: themeColors.text
    property int fontMicro: 14
    property int fontCaption: 15
    property int fontBody: 17
    property int fontTitle: 26
    property int fontDisplay: 30
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

    function powerProfileShortLabel(profile) {
        if (profile === "performance") return "PERF."
        if (profile === "balanced") return "ÉQUIL."
        if (profile === "power-saver") return "ÉCO"
        return String(profile || "").toUpperCase()
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
        toolbarFocusIndex = Math.max(0, Math.min(4, index))
        navigationArea = "toolbar"
        if (toolbarFocusIndex === 0)
            searchField.forceActiveFocus()
        else if (toolbarFocusIndex === 1)
            refreshLibraryButton.forceActiveFocus()
        else if (toolbarFocusIndex === 2)
            importEmulatorFolderButton.forceActiveFocus()
        else if (toolbarFocusIndex === 3)
            emulatorPrerequisitesButton.forceActiveFocus()
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
        } else if (toolbarFocusIndex === 2) {
            emulatorImportDialog.open()
        } else if (toolbarFocusIndex === 3) {
            emulatorPrerequisitesDialog.open()
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

    function focusEmulatorPrerequisiteAction() {
        if (emulatorPrerequisitesDialog.controllerFocusIndex === 0)
            edenOpenSetupButton.forceActiveFocus()
        else if (emulatorPrerequisitesDialog.controllerFocusIndex === 1)
            retroArchOpenCoreUpdaterButton.forceActiveFocus()
        else if (emulatorPrerequisitesDialog.controllerFocusIndex === 2)
            retroArchRefreshCoreStatusButton.forceActiveFocus()
        else
            retroArchCloseDialogButton.forceActiveFocus()
    }

    function activateEmulatorPrerequisiteAction() {
        if (emulatorPrerequisitesDialog.controllerFocusIndex === 0)
            leos.openEdenSetup()
        else if (emulatorPrerequisitesDialog.controllerFocusIndex === 1)
            leos.openRetroArchCoreUpdater()
        else if (emulatorPrerequisitesDialog.controllerFocusIndex === 2)
            leos.refreshRetroArchCoreStatuses()
        else
            emulatorPrerequisitesDialog.close()
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
        if (emulatorPrerequisitesDialog.visible) {
            if (action === "back") {
                emulatorPrerequisitesDialog.close()
            } else if (action === "left" || action === "up") {
                emulatorPrerequisitesDialog.controllerFocusIndex =
                        (emulatorPrerequisitesDialog.controllerFocusIndex + 3) % 4
                focusEmulatorPrerequisiteAction()
            } else if (action === "right" || action === "down") {
                emulatorPrerequisitesDialog.controllerFocusIndex =
                        (emulatorPrerequisitesDialog.controllerFocusIndex + 1) % 4
                focusEmulatorPrerequisiteAction()
            } else if (action === "confirm") {
                activateEmulatorPrerequisiteAction()
            }
            return
        }
        if (emulatorSourcesDialog.visible) {
            if (action === "back") {
                emulatorSourcesDialog.close()
            } else if (action === "up" || action === "down") {
                const count = leos.emulatorSourceFolders.length
                if (count > 0) {
                    const step = action === "up" ? -1 : 1
                    emulatorSourcesList.currentIndex = Math.max(
                        0, Math.min(count - 1, emulatorSourcesList.currentIndex + step))
                    if (emulatorSourcesList.currentItem)
                        emulatorSourcesList.currentItem.forceActiveFocus()
                }
            } else if (action === "confirm") {
                const index = emulatorSourcesList.currentIndex
                const count = leos.emulatorSourceFolders.length
                if (index >= 0 && index < count) {
                    const source = leos.emulatorSourceFolders[index]
                    if (leos.removeEmulatorFolder(source.platform, source.path)) {
                        const nextCount = leos.emulatorSourceFolders.length
                        emulatorSourcesList.currentIndex = nextCount > 0
                            ? Math.min(index, nextCount - 1) : -1
                        if (emulatorSourcesList.currentItem)
                            emulatorSourcesList.currentItem.forceActiveFocus()
                    }
                }
            }
            return
        }
        if (emulatorImportDialog.visible) {
            if (action === "back") {
                emulatorImportDialog.close()
            } else if (action === "up" || action === "down") {
                const step = action === "up" ? -1 : 1
                emulatorImportDialog.controllerFocusIndex = Math.max(
                    0, Math.min(2, emulatorImportDialog.controllerFocusIndex + step))
                if (emulatorImportDialog.controllerFocusIndex === 0)
                    emulatorPlatformCombo.forceActiveFocus()
                else if (emulatorImportDialog.controllerFocusIndex === 1)
                    emulatorChooseFolderButton.forceActiveFocus()
                else
                    emulatorManageSourcesButton.forceActiveFocus()
            } else if (action === "left" || action === "right") {
                if (emulatorImportDialog.controllerFocusIndex === 0) {
                    const step = action === "left" ? -1 : 1
                    const count = emulatorPlatformCombo.count
                    emulatorPlatformCombo.currentIndex = (
                        emulatorPlatformCombo.currentIndex + step + count
                    ) % count
                }
            } else if (action === "confirm") {
                if (emulatorImportDialog.controllerFocusIndex === 0) {
                    emulatorImportDialog.controllerFocusIndex = 1
                    emulatorChooseFolderButton.forceActiveFocus()
                } else if (emulatorImportDialog.controllerFocusIndex === 1) {
                    const platformKeys = ["gamecube_wii", "ps2", "psp", "melonds", "eden", "rpcs3"]
                    if (leos.beginEmulatorFolderBrowse(
                                platformKeys[emulatorPlatformCombo.currentIndex])) {
                        emulatorImportDialog.close()
                        emulatorFolderDialog.open()
                    }
                } else {
                    emulatorSourcesDialog.open()
                }
            }
            return
        }
        if (emulatorFolderDialog.visible) {
            const directoryCount = leos.emulatorFolderDirectories.length
            if (action === "back") {
                emulatorFolderDialog.close()
            } else if (action === "left") {
                leos.browseEmulatorFolderParent()
                folderDirectoryList.currentIndex = directoryCount > 0 ? 0 : -1
                if (folderDirectoryList.currentItem)
                    folderDirectoryList.currentItem.forceActiveFocus()
            } else if (action === "up" || action === "down") {
                if (directoryCount > 0) {
                    const step = action === "up" ? -1 : 1
                    folderDirectoryList.currentIndex = Math.max(
                        0, Math.min(directoryCount - 1,
                                    folderDirectoryList.currentIndex + step))
                    folderDirectoryList.positionViewAtIndex(
                        folderDirectoryList.currentIndex, ListView.Contain)
                    if (folderDirectoryList.currentItem)
                        folderDirectoryList.currentItem.forceActiveFocus()
                }
            } else if (action === "confirm" || action === "right") {
                if (folderDirectoryList.currentIndex >= 0 &&
                    folderDirectoryList.currentIndex < directoryCount) {
                    const folderName = leos.emulatorFolderDirectories[
                        folderDirectoryList.currentIndex]
                    if (leos.enterEmulatorFolder(folderName)) {
                        folderDirectoryList.currentIndex =
                            leos.emulatorFolderDirectories.length > 0 ? 0 : -1
                        if (folderDirectoryList.currentItem)
                            folderDirectoryList.currentItem.forceActiveFocus()
                    }
                }
            } else if (action === "menu") {
                if (leos.useCurrentEmulatorFolder()) {
                    emulatorFolderDialog.close()
                    window.clearSelection()
                    window.navigationArea = "games"
                    gameGrid.forceActiveFocus()
                }
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
            } else if (gameGrid.count === 0) {
                window.activateEmptyStatePrimaryAction()
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

    function emptyStatePrimaryLabel() {
        if (searchField.text.length > 0)
            return "EFFACER LA RECHERCHE"
        if (selectedCategory === "Favoris" || selectedCategory === "Récemment joués")
            return "VOIR TOUS LES JEUX"
        return "ACTUALISER LA BIBLIOTHÈQUE"
    }

    function activateEmptyStatePrimaryAction() {
        if (searchField.text.length > 0) {
            searchField.clear()
            statusText.text = "Recherche effacée."
        } else if (selectedCategory === "Favoris" || selectedCategory === "Récemment joués") {
            chooseCategory(0)
            statusText.text = "Affichage de toute la bibliothèque."
        } else {
            clearSelection()
            leos.refreshLibrary()
            statusText.text = "Actualisation de la bibliothèque demandée."
            navigationArea = "games"
            gameGrid.forceActiveFocus()
        }
    }

    Rectangle {
        id: gamingContent
        anchors.fill: parent
        color: window.color
        focus: true

        Branding.ParticleBackdrop {
            anchors.fill: parent
            z: 0
            colorA: window.accentA
            colorB: window.accentB
            particleOpacity: 0.78
            motionEnabled: leos.animationsEnabled
        }

        Rectangle {
            width: 620; height: 620; radius: 310
            x: parent.width - width * 0.55; y: -height * 0.48
            color: window.accentA; opacity: 0.085
        }
        Rectangle {
            width: 520; height: 520; radius: 260
            x: -width * 0.5; y: parent.height - height * 0.45
            color: window.accentB; opacity: 0.07
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: window.width < 1280 || window.height < 760 ? 20 : 34
            spacing: window.height < 760 ? 15 : 22

            RowLayout {
                Layout.fillWidth: true
                spacing: window.width < 1180 ? 7 : window.width < 1360 ? 10 : 18

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
                        color: window.themeColors.text
                        font.pixelSize: window.fontDisplay
                        font.weight: Font.Black
                        font.letterSpacing: 5
                        visible: gamingHeaderLogo.status !== Image.Ready
                    }
                    RowLayout {
                        spacing: 12
                        Label {
                            text: "GAMING MODE"
                            color: window.cyan
                            font.pixelSize: window.fontCaption
                            font.letterSpacing: 3
                        }
                        Button {
                            id: returnDesktopHeaderButton
                            text: "RETOUR DESKTOP"
                            Accessible.name: "Retourner à LEOS Desktop"
                            Accessible.description: "Quitter Gaming et revenir au bureau KDE."
                            Layout.preferredWidth: 148
                            Layout.preferredHeight: 32
                            onClicked: returnDialog.open()
                            background: Rectangle {
                                radius: 8
                                color: returnDesktopHeaderButton.down || returnDesktopHeaderButton.hovered
                                       || returnDesktopHeaderButton.activeFocus
                                       ? window.themeColors.surface_elevated : window.themeColors.surface
                                border.width: returnDesktopHeaderButton.activeFocus ? 2 : 1
                                border.color: returnDesktopHeaderButton.activeFocus ? window.focusColor
                                              : returnDesktopHeaderButton.hovered ? window.accentA
                                              : window.themeColors.border
                            }
                            contentItem: Label {
                                text: returnDesktopHeaderButton.text
                                color: window.themeColors.text
                                font.pixelSize: 10
                                font.weight: Font.Bold
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }
                }

                Item { Layout.fillWidth: true }

                Rectangle {
                    Layout.preferredWidth: window.width < 1180 ? 150 : window.width < 1360 ? 190 : 250
                    Layout.minimumWidth: 130
                    Layout.maximumWidth: 250
                    Layout.preferredHeight: 40
                    radius: 10
                    color: window.themeColors.surface
                    border.color: window.themeColors.border
                    Accessible.role: Accessible.Grouping
                    Accessible.name: "État des manettes"
                    Accessible.description: leos.gamepadStatus

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        spacing: 8
                        Rectangle {
                            Layout.preferredWidth: 3
                            Layout.preferredHeight: 18
                            radius: 2
                            gradient: Gradient {
                                GradientStop { position: 0; color: window.accentA }
                                GradientStop { position: 1; color: window.accentB }
                            }
                        }
                        Label {
                            text: leos.gamepadStatus
                            color: window.muted
                            font.pixelSize: window.fontCaption
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }
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
                        color: notificationCenterButton.down || notificationCenterButton.hovered || notificationCenterButton.activeFocus
                               ? window.themeColors.surface_elevated : window.themeColors.surface
                        border.width: notificationCenterButton.activeFocus ? 2 : 1
                        border.color: notificationCenterButton.activeFocus ? window.focusColor
                                      : notificationCenterButton.hovered ? window.accentB : window.themeColors.border
                    }
                    contentItem: Label {
                        text: notificationCenterButton.text
                        color: window.themeColors.text
                        font.pixelSize: window.fontCaption
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
                        color: notificationSilenceButton.down || notificationSilenceButton.hovered || notificationSilenceButton.activeFocus
                               ? window.themeColors.surface_elevated : window.themeColors.surface
                        border.width: notificationSilenceButton.activeFocus ? 2 : 1
                        border.color: notificationSilenceButton.activeFocus ? window.focusColor
                                      : leos.silentNotificationsInGaming ? window.accentA
                                      : notificationSilenceButton.hovered ? window.accentB : window.themeColors.border
                    }
                    contentItem: Label {
                        text: notificationSilenceButton.text
                        color: leos.silentNotificationsInGaming ? window.cyan : window.themeColors.text
                        font.pixelSize: window.fontCaption
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
                        color: quickPanelButton.down || quickPanelButton.hovered || quickPanelButton.activeFocus || quickPanel.visible
                               ? window.themeColors.surface_elevated : window.themeColors.surface
                        border.width: quickPanelButton.activeFocus ? 2 : 1
                        border.color: quickPanelButton.activeFocus ? window.focusColor
                                      : quickPanel.visible ? window.accentA
                                      : quickPanelButton.hovered ? window.accentB : window.themeColors.border
                    }
                    contentItem: Label {
                        text: quickPanelButton.text
                        color: window.themeColors.text
                        font.pixelSize: window.fontBody
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
                implicitHeight: window.height < 760 ? 214 : 230
                radius: 15
                color: window.themeColors.surface_elevated
                border.color: window.themeColors.border
                Accessible.role: Accessible.Grouping
                Accessible.name: "Panneau rapide Gaming"
                Accessible.description: "Statistiques, réglages de jeu, profils d’énergie et accès aux commandes de session."

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: window.width < 1180 ? 12 : 18
                    spacing: window.width < 1180 ? 12 : 22

                    ColumnLayout {
                        Label { text: "PERFORMANCES"; color: window.cyan; font.pixelSize: window.fontCaption; font.letterSpacing: 2 }
                        Label {
                            text: "CPU  " + window.metric(systemMonitor.cpuUsage, "%")
                            color: window.themeColors.text
                            font.pixelSize: window.fontBody
                            Accessible.name: "Utilisation processeur : " + text
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 4
                            radius: 2
                            visible: systemMonitor.cpuUsage >= 0
                            color: window.themeColors.background
                            Rectangle {
                                width: parent.width * Math.max(0, Math.min(100, systemMonitor.cpuUsage)) / 100
                                height: parent.height
                                radius: 2
                                gradient: Gradient {
                                    GradientStop { position: 0; color: window.accentA }
                                    GradientStop { position: 1; color: window.accentB }
                                }
                            }
                        }
                        Label {
                            text: "RAM  " + window.metric(systemMonitor.memoryUsage, "%")
                            color: window.themeColors.text
                            font.pixelSize: window.fontBody
                            Accessible.name: "Utilisation mémoire : " + text
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 4
                            radius: 2
                            visible: systemMonitor.memoryUsage >= 0
                            color: window.themeColors.background
                            Rectangle {
                                width: parent.width * Math.max(0, Math.min(100, systemMonitor.memoryUsage)) / 100
                                height: parent.height
                                radius: 2
                                gradient: Gradient {
                                    GradientStop { position: 0; color: window.accentA }
                                    GradientStop { position: 1; color: window.accentB }
                                }
                            }
                        }
                        Label {
                            text: "GPU  " + window.metric(systemMonitor.gpuUsage, "%")
                            color: window.themeColors.text
                            font.pixelSize: window.fontBody
                            Accessible.name: "Utilisation graphique : " + text
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 4
                            radius: 2
                            visible: systemMonitor.gpuUsage >= 0
                            color: window.themeColors.background
                            Rectangle {
                                width: parent.width * Math.max(0, Math.min(100, systemMonitor.gpuUsage)) / 100
                                height: parent.height
                                radius: 2
                                gradient: Gradient {
                                    GradientStop { position: 0; color: window.accentA }
                                    GradientStop { position: 1; color: window.accentB }
                                }
                            }
                        }
                        Label { text: systemMonitor.gpuName; color: window.muted; font.pixelSize: window.fontMicro; elide: Text.ElideRight; Layout.maximumWidth: 210 }
                        Label { text: systemMonitor.gpuMemoryTotal > 0 && systemMonitor.gpuMemoryUsed >= 0 ? "VRAM  " + Math.round(systemMonitor.gpuMemoryUsed / 1048576) + " / " + Math.round(systemMonitor.gpuMemoryTotal / 1048576) + " Mo" : "VRAM  —"; color: window.muted; font.pixelSize: window.fontCaption }
                    }
                    Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: window.themeColors.border }
                    ColumnLayout {
                        Label { text: "TEMPÉRATURE"; color: window.cyan; font.pixelSize: window.fontCaption; font.letterSpacing: 2 }
                        Label { text: "CPU  " + window.metric(systemMonitor.cpuTemperature, " °C"); color: window.themeColors.text; font.pixelSize: window.fontBody }
                        Label { text: "GPU  " + window.metric(systemMonitor.gpuTemperature, " °C"); color: window.themeColors.text; font.pixelSize: window.fontBody }
                    }
                    Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: window.themeColors.border }
                    ColumnLayout {
                        Label { text: "JEUX"; color: window.cyan; font.pixelSize: window.fontCaption; font.letterSpacing: 2 }
                        CheckBox {
                            text: "Overlay FPS · MangoHud"
                            checked: leos.mangoHudEnabled
                            enabled: leos.mangoHudAvailable
                            onToggled: leos.setMangoHudEnabled(checked)
                            palette.text: window.themeColors.text
                            background: Rectangle {
                                radius: 6
                                color: "transparent"
                                border.width: quickPanel.visible && window.quickPanelFocusIndex === 0 ? 2 : 0
                                border.color: window.focusColor
                            }
                        }
                        Label {
                            text: leos.mangoHudAvailable
                                  ? "Actif sur les lancements directs compatibles."
                                  : "MangoHud n'est pas installé sur cet hôte."
                            color: window.muted
                            font.pixelSize: window.fontCaption
                            wrapMode: Text.WordWrap
                            Layout.maximumWidth: 190
                        }
                        Label {
                            text: "Steam : ajouter « mangohud %command% » aux options de lancement du jeu."
                            color: window.muted
                            font.pixelSize: window.fontMicro
                            wrapMode: Text.WordWrap
                            Layout.maximumWidth: 190
                        }
                        Repeater {
                            model: leos.launcherStatuses
                            delegate: Label {
                                required property string modelData
                                text: modelData
                                color: modelData.indexOf("DISPONIBLE") >= 0 ? window.cyan : window.muted
                                font.pixelSize: window.fontMicro
                            }
                        }
                    }
                    ColumnLayout {
                        Layout.preferredWidth: 220
                        spacing: 6
                        Label { text: "PROFIL ÉNERGIE"; color: window.cyan; font.pixelSize: window.fontCaption; font.letterSpacing: 2 }
                        Label {
                            text: leos.powerProfileStatus
                            color: window.muted
                            font.pixelSize: window.fontMicro
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Label {
                            text: leos.activePowerProfile.length > 0
                                  ? "ACTIF · " + window.powerProfileLabel(leos.activePowerProfile)
                                  : "Aucun profil actif identifié"
                            color: window.themeColors.text
                            font.pixelSize: window.fontCaption
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Repeater {
                                model: leos.availablePowerProfiles
                                delegate: Button {
                                    id: powerProfileButton
                                    required property string modelData
                                    text: window.powerProfileShortLabel(modelData)
                                    Accessible.role: Accessible.Button
                                    Accessible.name: window.powerProfileLabel(modelData)
                                    Accessible.description: "Appliquer ce profil après confirmation."
                                    onClicked: {
                                        window.quickPanelFocusIndex = index + 1
                                        window.pendingPowerProfile = modelData
                                        powerProfileDialog.open()
                                    }
                                    background: Rectangle {
                                        radius: 6
                                        color: leos.activePowerProfile === modelData ? window.themeColors.surface_elevated : window.themeColors.surface
                                        border.width: window.quickPanelFocusIndex === index + 1 ? 2 : 1
                                        border.color: window.quickPanelFocusIndex === index + 1 ? window.focusColor : (leos.activePowerProfile === modelData ? window.accentA : window.themeColors.border)
                                    }
                                    contentItem: Label {
                                        text: powerProfileButton.text
                                        color: window.themeColors.text
                                        font.pixelSize: window.fontMicro
                                        horizontalAlignment: Text.AlignHCenter
                                    }
                                }
                            }
                        }
                    }
                    Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: window.themeColors.border }
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
                            color: window.themeColors.surface
                            border.width: window.quickPanelFocusIndex === leos.availablePowerProfiles.length + 1 ? 2 : 1
                            border.color: window.quickPanelFocusIndex === leos.availablePowerProfiles.length + 1 ? window.focusColor : window.themeColors.border
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
                            color: window.themeColors.surface
                            border.width: window.quickPanelFocusIndex === leos.availablePowerProfiles.length + 2 ? 2 : 1
                            border.color: window.quickPanelFocusIndex === leos.availablePowerProfiles.length + 2 ? window.focusColor : window.themeColors.border
                        }
                    }
                    Button {
                        text: "FERMER"
                        onClicked: quickPanel.visible = false
                        background: Rectangle {
                            radius: 7
                            color: window.themeColors.surface
                            border.width: window.quickPanelFocusIndex === leos.availablePowerProfiles.length + 3 ? 2 : 1
                            border.color: window.quickPanelFocusIndex === leos.availablePowerProfiles.length + 3 ? window.focusColor : window.themeColors.border
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: window.width < 1180 ? 12 : 26

                ColumnLayout {
                    Layout.preferredWidth: window.width < 1180 ? 150 : 190
                    Layout.minimumWidth: 140
                    Layout.fillHeight: true
                    spacing: 10

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 5
                        Label {
                            text: "BIBLIOTHÈQUE"
                            color: window.themeColors.text
                            font.pixelSize: window.fontCaption
                            font.weight: Font.Bold
                            font.letterSpacing: 2
                        }
                        Label {
                            text: "TA COLLECTION"
                            color: window.muted
                            font.pixelSize: window.fontMicro
                            font.letterSpacing: 1.5
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 2
                            radius: 1
                            gradient: Gradient {
                                GradientStop { position: 0; color: window.accentA }
                                GradientStop { position: 1; color: window.accentB }
                            }
                            opacity: 0.62
                        }
                    }

                    Repeater {
                        model: window.categoryNames
                        delegate: Button {
                            id: categoryButton
                            required property string modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 43
                            text: modelData
                            Accessible.role: Accessible.Button
                            Accessible.name: categoryButton.text
                            Accessible.description: "Afficher la catégorie " + categoryButton.text
                            onActiveFocusChanged: {
                                if (activeFocus) {
                                    window.navigationArea = "categories"
                                    window.selectedCategoryIndex = window.categoryNames.indexOf(modelData)
                                }
                            }
                            background: Rectangle {
                                radius: 9
                                color: modelData === window.selectedCategory || categoryButton.hovered
                                       ? window.themeColors.surface_elevated : "transparent"
                                border.width: modelData === window.categoryNames[window.selectedCategoryIndex] && window.navigationArea === "categories" ? 2 : 1
                                border.color: modelData === window.categoryNames[window.selectedCategoryIndex] && window.navigationArea === "categories"
                                              ? window.focusColor
                                              : modelData === window.selectedCategory ? window.accentA
                                              : categoryButton.hovered ? window.accentB : "transparent"

                                Rectangle {
                                    anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                                    anchors.leftMargin: 1
                                    width: 3
                                    radius: 2
                                    visible: modelData === window.selectedCategory
                                    gradient: Gradient {
                                        GradientStop { position: 0; color: window.accentA }
                                        GradientStop { position: 1; color: window.accentB }
                                    }
                                }
                            }
                            contentItem: Label {
                                text: categoryButton.text
                                color: window.themeColors.text
                                leftPadding: 9
                                verticalAlignment: Text.AlignVCenter
                                font.pixelSize: window.fontBody
                            }
                            onClicked: {
                                window.chooseCategory(window.categoryNames.indexOf(modelData))
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                    Label {
                        text: "UNE EXPÉRIENCE. DEUX MODES."
                        color: window.themeColors.muted_text
                        font.pixelSize: window.fontMicro
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
                            color: window.themeColors.text
                            font.pixelSize: window.fontTitle
                            font.weight: Font.Bold
                        }
                        Rectangle {
                            Layout.preferredHeight: 30
                            implicitWidth: 92
                            radius: 9
                            color: window.themeColors.surface
                            border.color: window.themeColors.border
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                spacing: 6
                                Rectangle {
                                    Layout.preferredWidth: 5
                                    Layout.preferredHeight: 5
                                    radius: 3
                                    color: window.accentA
                                }
                                Label {
                                    text: gameGrid.count + (gameGrid.count > 1 ? " JEUX" : " JEU")
                                    color: window.themeColors.text
                                    font.pixelSize: window.fontMicro
                                    font.weight: Font.DemiBold
                                    font.letterSpacing: 0.55
                                }
                            }
                        }
                        Item { Layout.fillWidth: true }
                        TextField {
                            id: searchField
                            Layout.preferredWidth: Math.max(170, Math.min(270, window.width * 0.19))
                            placeholderText: "Rechercher un jeu…"
                            color: window.themeColors.text
                            font.pixelSize: window.fontBody
                            Accessible.role: Accessible.EditableText
                            Accessible.name: "Rechercher un jeu"
                            Accessible.description: "Filtrer la bibliothèque par titre ou identifiant de jeu."
                            selectByMouse: true
                            onActiveFocusChanged: {
                                if (activeFocus) {
                                    window.navigationArea = "toolbar"
                                    window.toolbarFocusIndex = 0
                                }
                            }
                            background: Rectangle {
                                radius: 8
                                color: window.themeColors.surface
                                border.width: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 0 ? 2 : 1
                                border.color: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 0 ? window.focusColor : window.themeColors.border
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
                                color: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 1 ? window.themeColors.surface_elevated : window.themeColors.surface
                                border.width: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 1 ? 2 : 1
                                border.color: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 1 ? window.focusColor : window.themeColors.border
                            }
                            contentItem: Label {
                                text: refreshLibraryButton.text
                                color: window.themeColors.text
                                font.pixelSize: window.fontCaption
                                font.weight: Font.DemiBold
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                        Button {
                            id: importEmulatorFolderButton
                            text: "IMPORTER UN DOSSIER"
                            onActiveFocusChanged: {
                                if (activeFocus) {
                                    window.navigationArea = "toolbar"
                                    window.toolbarFocusIndex = 2
                                }
                            }
                            onClicked: {
                                window.navigationArea = "toolbar"
                                window.toolbarFocusIndex = 2
                                emulatorImportDialog.open()
                            }
                            background: Rectangle {
                                radius: 9
                                color: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 2 ? window.themeColors.surface_elevated : window.themeColors.surface
                                border.width: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 2 ? 2 : 1
                                border.color: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 2 ? window.accentA : window.themeColors.border
                            }
                            contentItem: Label {
                                text: importEmulatorFolderButton.text
                                color: window.themeColors.text
                                font.pixelSize: window.fontMicro
                                font.weight: Font.DemiBold
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                        Button {
                            id: emulatorPrerequisitesButton
                            text: "PRÉREQUIS"
                            onActiveFocusChanged: {
                                if (activeFocus) {
                                    window.navigationArea = "toolbar"
                                    window.toolbarFocusIndex = 3
                                }
                            }
                            onClicked: {
                                window.navigationArea = "toolbar"
                                window.toolbarFocusIndex = 3
                                emulatorPrerequisitesDialog.open()
                            }
                            background: Rectangle {
                                radius: 9
                                color: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 3 ? window.themeColors.surface_elevated : window.themeColors.surface
                                border.width: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 3 ? 2 : 1
                                border.color: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 3 ? window.focusColor : window.themeColors.border
                            }
                            contentItem: Label {
                                text: emulatorPrerequisitesButton.text
                                color: window.themeColors.text
                                font.pixelSize: window.fontCaption
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
                                    window.toolbarFocusIndex = 4
                                }
                            }
                            onClicked: {
                                window.navigationArea = "toolbar"
                                window.toolbarFocusIndex = 4
                                addDialog.open()
                            }
                            background: Rectangle {
                                radius: 9
                                color: window.themeColors.surface_elevated
                                border.width: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 4 ? 2 : 1
                                border.color: window.navigationArea === "toolbar" && window.toolbarFocusIndex === 4 ? window.focusColor : window.accentA
                            }
                            contentItem: Label {
                                text: addGameButton.text
                                color: window.themeColors.text
                                font.pixelSize: window.fontCaption
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
                            cellWidth: Math.max(220, Math.min(300, Math.floor(gameGrid.width / 3)))
                            cellHeight: 190
                            clip: true
                            model: gameLibrary
                            currentIndex: window.selectedIndex
                            Accessible.role: Accessible.List
                            Accessible.name: "Bibliothèque de jeux"
                            Accessible.description: "Jeux disponibles dans la catégorie sélectionnée. Les cartes ouvrent leur fiche détaillée."

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
                                Accessible.role: Accessible.Button
                                Accessible.name: gameCard.title
                                Accessible.selected: window.selectedIndex === gameCard.index
                                Accessible.focusable: true
                                Accessible.description: (gameCard.favorite ? "Favori. " : "")
                                    + "Plateforme " + gameCard.platform + ". Source " + gameCard.source
                                    + ". Activer pour afficher la fiche du jeu."
                                onClicked: window.selectGameAt(index)
                                background: Rectangle {
                                    radius: 15
                                    clip: true
                                    color: window.selectedIndex === gameCard.index || gameCard.hovered
                                           ? window.themeColors.surface_elevated : window.themeColors.surface
                                    border.width: gameCard.activeFocus ? 2 : 1
                                    border.color: gameCard.activeFocus ? window.focusColor
                                                  : window.selectedIndex === gameCard.index ? window.accentA
                                                  : gameCard.hovered ? window.accentB : window.themeColors.border
                                    Rectangle {
                                        anchors { left: parent.left; right: parent.right; top: parent.top }
                                        anchors.leftMargin: 16
                                        anchors.rightMargin: 16
                                        height: 2
                                        radius: 1
                                        visible: window.selectedIndex === gameCard.index || gameCard.hovered
                                        opacity: window.selectedIndex === gameCard.index ? 1 : 0.7
                                        gradient: Gradient {
                                            GradientStop { position: 0; color: window.accentA }
                                            GradientStop { position: 1; color: window.accentB }
                                        }
                                    }
                                    Rectangle {
                                        anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                                        width: 3
                                        opacity: window.selectedIndex === gameCard.index ? 1 : gameCard.hovered ? 0.72 : 0
                                        gradient: Gradient {
                                            GradientStop { position: 0; color: window.accentA }
                                            GradientStop { position: 1; color: window.accentB }
                                        }
                                    }
                                    Behavior on color { ColorAnimation { duration: 160; easing.type: Easing.OutCubic } }
                                    Behavior on border.color { ColorAnimation { duration: 160; easing.type: Easing.OutCubic } }
                                }
                                contentItem: ColumnLayout {
                                    spacing: 7
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        spacing: 10
                                        Item {
                                            Layout.preferredWidth: 88
                                            Layout.preferredHeight: 126
                                            Layout.alignment: Qt.AlignVCenter
                                            Rectangle {
                                                anchors.fill: parent
                                                radius: 9
                                                clip: true
                                                color: window.themeColors.background
                                                border.color: window.themeColors.border
                                                visible: gameCard.artwork.length === 0 || gameArtwork.status !== Image.Ready
                                                Rectangle {
                                                    width: parent.width * 1.5
                                                    height: parent.width * 1.5
                                                    radius: width / 2
                                                    x: -parent.width * 0.55
                                                    y: parent.height * 0.25
                                                    color: window.accentA
                                                    opacity: 0.18
                                                }
                                                Column {
                                                    anchors.centerIn: parent
                                                    spacing: 4
                                                    Label {
                                                        anchors.horizontalCenter: parent.horizontalCenter
                                                        text: window.gameMonogram(gameCard.title)
                                                        color: window.themeColors.text
                                                        font.pixelSize: window.fontTitle
                                                        font.weight: Font.Black
                                                        font.letterSpacing: 1
                                                    }
                                                    Label {
                                                        anchors.horizontalCenter: parent.horizontalCenter
                                                        text: "LEOS"
                                                        color: window.cyan
                                                        font.pixelSize: window.fontMicro
                                                        font.letterSpacing: 2
                                                    }
                                                }
                                            }
                                            Image {
                                                id: gameArtwork
                                                anchors.fill: parent
                                                anchors.margins: 1
                                                source: gameCard.artwork
                                                visible: gameCard.artwork.length > 0
                                                fillMode: Image.PreserveAspectCrop
                                                asynchronous: true
                                                cache: true
                                                sourceSize.width: 176
                                                sourceSize.height: 252
                                                opacity: status === Image.Ready ? 1 : 0
                                                Behavior on opacity { NumberAnimation { duration: 180 } }
                                            }
                                            Rectangle {
                                                anchors.fill: parent
                                                radius: 9
                                                color: "transparent"
                                                border.color: window.themeColors.border
                                            }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            spacing: 5
                                            Label {
                                                text: gameCard.title
                                                color: window.themeColors.text
                                                font.pixelSize: window.fontBody
                                                font.weight: Font.DemiBold
                                                wrapMode: Text.WordWrap
                                                Layout.fillWidth: true
                                            }
                                            Rectangle {
                                                visible: gameCard.favorite
                                                implicitWidth: favoriteChipLabel.implicitWidth + 16
                                                implicitHeight: 22
                                                radius: 11
                                                color: Qt.rgba(window.accentB.r, window.accentB.g, window.accentB.b, 0.14)
                                                border.color: window.accentB
                                                RowLayout {
                                                    anchors.fill: parent
                                                    anchors.leftMargin: 8
                                                    anchors.rightMargin: 8
                                                    spacing: 4
                                                    Label {
                                                        text: "★"
                                                        color: window.magenta
                                                        font.pixelSize: 12
                                                    }
                                                    Label {
                                                        id: favoriteChipLabel
                                                        text: "FAVORI"
                                                        color: window.themeColors.text
                                                        font.pixelSize: 12
                                                        font.weight: Font.Bold
                                                        font.letterSpacing: 0.6
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 7
                                        Rectangle {
                                            implicitWidth: platformChipLabel.implicitWidth + 14
                                            implicitHeight: 22
                                            radius: 7
                                            color: window.themeColors.surface_elevated
                                            border.color: window.themeColors.border
                                            Label {
                                                id: platformChipLabel
                                                anchors.centerIn: parent
                                                text: gameCard.platform
                                                color: window.themeColors.text
                                                font.pixelSize: 12
                                                font.weight: Font.DemiBold
                                            }
                                        }
                                        Label {
                                            text: gameCard.source
                                            color: window.muted
                                            font.pixelSize: window.fontMicro
                                            Layout.fillWidth: true
                                            elide: Text.ElideRight
                                        }
                                    }
                                }
                            }

                            ColumnLayout {
                                anchors.centerIn: parent
                                width: parent.width - 50
                                visible: gameGrid.count === 0
                                spacing: 14
                                Accessible.role: Accessible.Grouping
                                Accessible.name: "Bibliothèque vide ou sans résultat"

                                Label {
                                    Layout.fillWidth: true
                                    Accessible.role: Accessible.StaticText
                                    Accessible.name: text
                                    horizontalAlignment: Text.AlignHCenter
                                    wrapMode: Text.WordWrap
                                    text: searchField.text.length > 0
                                        ? "Aucun résultat pour « " + searchField.text + " »."
                                        : window.selectedCategory === "Favoris"
                                            ? "Aucun favori pour le moment."
                                            : window.selectedCategory === "Récemment joués"
                                                ? "Aucun jeu lancé récemment."
                                                : "Aucun jeu détecté dans cette catégorie. Installe un jeu dans Steam, Heroic ou Lutris, puis sélectionne ACTUALISER. Tu peux aussi ajouter un jeu manuellement."
                                    color: window.muted
                                    font.pixelSize: window.fontBody
                                }

                                Button {
                                    id: emptyStatePrimaryButton
                                    Layout.fillWidth: true
                                    text: window.emptyStatePrimaryLabel()
                                    Accessible.role: Accessible.Button
                                    Accessible.name: text
                                    Accessible.description: "Action proposée pour retrouver des jeux dans cette vue."
                                    onClicked: window.activateEmptyStatePrimaryAction()
                                    background: Rectangle {
                                        radius: 9
                                        color: window.themeColors.surface_elevated
                                        border.width: emptyStatePrimaryButton.activeFocus ? 2 : 1
                                        border.color: emptyStatePrimaryButton.activeFocus ? window.focusColor : window.accentA
                                    }
                                    contentItem: Label {
                                        text: emptyStatePrimaryButton.text
                                        color: window.themeColors.text
                                        font.pixelSize: window.fontCaption
                                        font.weight: Font.DemiBold
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }

                                Button {
                                    id: emptyStateAddButton
                                    Layout.fillWidth: true
                                    visible: searchField.text.length === 0
                                        && window.selectedCategory !== "Favoris"
                                        && window.selectedCategory !== "Récemment joués"
                                    text: "AJOUTER UN JEU"
                                    Accessible.role: Accessible.Button
                                    Accessible.name: text
                                    onClicked: {
                                        window.navigationArea = "toolbar"
                                        window.toolbarFocusIndex = 2
                                        addDialog.open()
                                    }
                                    background: Rectangle {
                                        radius: 9
                                        color: window.themeColors.surface
                                        border.width: emptyStateAddButton.activeFocus ? 2 : 1
                                        border.color: emptyStateAddButton.activeFocus ? window.focusColor : window.themeColors.border
                                    }
                                    contentItem: Label {
                                        text: emptyStateAddButton.text
                                        color: window.themeColors.text
                                        font.pixelSize: window.fontCaption
                                        font.weight: Font.DemiBold
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.preferredWidth: window.width < 1180 ? 230 : 280
                            Layout.minimumWidth: 210
                            Layout.fillHeight: true
                            radius: 17
                            clip: true
                            color: window.themeColors.surface
                            border.color: window.themeColors.border
                            Accessible.role: Accessible.Grouping
                            Accessible.name: "Détails du jeu sélectionné"
                            Rectangle {
                                anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                                width: 3
                                gradient: Gradient {
                                    GradientStop { position: 0; color: window.accentA }
                                    GradientStop { position: 1; color: window.accentB }
                                }
                                opacity: 0.75
                            }

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 20
                                spacing: 12

                                Label {
                                    text: "JEU SÉLECTIONNÉ"
                                    color: window.cyan
                                    font.pixelSize: window.fontCaption
                                    font.letterSpacing: 2
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 172
                                    radius: 11
                                    clip: true
                                    color: window.themeColors.background
                                    border.color: window.themeColors.border
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
                                            color: window.themeColors.muted_text
                                            font.pixelSize: window.fontTitle
                                            font.weight: Font.Black
                                            font.letterSpacing: 5
                                        }
                                        Label {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            text: window.selectedTitle ? "ARTWORK NON DISPONIBLE" : "SÉLECTIONNE UN JEU"
                                            color: window.muted
                                            font.pixelSize: window.fontMicro
                                            font.letterSpacing: 1
                                        }
                                    }
                                }
                                Label {
                                    text: window.selectedTitle || "Choisis un jeu"
                                    color: window.themeColors.text
                                    font.pixelSize: window.fontTitle
                                    font.weight: Font.Bold
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }
                                Label {
                                    text: window.selectedTitle ? window.selectedPlatform + " • " + window.selectedSource : "Les détails apparaîtront ici."
                                    color: window.muted
                                    font.pixelSize: window.fontBody
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    implicitHeight: 1
                                    color: window.themeColors.border
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    Label {
                                        text: "STATUT"
                                        color: window.muted
                                        font.pixelSize: window.fontMicro
                                        font.letterSpacing: 1
                                    }
                                    Item { Layout.fillWidth: true }
                                    Label {
                                        text: window.selectedInstallStatus || "—"
                                        color: window.selectedInstallStatus === "Installé" ? window.cyan :
                                               window.selectedInstallStatus === "Fichiers absents" ? "#d5a45d" : window.themeColors.text
                                        font.pixelSize: window.fontCaption
                                        font.weight: Font.DemiBold
                                    }
                                }
                                Label {
                                    Layout.fillWidth: true
                                    visible: window.selectedAppId.length > 0
                                    text: "IDENTIFIANT  ·  " + window.selectedAppId
                                    color: window.themeColors.muted_text
                                    font.pixelSize: window.fontMicro
                                    elide: Text.ElideMiddle
                                }
                                Label {
                                    Layout.fillWidth: true
                                    visible: window.selectedDuplicateCount > 1
                                    text: "DOUBLON POTENTIEL · " + window.selectedDuplicateCount + " entrées (" + window.selectedDuplicateSources + ")"
                                    color: "#d5a45d"
                                    font.pixelSize: window.fontMicro
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
                                        color: window.themeColors.surface
                                        border.width: window.navigationArea === "details" && window.detailsActionIndex === 0 ? 2 : 1
                                        border.color: window.navigationArea === "details" && window.detailsActionIndex === 0 ? window.focusColor : window.accentB
                                    }
                                    contentItem: Label {
                                        text: favoriteGameButton.text
                                        color: window.themeColors.text
                                        font.pixelSize: window.fontCaption
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
                                        color: launchSelectedGameButton.enabled ? window.themeColors.surface_elevated : window.themeColors.surface
                                        border.width: window.navigationArea === "details" && window.detailsActionIndex === 1 ? 2 : 1
                                        border.color: window.navigationArea === "details" && window.detailsActionIndex === 1 ? window.focusColor : launchSelectedGameButton.enabled ? window.accentA : window.themeColors.border
                                    }
                                    contentItem: Label {
                                        text: launchSelectedGameButton.text
                                        color: launchSelectedGameButton.enabled ? window.themeColors.text : window.themeColors.muted_text
                                        font.pixelSize: window.fontBody
                                        font.weight: Font.Bold
                                        horizontalAlignment: Text.AlignHCenter
                                    }
                                }
                                Label {
                                    id: statusText
                                    Layout.fillWidth: true
                                    Accessible.role: Accessible.StaticText
                                    Accessible.name: statusText.text
                                    Accessible.description: "Résultat de la dernière action ou du lancement."
                                    color: window.muted
                                    font.pixelSize: window.fontCaption
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 34
                spacing: 12
                Accessible.role: Accessible.Grouping
                Accessible.name: "Aide à la navigation Gaming"

                Label {
                    text: "MANETTE"
                    color: window.cyan
                    font.pixelSize: window.fontMicro
                    font.weight: Font.Bold
                }
                Label {
                    text: leos.gamepadButtonLegend + "   START / MENU · PANNEAU"
                    color: window.themeColors.text
                    font.pixelSize: window.fontMicro
                    Accessible.role: Accessible.StaticText
                    Accessible.name: "Commandes de la manette : " + text
                }
                Item { Layout.fillWidth: true }
                Label {
                    text: "CLAVIER"
                    color: window.cyan
                    font.pixelSize: window.fontMicro
                    font.weight: Font.Bold
                }
                Label {
                    text: "FLÈCHES · NAVIGUER    ENTRÉE / ESPACE · VALIDER    ÉCHAP · RETOUR    F1 · PANNEAU    F2 · AJOUTER"
                    color: window.muted
                    font.pixelSize: window.fontMicro
                    Accessible.role: Accessible.StaticText
                    Accessible.name: "Commandes clavier : " + text
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
                color: window.themeColors.text
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
                background: Rectangle { radius: 9; color: window.themeColors.surface_elevated; border.color: window.accentA }
                contentItem: Label {
                    text: returnToDesktopButton.text
                    color: window.themeColors.text
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
                color: window.themeColors.text
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
                background: Rectangle { radius: 9; color: window.themeColors.surface_elevated; border.color: window.accentA }
                contentItem: Label {
                    text: confirmPowerProfileButton.text
                    color: window.themeColors.text
                    font.weight: Font.Bold
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }

    Dialog {
        id: emulatorPrerequisitesDialog
        title: "PRÉREQUIS ET CŒURS RETROARCH"
        modal: true
        anchors.centerIn: parent
        width: Math.min(window.width - 64, 760)
        height: Math.min(window.height - 70, 720)
        property int controllerFocusIndex: 0

        onOpened: {
            controllerFocusIndex = 0
            edenOpenSetupButton.forceActiveFocus()
        }

        ColumnLayout {
            width: parent.width
            spacing: 10

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                ColumnLayout {
                    width: parent.width
                    spacing: 9

                    Label {
                        text: "ÉTAT DE CONFIGURATION"
                        color: window.accentA
                        font.pixelSize: window.fontCaption
                        font.letterSpacing: 2
                    }
                    Label {
                        text: "LEOS vérifie uniquement la présence de fichiers et de dossiers attendus. Il ne lit pas leur contenu et ne peut pas certifier leur authenticité ni leur compatibilité."
                        color: window.muted
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Repeater {
                        model: leos.emulatorPrerequisiteStatuses
                        delegate: Rectangle {
                            required property string modelData
                            Layout.fillWidth: true
                            implicitHeight: prerequisiteLabel.implicitHeight + 20
                            radius: 8
                            color: window.themeColors.surface
                            border.color: window.themeColors.border

                            Label {
                                id: prerequisiteLabel
                                anchors.fill: parent
                                anchors.margins: 10
                                text: modelData
                                color: modelData.toLowerCase().includes("détect") ? window.accentA : window.themeColors.text
                                wrapMode: Text.WordWrap
                                font.pixelSize: window.fontBody
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }

                    Label {
                        text: "CONFIGURATION NINTENDO SWITCH — EDEN"
                        color: window.accentA
                        font.pixelSize: window.fontCaption
                        font.letterSpacing: 2
                        Layout.topMargin: 5
                    }
                    Label {
                        text: "À savoir : le paquet Flathub d'Eden est communautaire et n'est pas vérifié ni pris en charge par l'équipe Eden. Sa fiche indique 8 Gio de mémoire au minimum et 16 Gio recommandés ; les performances dépendent aussi du jeu et du GPU."
                        color: window.muted
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Label {
                        text: "1. Ouvre Eden, puis Tools > Install Decryption Keys et sélectionne ton fichier prod.keys extrait de ta propre console. title.keys est facultatif selon les titres."
                        color: window.muted
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Label {
                        text: "2. Ensuite, utilise Tools > Install Firmware > Select From Folder ou Select From ZIP. Installe les clés avant le firmware ; choisis uniquement un firmware extrait de ta propre console."
                        color: window.muted
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Label {
                        text: "3. Dans la fenêtre principale d'Eden, ajoute le dossier de tes jeux. Pour régler la manette : Emulation > Configure > Input. Reviens ensuite ici et actualise l'état."
                        color: window.muted
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Label {
                        text: "LEOS ne fournit, ne télécharge et ne vérifie pas les clés, le firmware ou les jeux. La détection locale confirme seulement la présence de fichiers ; elle ne garantit pas qu'un jeu démarre."
                        color: window.muted
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    Label {
                        text: "CŒURS RETROARCH RECOMMANDÉS"
                        color: window.accentA
                        font.pixelSize: window.fontCaption
                        font.letterSpacing: 2
                        Layout.topMargin: 5
                    }
                    Label {
                        text: "Les cœurs ci-dessous couvrent plusieurs systèmes courants. « Détecté » signifie seulement que le fichier du cœur est présent ; cela ne garantit pas son bon fonctionnement ni les performances sur ton matériel."
                        color: window.muted
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Repeater {
                        model: leos.retroarchCoreStatuses
                        delegate: Rectangle {
                            required property string modelData
                            Layout.fillWidth: true
                            implicitHeight: retroArchCoreLabel.implicitHeight + 16
                            radius: 8
                            color: window.themeColors.surface
                            border.color: window.themeColors.border

                            Label {
                                id: retroArchCoreLabel
                                anchors.fill: parent
                                anchors.margins: 8
                                text: modelData
                                color: modelData.toLowerCase().includes("détecté") ? window.accentA : window.themeColors.text
                                wrapMode: Text.WordWrap
                                font.pixelSize: window.fontBody
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }
                    Label {
                        text: "Pour installer un cœur : ouvre RetroArch, puis Online Updater > Select Core Downloader. Si « Core Downloader » est masqué, active-le dans Settings > User Interface > Menu Item Visibility > Show Core Downloader."
                        color: window.muted
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Label {
                        text: "LEOS ne télécharge pas les cœurs, jeux, BIOS, firmwares ni clés. Les listes et fichiers de jeu restent gérés par RetroArch ; reviens ici et actualise après avoir installé les cœurs."
                        color: window.muted
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Button {
                    id: edenOpenSetupButton
                    text: "OUVRIR EDEN"
                    Layout.fillWidth: true
                    onActiveFocusChanged: {
                        if (activeFocus)
                            emulatorPrerequisitesDialog.controllerFocusIndex = 0
                    }
                    onClicked: leos.openEdenSetup()
                    background: Rectangle {
                        radius: 9
                        color: window.themeColors.surface_elevated
                        border.color: edenOpenSetupButton.activeFocus ? window.focusColor : window.accentA
                        border.width: edenOpenSetupButton.activeFocus ? 2 : 1
                    }
                    contentItem: Label {
                        text: edenOpenSetupButton.text
                        color: window.themeColors.text
                        font.weight: Font.Bold
                        horizontalAlignment: Text.AlignHCenter
                    }
                }

                Button {
                    id: retroArchOpenCoreUpdaterButton
                    text: "OUVRIR RETROARCH"
                    Layout.fillWidth: true
                    onActiveFocusChanged: {
                        if (activeFocus)
                            emulatorPrerequisitesDialog.controllerFocusIndex = 1
                    }
                    onClicked: leos.openRetroArchCoreUpdater()
                    background: Rectangle {
                        radius: 9
                        color: window.themeColors.surface_elevated
                        border.color: retroArchOpenCoreUpdaterButton.activeFocus ? window.focusColor : window.accentA
                        border.width: retroArchOpenCoreUpdaterButton.activeFocus ? 2 : 1
                    }
                    contentItem: Label {
                        text: retroArchOpenCoreUpdaterButton.text
                        color: window.themeColors.text
                        font.weight: Font.Bold
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Button {
                    id: retroArchRefreshCoreStatusButton
                    text: "ACTUALISER"
                    Layout.fillWidth: true
                    onActiveFocusChanged: {
                        if (activeFocus)
                            emulatorPrerequisitesDialog.controllerFocusIndex = 2
                    }
                    onClicked: leos.refreshRetroArchCoreStatuses()
                    background: Rectangle {
                        radius: 9
                        color: window.themeColors.surface
                        border.color: retroArchRefreshCoreStatusButton.activeFocus ? window.focusColor : window.themeColors.border
                        border.width: retroArchRefreshCoreStatusButton.activeFocus ? 2 : 1
                    }
                    contentItem: Label {
                        text: retroArchRefreshCoreStatusButton.text
                        color: window.themeColors.text
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                    }
                }

                Button {
                    id: retroArchCloseDialogButton
                    text: "FERMER"
                    Layout.fillWidth: true
                    onActiveFocusChanged: {
                        if (activeFocus)
                            emulatorPrerequisitesDialog.controllerFocusIndex = 3
                    }
                    onClicked: emulatorPrerequisitesDialog.close()
                    background: Rectangle {
                        radius: 9
                        color: window.themeColors.surface
                        border.color: retroArchCloseDialogButton.activeFocus ? window.focusColor : window.themeColors.border
                        border.width: retroArchCloseDialogButton.activeFocus ? 2 : 1
                    }
                    contentItem: Label {
                        text: retroArchCloseDialogButton.text
                        color: window.themeColors.text
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }

        }
    }

    Dialog {
        id: emulatorImportDialog
        title: "Importer des jeux console"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Cancel
        width: 520
        property int controllerFocusIndex: 0

        onOpened: {
            controllerFocusIndex = 0
            emulatorPlatformCombo.forceActiveFocus()
        }

        ColumnLayout {
            width: parent.width
            spacing: 12
            Label {
                text: "Choisis la plateforme correspondant aux fichiers du dossier."
                color: window.themeColors.text
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            ComboBox {
                id: emulatorPlatformCombo
                Layout.fillWidth: true
                onActiveFocusChanged: {
                    if (activeFocus)
                        emulatorImportDialog.controllerFocusIndex = 0
                }
                model: [
                    "Nintendo GameCube / Wii",
                    "PlayStation 2",
                    "PlayStation Portable (PSP)",
                    "Nintendo DS (melonDS)",
                    "Nintendo Switch (Eden)",
                    "PlayStation 3 (RPCS3)"
                ]
            }
            Label {
                text: "LEOS parcourra uniquement le dossier que tu sélectionnes et ses sous-dossiers (limites de profondeur et de fichiers). Les jeux ne seront ni modifiés ni déplacés."
                color: window.muted
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                font.pixelSize: window.fontMicro
            }
            Label {
                text: "RPCS3 : importe un dossier de jeu PS3 contenant PARAM.SFO et USRDIR/EBOOT.BIN. Les PKG et fichiers RAP se configurent dans RPCS3 ; LEOS ne les installe pas."
                color: window.muted
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                font.pixelSize: window.fontMicro
            }
            Label {
                text: "LEOS prépare automatiquement les émulateurs au premier démarrage connecté. Les jeux, BIOS, firmwares et clés personnels ne sont pas fournis."
                color: window.muted
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                font.pixelSize: window.fontMicro
            }
            Button {
                id: emulatorChooseFolderButton
                text: "CHOISIR LE DOSSIER"
                Layout.fillWidth: true
                onActiveFocusChanged: {
                    if (activeFocus)
                        emulatorImportDialog.controllerFocusIndex = 1
                }
                onClicked: {
                    const platformKeys = ["gamecube_wii", "ps2", "psp", "melonds", "eden", "rpcs3"]
                    if (leos.beginEmulatorFolderBrowse(
                                platformKeys[emulatorPlatformCombo.currentIndex])) {
                        emulatorImportDialog.close()
                        emulatorFolderDialog.open()
                    }
                }
                background: Rectangle { radius: 9; color: window.themeColors.surface_elevated; border.color: window.accentA }
                contentItem: Label {
                    text: "CHOISIR LE DOSSIER"
                    color: window.themeColors.text
                    font.weight: Font.Bold
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            Button {
                id: emulatorManageSourcesButton
                text: "GÉRER LES DOSSIERS AJOUTÉS"
                Layout.fillWidth: true
                onActiveFocusChanged: {
                    if (activeFocus)
                        emulatorImportDialog.controllerFocusIndex = 2
                }
                onClicked: emulatorSourcesDialog.open()
                background: Rectangle {
                    radius: 9
                    color: window.themeColors.surface
                    border.color: activeFocus ? window.focusColor : window.themeColors.border
                    border.width: activeFocus ? 2 : 1
                }
                contentItem: Label {
                    text: "GÉRER LES DOSSIERS AJOUTÉS"
                    color: window.themeColors.text
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }

    Dialog {
        id: emulatorSourcesDialog
        title: "GÉRER LES DOSSIERS DE JEUX"
        modal: true
        anchors.centerIn: parent
        width: Math.min(window.width - 64, 680)
        height: Math.min(window.height - 80, 560)
        standardButtons: Dialog.Close

        onOpened: {
            emulatorSourcesList.currentIndex =
                leos.emulatorSourceFolders.length > 0 ? 0 : -1
            if (emulatorSourcesList.currentItem)
                emulatorSourcesList.currentItem.forceActiveFocus()
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 10

            Label {
                text: "DOSSIERS SÉLECTIONNÉS"
                color: window.accentA
                font.pixelSize: window.fontMicro
                font.letterSpacing: 2
            }
            Label {
                text: "Retirer un dossier le supprime uniquement de la bibliothèque LEOS. Aucun jeu et aucun fichier du disque ne sera effacé."
                color: window.muted
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 10
                color: window.themeColors.surface
                border.color: window.themeColors.border

                ListView {
                    id: emulatorSourcesList
                    anchors.fill: parent
                    anchors.margins: 8
                    clip: true
                    spacing: 5
                    model: leos.emulatorSourceFolders
                    delegate: Button {
                        required property var modelData
                        required property int index
                        width: ListView.view.width
                        height: 48
                        text: "RETIRER  ·  " + modelData.label
                        Accessible.name: "Retirer " + modelData.label + " de la bibliothèque"
                        onActiveFocusChanged: {
                            if (activeFocus)
                                emulatorSourcesList.currentIndex = index
                        }
                        onClicked: {
                            if (leos.removeEmulatorFolder(modelData.platform, modelData.path)) {
                                const count = leos.emulatorSourceFolders.length
                                emulatorSourcesList.currentIndex =
                                    count > 0 ? Math.min(index, count - 1) : -1
                                if (emulatorSourcesList.currentItem)
                                    emulatorSourcesList.currentItem.forceActiveFocus()
                            }
                        }
                        background: Rectangle {
                            radius: 8
                            color: emulatorSourcesList.currentIndex === index
                                ? window.themeColors.surface_elevated : window.themeColors.surface
                            border.width: activeFocus ? 2 : 1
                            border.color: activeFocus ? window.focusColor : window.themeColors.border
                        }
                        contentItem: Label {
                            text: parent.text
                            color: window.themeColors.text
                            elide: Text.ElideMiddle
                            verticalAlignment: Text.AlignVCenter
                            leftPadding: 10
                        }
                    }
                    Keys.onUpPressed: {
                        if (count > 0)
                            currentIndex = Math.max(0, currentIndex - 1)
                        event.accepted = true
                    }
                    Keys.onDownPressed: {
                        if (count > 0)
                            currentIndex = Math.min(count - 1, currentIndex + 1)
                        event.accepted = true
                    }
                }
            }
            Label {
                visible: leos.emulatorSourceFolders.length === 0
                text: "Aucun dossier de jeux n'est encore ajouté."
                color: window.muted
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }

    Dialog {
        id: emulatorFolderDialog
        title: "CHOISIR LE DOSSIER DES JEUX"
        modal: true
        anchors.centerIn: parent
        width: Math.min(window.width - 80, 720)
        height: Math.min(window.height - 100, 650)
        standardButtons: Dialog.NoButton

        onOpened: {
            folderDirectoryList.currentIndex =
                leos.emulatorFolderDirectories.length > 0 ? 0 : -1
            if (folderDirectoryList.currentItem)
                folderDirectoryList.currentItem.forceActiveFocus()
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 12

            Label {
                text: "EMPLACEMENT"
                color: window.cyan
                font.pixelSize: window.fontMicro
                font.letterSpacing: 2
            }
            Label {
                text: leos.emulatorFolderPath
                color: window.themeColors.text
                font.pixelSize: 12
                Layout.fillWidth: true
                elide: Text.ElideMiddle
            }
            RowLayout {
                Layout.fillWidth: true
                Button {
                    text: "← DOSSIER PARENT"
                    onClicked: {
                        leos.browseEmulatorFolderParent()
                        folderDirectoryList.currentIndex =
                            leos.emulatorFolderDirectories.length > 0 ? 0 : -1
                    }
                    background: Rectangle {
                        radius: 8
                        color: window.themeColors.surface
                        border.color: window.themeColors.border
                    }
                    contentItem: Label {
                        text: parent.text
                        color: window.themeColors.text
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
                Item { Layout.fillWidth: true }
                Label {
                    text: "A : ouvrir  ·  ← : parent  ·  Menu : choisir"
                    color: window.muted
                    font.pixelSize: window.fontMicro
                }
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 10
                color: window.themeColors.surface
                border.color: window.themeColors.border
                ListView {
                    id: folderDirectoryList
                    anchors.fill: parent
                    anchors.margins: 8
                    clip: true
                    spacing: 4
                    focus: true
                    model: leos.emulatorFolderDirectories
                    delegate: Button {
                        required property string modelData
                        required property int index
                        width: ListView.view.width
                        height: 46
                        text: "📁  " + modelData
                        onActiveFocusChanged: {
                            if (activeFocus)
                                folderDirectoryList.currentIndex = index
                        }
                        onClicked: {
                            if (leos.enterEmulatorFolder(modelData)) {
                                folderDirectoryList.currentIndex =
                                    leos.emulatorFolderDirectories.length > 0 ? 0 : -1
                                if (folderDirectoryList.currentItem)
                                    folderDirectoryList.currentItem.forceActiveFocus()
                            }
                        }
                        background: Rectangle {
                            radius: 7
                            color: folderDirectoryList.currentIndex === index
                                   ? window.themeColors.surface_elevated : window.themeColors.surface
                            border.width: folderDirectoryList.currentIndex === index ? 2 : 1
                            border.color: folderDirectoryList.currentIndex === index
                                          ? window.cyan : window.themeColors.border
                        }
                        contentItem: Label {
                            text: parent.text
                            color: window.themeColors.text
                            verticalAlignment: Text.AlignVCenter
                            leftPadding: 10
                        }
                    }
                    Keys.onUpPressed: {
                        if (count > 0)
                            currentIndex = Math.max(0, currentIndex - 1)
                        event.accepted = true
                    }
                    Keys.onDownPressed: {
                        if (count > 0)
                            currentIndex = Math.min(count - 1, currentIndex + 1)
                        event.accepted = true
                    }
                    Keys.onLeftPressed: {
                        leos.browseEmulatorFolderParent()
                        currentIndex = leos.emulatorFolderDirectories.length > 0 ? 0 : -1
                        event.accepted = true
                    }
                    Keys.onRightPressed: {
                        if (currentIndex >= 0 && currentIndex < count) {
                            const name = leos.emulatorFolderDirectories[currentIndex]
                            if (leos.enterEmulatorFolder(name))
                                currentIndex = leos.emulatorFolderDirectories.length > 0 ? 0 : -1
                        }
                        event.accepted = true
                    }
                    Keys.onReturnPressed: {
                        if (currentIndex >= 0 && currentIndex < count) {
                            const name = leos.emulatorFolderDirectories[currentIndex]
                            if (leos.enterEmulatorFolder(name))
                                currentIndex = leos.emulatorFolderDirectories.length > 0 ? 0 : -1
                        }
                        event.accepted = true
                    }
                    Keys.onEnterPressed: {
                        if (currentIndex >= 0 && currentIndex < count) {
                            const name = leos.emulatorFolderDirectories[currentIndex]
                            if (leos.enterEmulatorFolder(name))
                                currentIndex = leos.emulatorFolderDirectories.length > 0 ? 0 : -1
                        }
                        event.accepted = true
                    }
                }
                Label {
                    anchors.centerIn: parent
                    visible: folderDirectoryList.count === 0
                    text: "Aucun sous-dossier accessible à cet emplacement."
                    color: window.muted
                    font.pixelSize: 12
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }
                Button {
                    text: "ANNULER"
                    onClicked: emulatorFolderDialog.close()
                    background: Rectangle {
                        radius: 8
                        color: "transparent"
                        border.color: window.themeColors.border
                    }
                    contentItem: Label {
                        text: parent.text
                        color: window.themeColors.text
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
                Button {
                    text: "UTILISER CE DOSSIER"
                    onClicked: {
                        if (leos.useCurrentEmulatorFolder()) {
                            emulatorFolderDialog.close()
                            window.clearSelection()
                            window.navigationArea = "games"
                            gameGrid.forceActiveFocus()
                        }
                    }
                    background: Rectangle {
                        radius: 8
                        color: window.themeColors.surface_elevated
                        border.color: window.accentA
                    }
                    contentItem: Label {
                        text: parent.text
                        color: window.themeColors.text
                        font.weight: Font.Bold
                        horizontalAlignment: Text.AlignHCenter
                    }
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
            Label { text: "Nom du jeu"; color: window.themeColors.text }
            TextField {
                id: gameName
                Layout.fillWidth: true
                placeholderText: "Ex. : Mon jeu"
                maximumLength: 256
            }
            Label { text: "Plateforme"; color: window.themeColors.text }
            ComboBox {
                id: gamePlatform
                Layout.fillWidth: true
                model: ["PC", "Nintendo", "PlayStation", "SEGA", "Arcade", "Autre"]
            }
            Label { text: "Commande de lancement"; color: window.themeColors.text }
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
                font.pixelSize: window.fontCaption
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
