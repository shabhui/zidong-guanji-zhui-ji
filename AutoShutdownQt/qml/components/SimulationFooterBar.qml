import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property string taskTitle: "Simulation task"
    property string remainingTime: "--:--:--"
    property string simulationState: "stopped"
    property string dateTimeText: "--"

    readonly property string normalizedState: {
        var state = simulationState.toLowerCase()
        return state === "running" || state === "paused" ? state : "stopped"
    }
    readonly property color stateColor: normalizedState === "running" ? "#58E6A4"
                                      : normalizedState === "paused" ? "#FFC75D"
                                      : "#8298AA"
    readonly property string stateLabel: normalizedState === "running" ? "Running"
                                       : normalizedState === "paused" ? "Paused"
                                       : "Stopped"

    signal startRequested()
    signal pauseResumeRequested()
    signal resetRequested()

    implicitWidth: 760
    implicitHeight: 66
    height: 66

    Rectangle {
        anchors.fill: parent
        anchors.margins: -1
        radius: 16
        color: "transparent"
        border.color: "#3849D9FF"
        border.width: 1
        opacity: 0.55
    }

    Rectangle {
        anchors.fill: parent
        radius: 15
        color: "#DE101D2D"
        border.color: "#8C4DDCFF"
        border.width: 1
        antialiasing: true
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 3
        radius: 12
        color: "#1A7DC8E8"
        border.color: "#3049D9FF"
        border.width: 1
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        anchors.topMargin: 10
        anchors.bottomMargin: 10
        spacing: 12

        Item {
            Layout.fillWidth: true
            Layout.preferredWidth: 250
            Layout.minimumWidth: 162
            Layout.maximumWidth: 300
            Layout.fillHeight: true

            RowLayout {
                anchors.fill: parent
                spacing: 9

                Rectangle {
                    Layout.alignment: Qt.AlignVCenter
                    Layout.preferredWidth: 10
                    Layout.preferredHeight: 10
                    radius: width / 2
                    color: root.stateColor

                    Rectangle {
                        anchors.centerIn: parent
                        width: 4
                        height: 4
                        radius: 2
                        color: "#EAFBFF"
                        opacity: 0.85
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1

                    Text {
                        Layout.fillWidth: true
                        text: root.taskTitle
                        color: "#F1FAFF"
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                        maximumLineCount: 1
                    }

                    Text {
                        Layout.fillWidth: true
                        text: root.stateLabel + "  ·  " + root.remainingTime + " remaining"
                        color: "#A8C0D0"
                        font.pixelSize: 11
                        elide: Text.ElideRight
                        maximumLineCount: 1
                    }
                }
            }
        }

        RowLayout {
            id: controlsRow

            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
            Layout.minimumWidth: implicitWidth
            spacing: 8

            NeonButton {
                text: "Start"
                variant: root.normalizedState === "stopped" ? "primary" : "secondary"
                compact: true
                enabled: root.normalizedState === "stopped"
                onClicked: root.startRequested()
            }

            NeonButton {
                text: root.normalizedState === "paused" ? "Resume" : "Pause"
                variant: root.normalizedState === "paused" ? "primary" : "secondary"
                compact: true
                enabled: root.normalizedState !== "stopped"
                onClicked: root.pauseResumeRequested()
            }

            NeonButton {
                text: "Reset"
                variant: "ghost"
                compact: true
                onClicked: root.resetRequested()
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.preferredWidth: 164
            Layout.minimumWidth: 120
            Layout.maximumWidth: 184
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 1

                Text {
                    Layout.fillWidth: true
                    text: "LIVE TIME"
                    color: "#77CFE5"
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignRight
                    elide: Text.ElideRight
                }

                Text {
                    Layout.fillWidth: true
                    text: root.dateTimeText
                    color: "#E1F6FF"
                    font.pixelSize: 12
                    font.weight: Font.Medium
                    horizontalAlignment: Text.AlignRight
                    elide: Text.ElideLeft
                    maximumLineCount: 1
                }
            }
        }
    }
}
