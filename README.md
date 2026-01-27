# Blender Feather 🪶

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Blender Feather** is an experimental Python script designed to reduce the size of `.blend` files. It automates the process of removing unused data and can optionally rebuild the file structure to achieve maximum lightweighting.

> [!WARNING]
> This is an **experimental** tool. It runs **without** a GUI and has no safety checks.  
> Always keep a backup of your original file.

---

## Capabilities

The script processes files in the background using your installed Blender version.

### Lightweighting Levels
* **Level 1 (Safe):** Purges orphan data (runs recursively).
* **Level 2 (Moderate):** Level 1 + removes unused brushes, palettes, and line styles.
* **Level 3 (Aggressive):** Recreates the file by appending collections and objects into a fresh `.blend` file. This is the most effective but destructive method.

### Additional Options
* **Delete World Materials:** Removes World material
* **Experimental Append (Level 3):** Tries to rescue objects that are not linked to any collection, this will cause some bugs
* **Compression:** Enables blender compression for the saved file

---

## How to Use

1.  Ensure you have **Python 3.10+** and **Blender** installed.
2.  Open `blender_feather.py` and update `BLENDER_VERSIONS` with your paths.
3.  Run `blender_feather.py`.
4.  Drag and drop your target `.blend` file and follow the prompts.

The processed file will be saved as `{filename}_L{level}.blend`.