import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"
import "pages"

Item {
    id: root
    property var rootWindow

    function syncDryRunSwitchState() { settingsPage.syncDryRunSwitchState() }

    Rectangle {
        anchors.fill: parent
        color: Theme.workspaceBackground

        Rectangle {
            anchors.fill: parent
            opacity: 0.22
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#18274D78" }
                GradientStop { position: 0.46; color: "#00050B16" }
                GradientStop { position: 1.0; color: "#1AFF6FAE" }
            }
        }
    }

    Rectangle {
        id: topBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 76
        color: Theme.workspaceTopbar

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 1
            color: Theme.workspaceBorder
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 28
            anchors.rightMargin: 18
            spacing: 14

            Item {
                Layout.preferredWidth: 242
                Layout.fillHeight: true

                Rectangle {
                    id: brandDiamond
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    width: 42
                    height: 42
                    rotation: 45
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: Theme.workspaceCyan }
                        GradientStop { position: 1.0; color: Theme.workspaceAccent }
                    }

                    Text {
                        anchors.centerIn: parent
                        rotation: -45
                        text: "时"
                        color: Theme.workspaceBackground
                        font.pixelSize: 17
                        font.weight: Font.Black
                    }
                }

                Column {
                    anchors.left: brandDiamond.right
                    anchors.leftMargin: 16
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 1

                    Text {
                        text: "定时关机助手"
                        color: Theme.workspaceInk
                        font.pixelSize: 18
                        font.weight: Font.Bold
                    }

                    Text {
                        text: "N I G H T   S H I F T"
                        color: Theme.workspaceMuted
                        font.pixelSize: 8
                        font.letterSpacing: 2
                    }
                }
            }

            RowLayout {
                id: topNavigation
                Layout.alignment: Qt.AlignVCenter
                spacing: 8

                Repeater {
                    model: root.rootWindow.workspaceNavItems

                    Item {
                        required property var modelData
                        required property int index
                        Layout.preferredWidth: Math.max(52, navLabel.implicitWidth + 24)
                        Layout.preferredHeight: 76

                        Text {
                            id: navLabel
                            anchors.centerIn: parent
                            text: modelData.label
                            color: root.rootWindow.currentPage === index ? Theme.workspaceInk : Theme.workspaceMuted
                            font.pixelSize: 13
                            font.weight: root.rootWindow.currentPage === index ? Font.Bold : Font.Medium
                        }

                        Rectangle {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            anchors.leftMargin: 8
                            anchors.rightMargin: 8
                            height: 2
                            visible: root.rootWindow.currentPage === index
                            gradient: Gradient {
                                orientation: Gradient.Horizontal
                                GradientStop { position: 0.0; color: Theme.workspaceCyan }
                                GradientStop { position: 1.0; color: Theme.workspaceAccent }
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.rootWindow.selectWorkspacePage(index)
                        }
                    }
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton
                    onPressed: root.rootWindow.startSystemMove()
                    onDoubleClicked: root.rootWindow.toggleMaximized()
                }
            }

            V5StatusPill {
                text: controller.dryRun ? "安全验证已开启" : "真实执行模式"
                accentColor: controller.dryRun ? Theme.workspaceSuccess : Theme.workspaceDanger
            }

            NeonButton {
                compact: true
                variant: "ghost"
                Layout.preferredWidth: 34
                text: "♪"
                onClicked: root.rootWindow.openMusicPlayer()
            }

            NeonButton {
                compact: true
                variant: "ghost"
                Layout.preferredWidth: 34
                text: "—"
                onClicked: root.rootWindow.showMinimized()
            }

            NeonButton {
                compact: true
                variant: "ghost"
                Layout.preferredWidth: 34
                text: root.rootWindow.visibility === Window.Maximized ? "▣" : "□"
                onClicked: root.rootWindow.toggleMaximized()
            }

            NeonButton {
                compact: true
                variant: "quietDanger"
                Layout.preferredWidth: 34
                text: "×"
                onClicked: root.rootWindow.close()
            }
        }
    }

    StackLayout {
        id: workspaceStack
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: topBar.bottom
        anchors.bottom: parent.bottom
        currentIndex: root.rootWindow.currentPage

        OverviewPage {
            rootWindow: root.rootWindow
        }

        Item {
            TimerPage {
                anchors.fill: parent
                anchors.margins: 24
                rootWindow: root.rootWindow
            }
        }

        Item {
            TasksPage {
                anchors.fill: parent
                anchors.margins: 24
                rootWindow: root.rootWindow
            }
        }

        Item {
            TriggersPage {
                anchors.fill: parent
                anchors.margins: 24
                rootWindow: root.rootWindow
            }
        }

        Item {
            ScriptPage {
                anchors.fill: parent
                anchors.margins: 24
                rootWindow: root.rootWindow
            }
        }

        Item {
            SettingsPage {
                id: settingsPage
                anchors.fill: parent
                anchors.margins: 24
                rootWindow: root.rootWindow
            }
        }
    }
}
