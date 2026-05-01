import os, subprocess, re, atexit, tempfile, traceback
from pathlib import Path

BLENDER_EXECUTABLES_PATHS: list[str] = [r"S:\Programs\Blender Launcher"]
TEMP_DIR: str = tempfile.gettempdir()

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


def get_user_input(prompt: str, valid_responses: list[str | int | float] = ["y", "yes", "n", "no"],
                    default_value: None | bool | str | int | float = None) -> str:
    """Get user input with validation and default option"""
    if valid_responses:
        valid_responses = [str(response) for response in valid_responses]
        prompt += f" (valid responses: {', '.join(valid_responses)})"

    if default_value is not None:
        prompt += f" (default: {default_value})"

    while True:
        response = input(f"{prompt}: ").strip().lower()
        if response == "" and default_value is not None:
            return default_value
        if (valid_responses and response in valid_responses) or not valid_responses:
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

def get_blender_executables() -> dict[str, str]:
    """Detect valid blender executables paths from BLENDER_EXECUTABLES_PATHS"""
    blender_versions = {}
    version_pattern = re.compile(r'^\d+\.\d+')

    def walk(directory: str):
        try:
            entries = os.listdir(directory)
        except PermissionError:
            return

        for entry in entries:
            entry_path = os.path.join(directory, entry)
            if not os.path.isdir(entry_path):
                continue

            if version_pattern.match(entry):
                blender_exe = os.path.join(directory, "blender.exe")
                if os.path.isfile(blender_exe):
                    blender_versions[entry] = blender_exe
            else:
                walk(entry_path)

    for path in BLENDER_EXECUTABLES_PATHS:
        if os.path.exists(path):
            walk(path)

    return blender_versions

def choose_blender(file_version, blender_versions):
    """Select Blender version"""
    versions = [(ver, path) for ver, path in blender_versions.items() if os.path.exists(path)]
    if not versions:
        print("No valid Blender executables found. Please check BLENDER_VERSIONS paths.")
        exit(1)

    print("Available versions:")
    for i, (ver, _) in enumerate(versions, 1):
        print(f"{i}. Blender {ver}")

    default_blender_version = next((i for i, (ver, _) in enumerate(versions, 1) if ver == file_version), None)
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
    print("=== Blender Feather #30 ===")

    delete_temp_files()

    while True:
        if any(path for path in BLENDER_EXECUTABLES_PATHS if not os.path.exists(path)):
            print("\nInvalid Blender executables paths will be skipped. Please remove or fix them in BLENDER_EXECUTABLES_PATHS in the script:")
            for path in BLENDER_EXECUTABLES_PATHS:
                if not os.path.exists(path):
                    print(f"  - {path}")

        if not any(os.path.exists(path) for path in BLENDER_EXECUTABLES_PATHS):
            print("\nNo valid Blender executables found. Please check BLENDER_EXECUTABLES_PATHS in the script.")
            exit(1)

        blender_versions: dict[str, str] = get_blender_executables()
        if not blender_versions:
            print("\nNo valid Blender executables found. Please check BLENDER_EXECUTABLES_PATHS in the script.")
            exit(1)

        filepath = input("\nDrag .blend file: ").strip().strip('"').strip("'")
        
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
        if not filepath.lower().endswith('.blend'):
            print("Not a .blend file")
            continue
        
        # Detect file version (using latest Blender)
        print("\nDetecting file version...")
        latest_blender_version = blender_versions[sorted(blender_versions.keys())[-1]]
        file_version = get_blend_version(filepath, latest_blender_version)
        print(f"\nFile saved in Blender {file_version}")
        
        blender_executable_path: str = choose_blender(file_version, blender_versions)
        
        print("\nLightweighting levels:")
        print("1. Purge (remove unused data)")
        print("2. Level 1 + remove brushes, palettes, line styles")
        print("3. Level 2 + remove fake users + rebuild via Append")
        
        lightweighting_level: int = int(get_user_input("\nChoose Lightweighting Level", [1, 2, 3], 1))
        
        do_delete_worlds: bool = get_user_input("\nDelete world materials ?", default_value="n") in ["y", "yes"]

        do_experimental_append: bool = False
        if lightweighting_level == 3:
            do_experimental_append: bool = get_user_input("\nEnable experimental Scene Collection object append ?", default_value="n") in ["y", "yes"]

        do_compress: bool = get_user_input("\nCompress file ?", default_value="y") in ["y", "yes"]
        
        print("\nProcessing file...")
        
        process_file(filepath, lightweighting_level, do_compress, do_delete_worlds, do_experimental_append, blender_executable_path)

        print("\n=== Done ===")


atexit.register(delete_temp_files)


if __name__ == "__main__":
    main()