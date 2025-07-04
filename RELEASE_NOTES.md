### Release Notes - v1.3.0

#### ✨ New Features
*   **Multi-Gun Fire Missions:** The calculator now supports up to four mortar tubes for coordinated fire missions.
*   **Advanced Fire Mission Types:**
    *   **Small Barrage:** Calculates a barrage prioritizing the rounds with the smallest dispersion radius for maximum precision.
    *   **Large Barrage:** Calculates a barrage prioritizing the rounds with the largest dispersion radius for maximum area coverage.
    *   **Creeping Barrage:** Calculates a sequential barrage where each round lands a set distance from the last, in a user-defined direction.
*   **Enhanced Map Visuals:**
    *   The map now displays unique, color-coded icons for each mortar tube.
    *   Dispersion radii are now visualized on the map:
        *   **Regular:** A red inner circle for the "Kill Area" (least ToF) and a yellow outer circle for the "Expected Injury Area" (most ToF).
        *   **Barrage:** A single, solid circle representing the dispersion of the chosen round.
        *   **Creeping Barrage:** A bounding box that encloses the entire barrage area.
*   **Improved UI:**
    *   The main UI sections have been renumbered for a more logical workflow.
    *   The 'Fire Mission' section has been rearranged for a more balanced and intuitive layout.
    *   The "Calculate Firing Solution" button has been moved to a more central and accessible location.
    *   The mortar inputs are now arranged in a two-column layout to save space and prevent scrolling.
    *   The "Quick Fire Data" section now displays information for each gun in a horizontal layout.
    *   Mortar positions can now be locked to prevent accidental changes.
    *   The fire mission type is now selected with radio buttons for easier use.
*   **Saved Mission Enhancements:**
    *   Saved missions now include all data for multi-gun and advanced fire missions.
    *   When a mission is loaded, the target's location is now displayed on the map with a toggle to show or hide it.

#### 🐛 Bug Fixes
*   **Map Visualization:** Corrected the rendering logic to ensure that dispersion radii for all mortars in a regular fire mission are now correctly displayed on the map. Regular fire missions now display a single target marker, with dispersion radii for each mortar color-coded to its respective gun.
*   Fixed an issue where the application would crash when loading a saved mission.
*   Corrected the logic for small and large barrages to properly prioritize dispersion radius.
*   When loading a saved mission, the fire mission type is now cleared, and the mortar lock status is correctly applied.
*   Selecting a new fire mission type no longer triggers an automatic recalculation.
*   The main application window now opens centered with consistent padding, regardless of whether the scrollbar is visible.