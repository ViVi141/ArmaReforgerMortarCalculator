### Release Notes - v1.3.3 (Future)

#### ✨ New Features
*   **Scroll Wheel Navigation:** The mouse scroll wheel now works on the main application canvas, allowing for easier navigation of the UI.
*   **Adjustable Creeping Barrage:** Added a slider to control the spread of the creeping barrage, allowing for more tactical flexibility.

#### 🐛 Bug Fixes
*   **File Permissions:** Fixed a `PermissionError` that occurred when launching the application from "Recent Apps" by ensuring all file paths are absolute.
*   **Window Position:** Corrected the initial window position to prevent the application from opening partially off-screen.
*   **Fullscreen Display:** Resolved an issue where white bars would appear when the application was in fullscreen mode.
*   **Application Stability:** Fixed a bug that caused the application to hang after long periods of inactivity by implementing a more robust event system for thread communication.
*   **Map Change Stability:** Fixed a bug where changing the map after a calculation would cause the application to become unresponsive. The application state is now properly reset when a new map is selected.

#### 🤖 Roo's Notes
*   