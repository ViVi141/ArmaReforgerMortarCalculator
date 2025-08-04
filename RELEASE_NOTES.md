### Release Notes - v1.4.2

#### ✨ New Features
*   **TRP Tab:** Introduced a new "TRP" tab for managing Target Reference Points.
    *   Users can add, remove, and clear TRPs with grid, elevation, and name.
    *   TRPs are displayed in a table with their calculation status (Solution Found, No Solution, Error).
    *   **TRP Details View:** Selecting a TRP in the list now displays its Grid, Elevation, Name/ID, and Status in a dedicated details panel.
*   **Batch TRP Calculation:** Implemented a "Calculate All TRPs" button on the TRP tab.
    *   Calculates solutions for all TRPs in the list using current mortar positions.
    *   Displays per-gun error messages for out-of-range or invalid solutions in the main UI's solution tabs and quick fire data.
    *   Logs only successfully calculated (green) TRP-mortar solutions as individual mission entries in the main "Fire Mission Log".
    *   Clears the in-memory mission log before batch calculation to show only current results (without affecting saved log files).
    *   **UI Performance Improvement:** Batch calculations now run more smoothly in the background, with only the TRP list status and mission log updating during the process. The map updates once at the end to show all calculated TRP targets.
*   **TRP Button on Main UI:** The TRP button has been added to the main UI for ease of access.
*   **Load TRPs from Log:** Added a "Load TRPs from Mission Log" button on the TRP tab.
    *   Allows importing TRP data from existing mission log files into the TRP list.
    *   Robustly handles various log formats and missing data.
*   **Load TRP from TRP List (Main Tab):** The "Load TRP from TRP List" button has been relocated from the TRP tab to the "3. Targeting Data" frame on the Main tab.
    *   It is now conditionally visible only when "Grid (TRP)" targeting mode is selected.
    *   Opens a pop-up dialog listing *all* TRPs from the currently loaded TRP list (regardless of calculation status).
    *   Selecting a TRP auto-fills its grid and elevation into the main UI's TRP input fields, sets the targeting mode to "Grid", and auto-calculates.
*   **Load TRP from Log (Main Tab):** Added a "Load TRP from Log" button to the "Quick Fire Data" section on the Main tab.
    *   Allows selecting any individual mission entry from the main mission log to populate the main UI's TRP input fields.
*   **TRPSelectDialog Scrolling:** The TRP selection pop-up dialog (`TRPSelectDialog`) now handles its own mouse wheel scrolling, preventing interference with the main application's scroll.
*   **Refined Map Display in TRP Mode:** The Forward Observer (FO) position is no longer plotted on the map when in "Grid (TRP)" targeting mode, providing a cleaner and more relevant view.
*   **Improved TRP Grid Formatting:** All TRP grid inputs and displays now consistently use a 10-digit format with leading zeros, improving data consistency and readability.
*   **Enhanced TRP List Visuals:** The "Solution Found" text in the TRP list now uses a more vibrant green in dark mode and black in light mode, improving visibility and contrast.
