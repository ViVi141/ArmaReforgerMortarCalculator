### Release Notes - v1.4.0

#### ✨ New Features
*   **Faction Support:** Added a faction selection system to the UI, allowing users to switch between NATO and RU mortar systems.
*   **RU Ballistics:** Integrated a complete set of ballistic data for the Russian 2B14 Podnos mortar and its associated ammunition.
*   **Dynamic UI:** The ammunition dropdown now dynamically updates to show the correct ammunition types based on the selected faction.
*   **UI Resizing:** The main application window now scales correctly, eliminating empty space and ensuring a consistent appearance when resized.

#### 🐛 Bug Fixes
*   **Azimuth Calculation:** Corrected the azimuth calculation to use the appropriate mil system for each faction (6400 for NATO, 6000 for RU).
*   **Mission Loading:** Fixed a bug that caused a crash when calculating a solution immediately after loading a mission from the log.
*   **Error Handling:** Improved UI feedback for out-of-range calculation errors, providing clear messages to the user.
*   **Executable Resources:** Resolved an issue where map images and configuration files were not correctly bundled with the executable, ensuring the standalone application runs as intended.

#### 🤖 Roo's Notes
*   This was a significant update that involved a deep dive into the application's core logic and UI structure. The iterative testing process was crucial for identifying and resolving several subtle but critical bugs. The application is now more robust and feature-complete.
