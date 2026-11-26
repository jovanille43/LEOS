import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1180
    height: 790
    minimumWidth: 900
    minimumHeight: 640
    visible: true
    title: "LEOS — Boutique"
    property var themeColors: leosTheme.themePalette
    color: themeColors.background

    property color cyan: themeColors.accent_primary_text
    property color magenta: themeColors.accent_secondary_text
    property color accentA: themeColors.accent_primary
    property color accentB: themeColors.accent_secondary
    property color muted: themeColors.muted_text
    property int selectedRow: -1

    function normalizedSearchText(value) {
        return String(value || "")
            .normalize("NFKD")
            .toLowerCase()
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/\s+/g, " ")
            .trim()
    }

    function matchesSearch(name, appId, category, description, source, compatibility, operationNote) {
        const query = normalizedSearchText(searchField.text)
        if (!query)
            return true
        const searchable = normalizedSearchText(
            [name, appId, category, description, source, compatibility, operationNote].join(" ")
        )
        return searchable.includes(query)
    }

    function visibleApplicationCount() {
        let visibleCount = 0
        for (let row = 0; row < catalogModel.rowCount(); row++) {
            const item = store.catalogItem(row)
            if (!item)
                continue
            if (categoryFilter.currentText !== "Toutes" && item.category !== categoryFilter.currentText)
                continue
            if (matchesSearch(item.name, item.id, item.category, item.description,
                              item.source, item.compatibility, item.operation_note))
                visibleCount++
        }
        return visibleCount
    }

    function clearFilters() {
        searchField.clear()
        categoryFilter.currentIndex = 0
        clearSelection()
        searchField.forceActiveFocus()
    }

    function clearSelection() {
        selectedRow = -1
        detailsPane.appId = ""
        detailsPane.appName = "Choisis une application"
        detailsPane.appCategory = ""
        detailsPane.appDescription = "Sélectionne une application pour consulter sa fiche et ses options."
        detailsPane.appSource = ""
        detailsPane.appCompatibility = ""
        detailsPane.operationNote = ""
        detailsPane.isInstalled = false
        detailsPane.installedScope = ""
        detailsPane.bundled = false
    }

    function selectApp(row, id, name, category, description, source, compatibility, note, installed, scope, bundled) {
        selectedRow = row
        detailsPane.appId = id
        detailsPane.appName = name
        detailsPane.appCategory = category
        detailsPane.appDescription = description
        detailsPane.appSource = source
        detailsPane.appCompatibility = compatibility
        detailsPane.operationNote = note
        detailsPane.isInstalled = installed
        detailsPane.installedScope = scope
        detailsPane.bundled = bundled
    }

    Rectangle {
        anchors.fill: parent
        color: window.color
        clip: true

        Rectangle {
            width: 520
            height: width
            radius: width / 2
            x: parent.width - width * 0.58
            y: -height * 0.68
            color: window.themeColors.accent_primary
            opacity: 0.05
        }
        Rectangle {
            width: 410
            height: width
            radius: width / 2
            x: -width * 0.55
            y: parent.height * 0.68
            color: window.themeColors.accent_secondary
            opacity: 0.04
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: window.width < 1080 ? 18 : 30
            spacing: 15

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 58
                spacing: 14

                Image {
                    id: storeLogo
                    source: leosTheme.desktopLogoUrl
                    asynchronous: true
                    smooth: true
                    fillMode: Image.PreserveAspectFit
                    Layout.preferredWidth: 78
                    Layout.preferredHeight: 50
                    visible: status === Image.Ready
                }

                ColumnLayout {
                    spacing: 2
                    Label {
                        text: "LEOS"
                        color: window.themeColors.text
                        font.pixelSize: 26
                        font.weight: Font.Black
                        font.letterSpacing: 5
                        visible: storeLogo.status !== Image.Ready
                    }
                    Label {
                        text: "BOUTIQUE D’APPLICATIONS"
                        color: window.cyan
                        font.pixelSize: 10
                        font.weight: Font.Bold
                        font.letterSpacing: 2.4
                    }
                    Label {
                        text: "DÉCOUVRIR · INSTALLER · GÉRER"
                        color: window.muted
                        font.pixelSize: 9
                        font.letterSpacing: 0.8
                    }
                }

                Item { Layout.fillWidth: true }

                Rectangle {
                    radius: 11
                    color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.075)
                    border.color: window.themeColors.border
                    implicitWidth: storeBusyLabel.implicitWidth + 24
                    implicitHeight: 36
                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 8
                        Rectangle {
                            width: 7
                            height: 7
                            radius: 4
                            color: store.busy ? window.accentA : "#79B99A"
                        }
                        Label {
                            id: storeBusyLabel
                            text: store.busy ? "ACTUALISATION EN COURS" : "CATALOGUE PRÊT"
                            color: store.busy ? window.cyan : window.muted
                            font.pixelSize: 9
                            font.weight: Font.DemiBold
                            font.letterSpacing: 1
                        }
                    }
                }

                Button {
                    id: refreshButton
                    text: "ACTUALISER"
                    enabled: !store.busy
                    implicitHeight: 38
                    onClicked: store.refreshInstalled()
                    background: Rectangle {
                        radius: 10
                        color: refreshButton.down
                               ? window.themeColors.surface_elevated
                               : Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.10)
                        border.color: refreshButton.hovered ? window.accentA : window.themeColors.border
                        Behavior on border.color { ColorAnimation { duration: 140 } }
                    }
                    contentItem: Label {
                        text: refreshButton.text
                        color: refreshButton.enabled ? window.themeColors.text : window.muted
                        font.pixelSize: 10
                        font.weight: Font.DemiBold
                        letterSpacing: 0.8
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 12
                        rightPadding: 12
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 2
                radius: 1
                opacity: 0.72
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: window.accentA }
                    GradientStop { position: 0.48; color: window.themeColors.border }
                    GradientStop { position: 1.0; color: window.accentB }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 48
                    radius: 12
                    color: window.themeColors.surface
                    border.width: searchField.activeFocus ? 2 : 1
                    border.color: searchField.activeFocus ? window.accentA : window.themeColors.border
                    Behavior on border.color { ColorAnimation { duration: 140 } }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        anchors.rightMargin: 14
                        spacing: 10
                        Label {
                            text: "⌕"
                            color: window.cyan
                            font.pixelSize: 23
                            Layout.alignment: Qt.AlignVCenter
                        }
                        TextField {
                            id: searchField
                            Layout.fillWidth: true
                            placeholderText: "Rechercher une application, un outil ou un émulateur…"
                            color: window.themeColors.text
                            placeholderTextColor: window.muted
                            selectByMouse: true
                            enabled: !store.busy
                            Accessible.name: "Rechercher dans la Boutique LEOS"
                            Accessible.description: "Recherche dans les noms, descriptions, catégories, identifiants et métadonnées des applications."
                            onTextChanged: window.clearSelection()
                            background: Rectangle { color: "transparent" }
                        }
                        Label {
                            text: "RECHERCHE"
                            color: window.muted
                            font.pixelSize: 8
                            font.letterSpacing: 1
                        }
                    }
                }

                ComboBox {
                    id: categoryFilter
                    Layout.preferredWidth: 190
                    Layout.preferredHeight: 48
                    model: ["Toutes"].concat(catalogModel.availableCategories)
                    enabled: !store.busy
                    Accessible.name: "Filtrer par catégorie"
                    onCurrentTextChanged: window.clearSelection()
                    background: Rectangle {
                        radius: 12
                        color: window.themeColors.surface
                        border.color: categoryFilter.activeFocus || categoryFilter.hovered
                                      ? window.accentA : window.themeColors.border
                    }
                    contentItem: Label {
                        leftPadding: 14
                        rightPadding: 30
                        text: categoryFilter.displayText
                        color: window.themeColors.text
                        font.pixelSize: 12
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                    indicator: Label {
                        x: categoryFilter.width - width - 13
                        y: (categoryFilter.height - height) / 2
                        text: "⌄"
                        color: window.cyan
                        font.pixelSize: 16
                    }
                }
                Button {
                    id: clearFiltersButton
                    text: "EFFACER"
                    visible: searchField.text.length > 0 || categoryFilter.currentText !== "Toutes"
                    enabled: visible && !store.busy
                    Accessible.name: "Effacer la recherche et le filtre de catégorie"
                    onClicked: window.clearFilters()
                    background: Rectangle {
                        radius: 10
                        color: clearFiltersButton.activeFocus || clearFiltersButton.hovered
                               ? window.themeColors.surface_elevated : "transparent"
                        border.width: clearFiltersButton.activeFocus ? 2 : 1
                        border.color: clearFiltersButton.activeFocus ? window.themeColors.text
                                       : clearFiltersButton.hovered ? window.accentA : window.themeColors.border
                    }
                    contentItem: Label {
                        text: clearFiltersButton.text
                        color: clearFiltersButton.enabled ? window.themeColors.text : window.muted
                        font.pixelSize: 10
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                        rightPadding: 10
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 16

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumWidth: 0
                    radius: 17
                    color: window.themeColors.surface
                    border.color: window.themeColors.border

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 9

                        RowLayout {
                            Layout.fillWidth: true
                            Label {
                                text: "EXPLORER LE CATALOGUE"
                                color: window.muted
                                font.pixelSize: 9
                                font.weight: Font.Bold
                                font.letterSpacing: 1.8
                            }
                            Item { Layout.fillWidth: true }
                            Label {
                                text: window.visibleApplicationCount() + " / " + catalogModel.rowCount() + " APPLICATIONS"
                                color: window.themeColors.muted_text
                                font.pixelSize: 8
                                font.letterSpacing: 0.8
                            }
                        }

                        ListView {
                            id: appList
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            spacing: 7
                            model: catalogModel
                            enabled: !store.busy
                            currentIndex: window.selectedRow
                            Accessible.role: Accessible.List
                            Accessible.name: "Catalogue d'applications LEOS"
                            Accessible.description: "Sélectionne une application pour afficher sa fiche et l'action disponible."
                            keyNavigationEnabled: true
                            boundsBehavior: Flickable.StopAtBounds
                            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                            delegate: Rectangle {
                                required property string appId
                                required property string name
                                required property string category
                                required property string description
                                required property string source
                                required property string compatibility
                                required property string operationNote
                                required property bool installed
                                required property string installedScope
                                required property bool bundled
                                required property int index

                                width: ListView.view.width
                                height: visible ? 84 : 0
                                visible: (categoryFilter.currentText === "Toutes" || category === categoryFilter.currentText)
                                    && window.matchesSearch(name, appId, category, description, source, compatibility, operationNote)
                                radius: 12
                                gradient: Gradient {
                                    GradientStop {
                                        position: 0.0
                                        color: window.selectedRow === index
                                            ? Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.13)
                                            : appRowButton.hovered || appRowButton.activeFocus
                                                ? window.themeColors.surface_elevated
                                                : window.themeColors.surface
                                    }
                                    GradientStop { position: 1.0; color: window.themeColors.surface }
                                }
                                border.width: window.selectedRow === index ? 1.5 : 1
                                border.color: window.selectedRow === index ? window.accentA
                                              : appRowButton.activeFocus ? window.themeColors.text
                                              : appRowButton.hovered ? window.themeColors.muted_text
                                              : window.themeColors.border
                                Behavior on border.color { ColorAnimation { duration: 130 } }

                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.top: parent.top
                                    anchors.bottom: parent.bottom
                                    width: window.selectedRow === index ? 3 : 0
                                    radius: 2
                                    color: window.accentA
                                }

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 14
                                    anchors.rightMargin: 12
                                    spacing: 12

                                    Rectangle {
                                        Layout.preferredWidth: 42
                                        Layout.preferredHeight: 42
                                        radius: 12
                                        gradient: Gradient {
                                            GradientStop {
                                                position: 0.0
                                                color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.17)
                                            }
                                            GradientStop {
                                                position: 1.0
                                                color: Qt.rgba(window.accentB.r, window.accentB.g, window.accentB.b, 0.10)
                                            }
                                        }
                                        border.color: window.themeColors.border
                                        Label {
                                            anchors.centerIn: parent
                                            text: name.length ? name.substring(0, 1).toUpperCase() : "L"
                                            color: window.themeColors.text
                                            font.pixelSize: 19
                                            font.weight: Font.Bold
                                        }
                                    }

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 4
                                        Label {
                                            text: name
                                            color: window.themeColors.text
                                            font.pixelSize: 13
                                            font.weight: Font.DemiBold
                                            Layout.fillWidth: true
                                            elide: Text.ElideRight
                                        }
                                        Label {
                                            text: category + "  ·  " + source
                                            color: window.muted
                                            font.pixelSize: 10
                                            Layout.fillWidth: true
                                            elide: Text.ElideRight
                                        }
                                    }

                                    Rectangle {
                                        radius: 8
                                        implicitWidth: stateLabel.implicitWidth + 18
                                        implicitHeight: 27
                                        color: installed
                                            ? Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.10)
                                            : Qt.rgba(window.themeColors.muted_text.r,
                                                      window.themeColors.muted_text.g,
                                                      window.themeColors.muted_text.b, 0.07)
                                        border.color: installed ? Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.32)
                                                                : window.themeColors.border
                                        Label {
                                            id: stateLabel
                                            anchors.centerIn: parent
                                            text: installedScope === "system" ? (bundled ? "INCLUSE LEOS" : "SYSTÈME")
                                                  : installed ? "INSTALLÉE" : "DISPONIBLE"
                                            color: installed ? window.cyan : window.muted
                                            font.pixelSize: 8
                                            font.weight: Font.DemiBold
                                            font.letterSpacing: 0.5
                                        }
                                    }
                                }

                                Button {
                                    id: appRowButton
                                    anchors.fill: parent
                                    activeFocusOnTab: true
                                    Accessible.role: Accessible.Button
                                    Accessible.name: name + (installed ? ", installée" : ", disponible")
                                    Accessible.description: category + ". Source " + source + ". Activer pour ouvrir la fiche."
                                    Accessible.selected: window.selectedRow === index
                                    background: Item { }
                                    contentItem: Item { }
                                    onClicked: window.selectApp(index, appId, name, category, description, source,
                                                                compatibility, operationNote, installed,
                                                                installedScope, bundled)
                                }
                            }

                            Label {
                                anchors.centerIn: parent
                                visible: window.visibleApplicationCount() === 0
                                width: parent.width - 44
                                horizontalAlignment: Text.AlignHCenter
                                text: store.busy ? "Chargement du catalogue…"
                                      : catalogModel.rowCount() === 0
                                          ? "Le catalogue LEOS n'est pas disponible."
                                          : "Aucun résultat pour ces filtres. Efface la recherche ou choisis une autre catégorie."
                                color: window.muted
                                font.pixelSize: 12
                            }
                        }
                    }
                }

                Rectangle {
                    id: detailsPane
                    property string appId: ""
                    property string appName: "Choisis une application"
                    property string appCategory: ""
                    property string appDescription: "Les détails et les opérations apparaîtront ici."
                    property string appSource: ""
                    property string appCompatibility: ""
                    property string operationNote: ""
                    property bool isInstalled: false
                    property string installedScope: ""
                    property bool bundled: false
                    Layout.preferredWidth: window.width < 1080 ? 300 : 360
                    Layout.minimumWidth: 280
                    Layout.fillHeight: true
                    radius: 17
                    color: window.themeColors.surface
                    border.color: window.themeColors.border

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 11

                        RowLayout {
                            Layout.fillWidth: true
                            Label {
                                text: "FICHE APPLICATION"
                                color: window.cyan
                                font.pixelSize: 9
                                font.weight: Font.Bold
                                font.letterSpacing: 1.7
                            }
                            Item { Layout.fillWidth: true }
                            Label {
                                text: detailsPane.appId.length > 0 ? "DÉTAILS" : "EN ATTENTE"
                                color: window.muted
                                font.pixelSize: 8
                                font.letterSpacing: 1
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 104
                            radius: 14
                            gradient: Gradient {
                                GradientStop {
                                    position: 0.0
                                    color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.11)
                                }
                                GradientStop {
                                    position: 1.0
                                    color: Qt.rgba(window.accentB.r, window.accentB.g, window.accentB.b, 0.045)
                                }
                            }
                            border.color: window.themeColors.border
                            Label {
                                anchors.centerIn: parent
                                text: detailsPane.appName.length > 0
                                      ? detailsPane.appName.substring(0, 1).toUpperCase() : "L"
                                color: window.themeColors.text
                                font.pixelSize: 42
                                font.weight: Font.Light
                            }
                        }

                        Label {
                            text: detailsPane.appName
                            color: window.themeColors.text
                            font.pixelSize: 21
                            font.weight: Font.Bold
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Label {
                            text: detailsPane.appCategory.length > 0
                                  ? detailsPane.appCategory + "  ·  " + detailsPane.appSource
                                  : "Sélectionne une application dans le catalogue"
                            color: window.muted
                            font.pixelSize: 10
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                        }
                        Label {
                            text: detailsPane.appDescription
                            color: window.themeColors.text
                            opacity: 0.86
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: window.themeColors.border
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: window.themeColors.border
                        }
                        Label {
                            text: "IDENTIFIANT"
                            color: window.cyan
                            font.pixelSize: 8
                            font.weight: Font.Bold
                            font.letterSpacing: 1.3
                        }
                        Label {
                            text: detailsPane.appId || "—"
                            color: window.themeColors.muted_text
                            font.pixelSize: 10
                            wrapMode: Text.WrapAnywhere
                            Layout.fillWidth: true
                        }
                        Label {
                            text: "COMPATIBILITÉ"
                            color: window.cyan
                            font.pixelSize: 8
                            font.weight: Font.Bold
                            font.letterSpacing: 1.3
                        }
                        Label {
                            text: detailsPane.appCompatibility.length > 0
                                  ? detailsPane.appCompatibility : "Les informations de compatibilité s’afficheront avec la sélection."
                            color: window.muted
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        Label {
                            text: detailsPane.operationNote
                            color: window.muted
                            font.pixelSize: 9
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                            visible: detailsPane.operationNote.length > 0
                        }

                        Rectangle {
                            visible: detailsPane.installedScope === "system"
                            Layout.fillWidth: true
                            Layout.preferredHeight: visible ? 58 : 0
                            radius: 10
                            color: Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, 0.07)
                            border.color: window.themeColors.border
                            Label {
                                anchors.fill: parent
                                anchors.margins: 10
                                text: "Installée pour tout le système. Sa désinstallation peut demander une autorisation administrateur."
                                color: window.cyan
                                font.pixelSize: 9
                                wrapMode: Text.WordWrap
                                verticalAlignment: Text.AlignVCenter
                            }
                        }

                        Item { Layout.fillHeight: true }

                        Button {
                            id: installRemoveButton
                            Layout.fillWidth: true
                            implicitHeight: 48
                            enabled: detailsPane.appId.length > 0 && !store.busy
                            text: detailsPane.isInstalled ? "DÉSINSTALLER" : "INSTALLER"
                            Accessible.name: detailsPane.isInstalled ? "Désinstaller " + detailsPane.appName : "Installer " + detailsPane.appName
                            Accessible.description: "Une confirmation sera demandée avant toute modification."
                            onClicked: operationDialog.open()
                            background: Rectangle {
                                radius: 12
                                gradient: Gradient {
                                    GradientStop {
                                        position: 0.0
                                        color: installRemoveButton.enabled && !detailsPane.isInstalled
                                            ? Qt.rgba(window.accentA.r, window.accentA.g, window.accentA.b, installRemoveButton.down ? 0.20 : 0.30)
                                            : window.themeColors.surface_elevated
                                    }
                                    GradientStop {
                                        position: 1.0
                                        color: installRemoveButton.enabled && !detailsPane.isInstalled
                                            ? Qt.rgba(window.accentB.r, window.accentB.g, window.accentB.b, installRemoveButton.down ? 0.14 : 0.22)
                                            : window.themeColors.surface
                                    }
                                }
                                border.width: installRemoveButton.activeFocus ? 2 : 1
                                border.color: installRemoveButton.activeFocus ? window.themeColors.text
                                              : detailsPane.isInstalled ? window.themeColors.border : window.accentA
                            }
                            contentItem: Label {
                                text: installRemoveButton.text
                                color: installRemoveButton.enabled ? window.themeColors.text : window.muted
                                font.pixelSize: 11
                                font.weight: Font.Bold
                                letterSpacing: 1
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Label {
                    text: store.status
                    color: window.muted
                    font.pixelSize: 10
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }
                BusyIndicator {
                    running: store.busy
                    visible: store.busy
                    implicitWidth: 26
                    implicitHeight: 26
                }
            }
        }
    }

    Dialog {
        id: operationDialog
        title: detailsPane.isInstalled ? "Confirmer la désinstallation" : "Confirmer l'installation"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Cancel
        width: 480
        background: Rectangle {
            radius: 16
            color: window.themeColors.surface
            border.color: window.themeColors.border
        }

        ColumnLayout {
            width: parent.width
            spacing: 12
            Label {
                text: (detailsPane.isInstalled ? "Tu vas désinstaller " : "Tu vas installer ")
                      + detailsPane.appName + "."
                color: window.themeColors.text
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                text: "Identifiant : " + detailsPane.appId + "\nSource : " + detailsPane.appSource
                color: window.muted
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                text: detailsPane.isInstalled
                    ? (detailsPane.installedScope === "system" ? "L'application sera retirée de l'installation système. Une autorisation administrateur peut être demandée. Les données personnelles ne sont pas supprimées automatiquement." : "L'application sera retirée du profil utilisateur. Les données personnelles ne sont pas supprimées automatiquement.")
                    : "LEOS vérifiera d'abord la disponibilité sur Flathub. Flatpak pourra installer les dépendances et runtimes nécessaires."
                color: window.muted
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Button {
                text: "CONFIRMER"
                Layout.fillWidth: true
                implicitHeight: 42
                onClicked: {
                    operationDialog.close()
                    if (detailsPane.isInstalled)
                        store.requestUninstall(window.selectedRow)
                    else
                        store.requestInstall(window.selectedRow)
                }
            }
        }
    }

    Connections {
        target: store
        function onOperationFinished(success, message) {
            if (!success || !message.includes("disponible sur Flathub"))
                return
            verifyDialog.open()
        }
        function onCatalogUpdated() {
            if (window.selectedRow < 0)
                return
            const item = store.catalogItem(window.selectedRow)
            if (!item)
                return
            detailsPane.isInstalled = item.installed_scope !== ""
            detailsPane.installedScope = item.installed_scope
        }
    }

    Dialog {
        id: verifyDialog
        title: "Source vérifiée"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Cancel
        width: 440
        background: Rectangle {
            radius: 16
            color: window.themeColors.surface
            border.color: window.themeColors.border
        }
        ColumnLayout {
            width: parent.width
            Label {
                text: "Flathub confirme que " + detailsPane.appName + " est disponible. Confirmer maintenant son installation ?"
                color: window.themeColors.text
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Label {
                text: store.verificationDetails
                color: window.muted
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
            Button {
                text: "INSTALLER MAINTENANT"
                Layout.fillWidth: true
                implicitHeight: 42
                onClicked: {
                    verifyDialog.close()
                    store.confirmInstall(window.selectedRow)
                }
            }
        }
    }

    Component.onCompleted: {
        if (Qt.application.arguments.includes("--debug"))
            console.log("LEOS Store started")
    }
}
