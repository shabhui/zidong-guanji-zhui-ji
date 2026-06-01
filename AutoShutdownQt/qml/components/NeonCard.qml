import QtQuick
import ".."

Rectangle {
    property color cardBorderColor: Theme.borderSoft
    property color cardColor: Theme.surfaceGlass

    color: cardColor
    radius: Theme.radiusLg
    border.color: cardBorderColor
    border.width: 1

    Behavior on border.color {
        ColorAnimation { duration: Theme.animNormal }
    }
}
