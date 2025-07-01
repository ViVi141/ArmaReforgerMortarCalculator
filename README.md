# Arma Reforger Mortar Calculator

A mortar calculator for Arma Reforger designed to assist with indirect fire missions.

## How to Use

### Requirements
*   **Mortar Team:** 1-3 players
*   **Forward Observer (FO):** 1-2 players in a reconnaissance role

### Step 1: Mortar Position
1.  **Get Mortar Coordinates:**
    *   As a member of the mortar team, open the mortar sight and use the in-game DAGR to get a precise 10-digit grid coordinate.
    *   **Note on Grids:** An 8-digit grid can be converted to a 10-digit grid by adding a zero after the fourth digit of both the easting and northing (e.g., `1234 1234` becomes `12340 12340`). The calculator expects the easting (X-axis, left/right) first, then the northing (Y-axis, up/down).
2.  **Get Mortar Elevation:**
    *   Your elevation can be found on the DAGR, usually located beneath the grid coordinates.

### Step 2: Forward Observer & Target Data
1.  **Get FO and Target Data:**
    *   The Forward Observer should acquire their own 10-digit grid and elevation.
    *   Using the Vector 21 binoculars is recommended for acquiring target data, but manual calculation is also possible.
2.  **Acquire Target Range and Elevation Change:**
    *   Press and release `R`, then press and hold `R` again. This will display the range to the target on the left and the elevation difference on the right.
3.  **Acquire Target Azimuth:**
    *   Press and hold `V` until a vector appears. If two vectors are displayed, use the one on the left.
    *   **Tip:** Remember **R** for **R**ange and **V** for **V**ector.

### Step 3: Fire Mission
1.  **Ammunition:** Select the appropriate ammo type from the dropdown menu.
2.  **Calculate:** Click the "Calculate Firing Solution" button.
3.  **Verify:** Cross-reference the visual representation on the right with the actual battlefield to ensure the Mortar, FO, and Target positions are similar. Proceed with caution if they differ significantly.
4.  **Aiming:**
    *   Find the **"Mortar-Target Azimuth"** in the "Calculated Target Details" section. This is the MIL value you will use for the horizontal dial on the mortar sight.
    *   In the "Final Firing Solution" section, find the **"Corrected Elevation"** for your chosen charge. This is the MIL value for the vertical dial on the mortar sight.
    *   **Tactical Tip:** For a rapid barrage, you can fire the charge with the most time of flight first, then switch to the charge with the least time of flight. After about half the time has elapsed for the first round, begin firing the faster rounds. This gives the FO time to call for corrections while still delivering a high volume of fire.
5.  **Log Mission:** Give the mission a name and click "Log Current Mission" to save it for later. You can reload and adjust missions as needed.

### Current Status & Notes

*   **Fire Mission Corrections:** This feature is currently a work in progress and may not be reliable.
*   **Map Upload:** A map upload is not required for the visual representation to work. A map is primarily for checking accuracy. All items on the map could be +/- several meters if the map is not a perfect square or if the scale is set up incorrectly. A future update will allow for individual X and Y limits to be set.