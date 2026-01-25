# Blender Feather 🪶

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Blender Feather** is an experimental Python script designed to reduce the size of `.blend` files. It automates the process of removing unused data and can optionally rebuild the file structure to achieve maximum lightweighting.

> [!WARNING]
> This is an **experimental** tool, it is **not** actively developed and it will **not** be polished or made user-friendly.
> It runs **without** a GUI and has no safety checks.
> Large parts of the code were written with the help of **AI**.
> The goal was exploration, not production-quality software.

---

## Capabilities

The script processes files in the background using your installed Blender version. It offers three levels of lightweighting:

* **Level 1 (Safe):** Purges orphan data.
* **Level 2 (Moderate):** Level 1 + removes unused brushes, palettes, and line styles.
* **Level 3 (Aggressive):** Recreates the file by appending collections and objects into a fresh `.blend` file. This is the most effective but destructive method.

---

## How to Use

1.  Ensure you have **Python 3.10+** and **Blender** installed.
2.  Open the `blender_feather.py` file in a code (text) editor and update the `BLENDER_VERSIONS` configuration list with the paths to your Blender executables.
3.  Run the `blender_feather.py`
4.  Drag and drop your target `.blend` file into the window and follow the prompts.

The processed file will be saved as `{filename}_L{level}.blend`.

---

## License

This project is distributed under the **MIT License**