### Release Notes - v1.3.1

#### 🐛 Bug Fixes
*   Fixed a critical issue that caused the application to crash when loading a saved mission from an external file. The application is now more robust and can handle mission files from any location, allowing for seamless integration with third-party targeting data from command.
*   Resolved a `NameError` that occurred when drawing placeholder pins on the map before a map image was loaded.
*   Corrected an issue where the executable would not include necessary data files (maps and map configurations), causing errors when running the bundled application.

#### ✨ New Features
*   The "Save Mission File" and "Load Mission File" buttons have been updated to "Save Log As..." and "Load Log File" respectively, and now save and load the entire fire mission log.