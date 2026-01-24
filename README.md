# Blender Feather 🪶

**Blender Feather** is a small experimental Python script for making `.blend` files lighter by removing unused data and optionally recreating the file structure.

> [!WARNING]
> This is **not** a finished product and never will be.  
> It has no safety checks, no GUI, and no protection from incorrect usage.  
> Use it only if you understand what you are doing.

---

## Project status

- This project is an **experiment**
- It is **not actively developed**
- It will **not** be polished or made user-friendly
- Large parts of the code were written with the help of **AI**
- The goal was exploration, not production-quality software

---

## What it does

- Runs Blender in background mode
- Performs file **lightweighting** using a selected level
- Saves the result as {ORIGINAL_FILE_NAME}_L{LIGHTWEIGHTING_LEVEL}.blend

---

## What it does NOT do

- No geometry optimization
- No texture or image compression
- No artistic or scene analysis
- No guarantees of correctness or safety

---

## Lightweighting levels

- **Level 1** — Orphan purge only   
(safe)
- **Level 2** — Level 1 + removal of brushes, palettes and line styles  
(safe in most cases)
- **Level 3** — Level 2 + file recreation via collections append  
(most effective, most destructive)

---

## Requirements

### Blender
- Any version that supports background execution
- Recommended:
- 3.6 LTS
- 4.5 LTS
- 5.0

### Python
- Tested on **Python 3.12**
- Other versions may work but are untested

---

## Setup

1. Install Python
2. Manually set paths to your Blender executables in `BLENDER_VERSIONS`  
 (you can add as many versions as you want)
3. Run `blender_feather.py`