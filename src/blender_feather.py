import os, subprocess, re
from pathlib import Path

# Add your Blender versions here
BLENDER_VERSIONS = {
    "3.6": r"E:\blender launcher\stable\blender-3.6.22-lts.30b431ea75f7\blender.exe",
    "4.0": r"E:\blender launcher\stable\blender-4.0.2-stable.9be62e85b727\blender.exe",
    "4.1": r"E:\blender launcher\stable\blender-4.1.1-stable.e1743a0317bc\blender.exe",
    "4.2": r"E:\blender launcher\stable\blender-4.2.16-lts.39502cae951c\blender.exe",
    "4.5": r"E:\blender launcher\stable\blender-4.5.5-lts.836beaaf597a\blender.exe",
    "5.0": r"E:\blender launcher\stable\blender-5.0.1-stable.a3db93c5b259\blender.exe",
}


def parse_filepath(raw):
    """Removes quotes from path"""
    return raw.strip().strip('"').strip("'")


def get_blend_version(filepath, blender_exec):
    """Dynamically get Blender version using binary header inspection or fallback to latest Blender"""
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(24)
            
            header_text = chunk[7:].decode('ascii', errors='ignore')
            
            match = re.search(r'(\d+)', header_text)
            
            if match:
                ver_str = match.group(1)
                
                if len(ver_str) >= 3:
                    major = ver_str[:-2]
                    minor = int(ver_str[-2:])
                    return f"{major}.{minor}"
            
            script = 'import bpy; print(f"V:{bpy.data.version[0]}.{bpy.data.version[1]}")'
            temp = "temp_version.py"

            with open(temp, "w", encoding="utf-8") as f:
                f.write(script)
            
            result = subprocess.run(
                [blender_exec, "-b", filepath, "-P", temp],
                capture_output=True, text=True, timeout=60
            )
            for line in result.stdout.splitlines():
                if "V:" in line:
                    return line.split("V:")[1].strip()
            
            if os.path.exists(temp):
                os.remove(temp)

            return "Unknown"
                
    except subprocess.TimeoutExpired:
        return "Timeout, try later maybe"
    except Exception as e:
        return f"Error: {e}"


def choose_blender():
    """Select Blender version"""
    versions = [(ver, path) for ver, path in BLENDER_VERSIONS.items() if os.path.exists(path)]
    print("\nAvailable versions:")
    for i, (ver, _) in enumerate(versions, 1):
        print(f"{i}. Blender {ver}")
    
    while True:
        choice = input(f"\nSelect version (1-{len(versions)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(versions):
            return versions[int(choice) - 1][1]
        print("Invalid choice")


def process_file(filepath, level, compress, delete_worlds, exp_append, blender_exec):
    """Processes .blend file through Blender"""
    temp = "temp_process.py"
    
    # Script is located next to the launcher
    script_path = Path(__file__).resolve().parent / "blender_feather_script.py"
    if not script_path.exists():
        print("Error: blender_feather_script.py not found")
        return

    # Read script and inject parameters
    script = script_path.read_text(encoding="utf-8")
    script = (script
        .replace("{{LEVEL}}", str(level))
        .replace("{{FILEPATH}}", filepath.replace("\\", "/"))
        .replace("{{COMPRESS}}", str(compress))
        .replace("{{DELETE_WORLDS}}", str(delete_worlds))
        .replace("{{EXP_APPEND}}", str(exp_append))
    )

    with open(temp, "w", encoding="utf-8") as f:
        f.write(script)
    
    print(f"\nProcessing (Level {level})...")
    
    try:
        result = subprocess.run(
            [blender_exec, "-b", filepath, "-P", temp],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("\nComplete!")
            # Find saved file path
            for line in result.stdout.splitlines():
                if "Saved:" in line:
                    print(line)
        else:
            print("\nBlender error:")
            print(result.stderr[-1000:])
            print(result.stdout[-500:])

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Cleanup temp files
        if os.path.exists(temp):
            os.remove(temp)
        
        # Level 3 creates .temp.blend - remove it
        temp_blend = filepath + ".temp.blend"
        if os.path.exists(temp_blend):
            try:
                os.remove(temp_blend)
            except PermissionError:
                print(f"Could not delete {temp_blend}")


def main():
    print("=== Blender Feather #23 ===")
    
    while True:
        filepath = parse_filepath(input("\nDrag .blend file: "))
        
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
        if not filepath.lower().endswith('.blend'):
            print("Not a .blend file")
            continue
        
        # Detect file version (using latest Blender)
        print("\nDetecting file version...")
        latest = BLENDER_VERSIONS[sorted(BLENDER_VERSIONS.keys())[-1]]
        version = get_blend_version(filepath, latest)
        print(f"File saved in Blender {version}")
        
        blender_exec = choose_blender()
        
        print("\nLightweighting levels:")
        print("1. Purge (remove unused data)")
        print("2. Level 1 + remove brushes, palettes, line styles")
        print("3. Level 2 + remove fake users + rebuild via Append")
        
        choice = input("\nLightweighting Level (1-3): ").strip()
        while choice not in ['1', '2', '3']:
            choice = input("Lightweighting Level (1-3): ").strip()
        
        delete_worlds = input("\nDelete world materials? (y/n): ").strip().lower() in ['y', 'yes', ""]

        exp_append = False
        if choice == '3':
            exp_append = input("Enable experimental Scene Collection object append? (y/n): ").strip().lower() in ['y', 'yes']

        compress = input("Compress file? (y/n): ").strip().lower() in ['y', 'yes']
        
        process_file(filepath, int(choice), compress, delete_worlds, exp_append, blender_exec)

        print("\n=== Done ===")

if __name__ == "__main__":
    main()