### Release Notes - v1.3.2

#### ✨ New Features
*   **Show Logged Targets:** You can now display all targets from the mission log on the map at the same time, providing a complete tactical overview.
*   **Enhanced Map Visualization:** Target markers are now highlighted with a colored circle corresponding to the firing mortar, and locked input fields are color-coded to match their map icons, creating a more intuitive and visually cohesive experience.
*   **Multi-Mortar UI:** The user interface for managing multiple mortars has been streamlined. The control for selecting the number of mortars is now logically grouped with the mortar position inputs.

#### 🛠️ Refactoring
*   **Asynchronous Architecture:** Implemented a major performance enhancement by moving all firing solution calculations to a separate background thread. This ensures the user interface remains fluid and responsive, even during complex calculations, providing a much smoother user experience.
*   **Code Quality:** The `update_ui_with_solution` method in `main.py` has been refactored into smaller, more specialized functions to improve readability and maintainability.
*   **State Management:** Continued to centralize application state by moving all map-related variables to the `StateManager`. This improves code organization and maintainability.
*   **Barrage Logic:** The `calculate_small_barrage` and `calculate_large_barrage` functions have been refactored into a single, more generic function to reduce code duplication.

#### 🐛 Bug Fixes
*   **Locked Input Readability:** Fixed an issue where text in locked input fields was unreadable. The text is now white and clearly visible against the colored background.
*   **Barrage Logic:** Corrected the logic for "Small Barrage" and "Large Barrage" calculations. They now correctly prioritize the shortest and longest Time of Flight (ToF) respectively, as originally intended in the project plan.
*   **UI Rendering:** Fixed a visual bug that caused text to become garbled during fast scrolling in both the main input area and the mission log.
*   **Mission Log:** Fixed a critical bug where mortar positions were not being correctly saved to or loaded from mission log files.
*   Resolved an `AttributeError` that occurred after the state management refactoring.