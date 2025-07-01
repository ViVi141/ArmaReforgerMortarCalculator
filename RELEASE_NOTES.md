### Release Notes - v1.1.4

This release introduces a powerful new map management system, a new fire mission correction system, and other quality-of-life improvements.

#### ✨ New Features

*   **Advanced Map Management:**
    *   **Map Selection:** A new dropdown in the settings panel allows you to switch between preloaded and custom-uploaded maps.
    *   **Custom Map Dimensions:** The calculator now supports rectangular maps. You can set custom X and Y dimensions for each map.
    *   **Persistent Custom Maps:** Uploaded maps and their dimensions are now saved and will be automatically available the next time you launch the application.
    *   **Preloaded Maps:** The application now comes preloaded with configurations for Zarichne, Serhiivka, Everon, and Belleau Wood.
*   **Advanced Targeting Mode:** An advanced feature has been added for quickly setting a target's position by right-clicking directly on the map.
*   **Simplified Correction Inputs:** The correction input has been simplified to two fields: "Left/Right" and "Add/Drop".
*   **Automatic Correction Logic:** The application will now automatically test the four possible correction combinations (e.g., Left/Add, Right/Add, Left/Drop, Right/Drop) and apply the one that results in a target location closest to the original, uncorrected target.
*   **Save/Load Mission:** Users can now save the entire mission setup (Mortar, FO, Target positions, etc.) to a file and load it back into the application.
*   **Correction Fields Reset:** The correction input fields are now automatically zeroed out after a firing solution is calculated.
*   **Accurate FO Data:** After a correction is applied, the FO's azimuth and distance to the target are now updated to reflect the new, corrected target position, ensuring that saved missions are accurate.
*   **Default Map:** The application now loads a default map (`Zarichne.png`) from the `maps` folder on startup.

#### 🎨 UI Changes

*   The map settings panel has been redesigned for the new map management system.
*   The map selection dropdown menu is now correctly styled to match the application's theme.
*   The map now starts fully zoomed out and centered, filling the entire map view.
*   Placeholder pins for the mortar, FO, and target are now displayed vertically in the bottom-left corner of the map on startup.
*   Changed FO pin color to yellow and Target pin color to red for better visibility.
*   Pin labels are now always black for readability.

#### 🐛 Bug Fixes

*   Fixed a bug that caused a crash when loading a mission due to an undefined variable.
*   Fixed a visual bug where highlighted text did not have the correct background color.
*   Moved the "Save Mission" and "Load Mission" buttons to the mission log section for better organization.
*   Fixed a visual bug where highlighted fields would not display their borders correctly in dark mode.