# Plan for Application Improvements

This document outlines the plan to enhance the Arma Reforger Mortar Calculator application.

### 1. Restructure the UI with Tabs

*   Introduce a `ttk.Notebook` widget to create a tabbed interface.
*   Create two tabs: "Main" and "Settings".
*   Move the existing input fields, results display, and map canvas to the "Main" tab.
*   Move the "Upload Map" button and the theme toggle button to the "Settings" tab.

### 2. Enhance the Settings Tab

*   Add a new input field for "Uploaded Map Size" to the "Settings" tab. This will allow the user to specify the dimensions of the map in meters.
*   Add a duplicate of the dark/light mode toggle to the "Settings" tab for convenience.

### 3. Improve Map Interaction and Pin Placement

*   Modify the `plot_positions` function to use the user-defined map size for accurate scaling of the pins on the map.
*   After the initial calculation, automatically zoom and center the map to provide a clear view of the mortar, FO, and target pins.
*   The pins will remain locked to their geographical coordinates during panning and zooming.

### UI Structure Diagram

```mermaid
graph TD
    A[Mortar Calculator] --> B{ttk.Notebook};
    B --> C[Main Tab];
    B --> D[Settings Tab];

    C --> E[Input Frame];
    C --> F[Results Frame];
    C --> G[Map Canvas];

    D --> H[Upload Map Button];
    D --> I[Theme Toggle Button];
    D --> J[Map Size Input];

### 4. Deployment

*   After the implementation is complete and tested, the changes will be committed and pushed to the GitHub repository using the `gh` command-line interface.