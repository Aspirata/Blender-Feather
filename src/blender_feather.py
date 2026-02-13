import os, subprocess, re, atexit, tempfile, traceback
from pathlib import Path


# Add your Blender versions here
BLENDER_VERSIONS = {
    "3.6": r"E:\blender launcher\stable\blender-3.6.23-lts.e467db79ca8c\blender.exe",
    "4.0": r"E:\blender launcher\stable\blender-4.0.2-stable.9be62e85b727\blender.exe",
    "4.1": r"E:\blender launcher\stable\blender-4.1.1-stable.e1743a0317bc\blender.exe",
    "4.2": r"E:\blender launcher\stable\blender-4.2.17-lts.76b996a81c95\blender.exe",
    "4.4": r"E:\blender launcher\stable\blender-4.4.3-stable.802179c51ccc\blender.exe",
    "4.5": r"E:\blender launcher\stable\blender-4.5.6-lts.a78963ed6435\blender.exe",
    "5.0": r"E:\blender launcher\stable\blender-5.0.1-stable.a3db93c5b259\blender.exe",
}

TEMP_DIR = tempfile.gettempdir()

def delete_temp_files():
    """Remove temporary files created during version detection and processing"""
    temp_files = [
        Path(TEMP_DIR) / "blender_feather_temp_get_blender_version.py",
        Path(TEMP_DIR) / "blender_feather_temp_process_file.py"
    ]
    for temp_script_path in temp_files:
        try:
            os.remove(temp_script_path)
        except FileNotFoundError:
            pass
        except Exception:
            print(f"Could not delete {temp_script_path}: {traceback.format_exc()}")


def get_user_input(prompt: str, valid_responses: list[str | int | float], default_value: None | bool | str | int | float = None):
    """Get user input with validation and default option"""
    valid_responses = [str(response) for response in valid_responses]
    prompt += f" (valid responses: {', '.join(valid_responses)})"

    if default_value is not None:
        prompt += f" (default: {default_value})"

    while True:
        response = input(f"{prompt}: ").strip().lower()
        if response == "" and default_value:
            return default_value
        if response in valid_responses:
            return response
        print(f"Invalid input. Please enter one of: {', '.join(valid_responses)}")


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
            
            print("The file was compressed or saved in Blender 5.0+, this will take a while...")

            script = 'import bpy; print(f"V:{bpy.data.version[0]}.{bpy.data.version[1]}")'
            temp_script_path = Path(TEMP_DIR) / "blender_feather_temp_get_blender_version.py"

            with open(temp_script_path, "w", encoding="utf-8") as f:
                f.write(script)
            
            result = subprocess.run(
                [blender_exec, "-b", filepath, "-P", temp_script_path],
                capture_output=True, text=True, timeout=60
            )
            for line in result.stdout.splitlines():
                if "V:" in line:
                    return line.split("V:")[1].strip()

            return "Unknown"

    except subprocess.TimeoutExpired:
        return "Timeout, try later maybe"
    except Exception as e:
        return f"Error: {e}"


def choose_blender(file_version):
    """Select Blender version"""
    versions = [(ver, path) for ver, path in BLENDER_VERSIONS.items() if os.path.exists(path)]
    print("Available versions:")
    for i, (ver, _) in enumerate(versions, 1):
        print(f"{i}. Blender {ver}")

    default_blender_version = next((ver for ver, path in versions if ver == file_version), None)
    return versions[int(get_user_input("\nChoose Blender version", [i for i in range(1, len(versions) + 1)], default_blender_version)) - 1][1]


def process_file(filepath, lightweighting_level, do_compress, do_delete_worlds, do_experimental_append, blender_executable_path):
    """Processes .blend file through Blender"""
    temp_script_path = Path(TEMP_DIR) / "blender_feather_temp_process_file.py"
    
    # Script is located next to the launcher
    script_path = Path(__file__).resolve().parent / "blender_feather_script.py"
    if not script_path.exists():
        print("Error: blender_feather_script.py not found")
        return

    # Read script and inject parameters
    script = script_path.read_text(encoding="utf-8")
    script = (script
        .replace("{{LEVEL}}", str(lightweighting_level))
        .replace("{{FILEPATH}}", filepath.replace("\\", "/"))
        .replace("{{COMPRESS}}", str(do_compress))
        .replace("{{DELETE_WORLDS}}", str(do_delete_worlds))
        .replace("{{EXP_APPEND}}", str(do_experimental_append))
    )

    with open(temp_script_path, "w", encoding="utf-8") as f:
        f.write(script)
    
    try:
        result = subprocess.run(
            [blender_executable_path, "-b", filepath, "-P", temp_script_path],
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
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)
        
        # Level 3 creates .temp.blend - remove it
        temp_blend = filepath + ".temp.blend"
        if os.path.exists(temp_blend):
            try:
                os.remove(temp_blend)
            except PermissionError:
                print(f"Could not delete {temp_blend}")


def main():
    print("=== Blender Feather #24 ===")

    delete_temp_files()

    while True:
        filepath = input("\nDrag .blend file: ").strip().strip('"').strip("'")
        
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
        if not filepath.lower().endswith('.blend'):
            print("Not a .blend file")
            continue
        
        # Detect file version (using latest Blender)
        print("\nDetecting file version...")
        latest_blender_version = BLENDER_VERSIONS[sorted(BLENDER_VERSIONS.keys())[-1]]
        file_version = get_blend_version(filepath, latest_blender_version)
        print(f"\nFile saved in Blender {file_version}")
        
        blender_executable_path: str = choose_blender(file_version)
        
        print("\nLightweighting levels:")
        print("1. Purge (remove unused data)")
        print("2. Level 1 + remove brushes, palettes, line styles")
        print("3. Level 2 + remove fake users + rebuild via Append")
        
        lightweighting_level: int = int(get_user_input("\nChoose Lightweighting Level", [1, 2, 3], 1))
        
        do_delete_worlds: bool = get_user_input("\nDelete world materials ?", ["y", "yes", "n", "no"], "y") in ["y", "yes"]

        if lightweighting_level == 3:
            do_experimental_append: bool = get_user_input("\nEnable experimental Scene Collection object append ?", ["y", "yes", "n", "no"], "n") in ["y", "yes"]

        do_compress: bool = get_user_input("\nCompress file ?", ["y", "yes", "n", "no"], "n") in ["y", "yes"]
        
        print("\nProcessing file...")
        
        process_file(filepath, lightweighting_level, do_compress, do_delete_worlds, do_experimental_append or False, blender_executable_path)

        print("\n=== Done ===")


atexit.register(delete_temp_files)


if __name__ == "__main__":
    main()