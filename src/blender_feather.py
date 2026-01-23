import os
import subprocess

# --- КОНФИГУРАЦИЯ: Добавьте свои версии Blender ---
BLENDER_VERSIONS = {
    "3.6": r"E:\blender launcher\stable\blender-3.6.22-lts.30b431ea75f7\blender.exe",
    "4.5": r"E:\blender launcher\stable\blender-4.5.5-lts.836beaaf597a\blender.exe",
    "5.0": r"E:\blender launcher\stable\blender-5.0.1-stable.a3db93c5b259\blender.exe",
}

def parse_filepath(raw_input):
    """Очищает путь от PowerShell-артефактов и кавычек."""
    path = raw_input.strip()
    path = path.strip()
    if (path.startswith('"') and path.endswith('"')) or \
       (path.startswith("'") and path.endswith("'")):
        path = path[1:-1]
    elif path.startswith(('"', "'")):
        path = path[1:]
    elif path.endswith(('"', "'")):
        path = path[:-1]
    
    return path.strip()

def get_blend_version(filepath, blender_exec):
    """Определяет версию .blend файла."""
    script = 'import bpy; print(f"V:{bpy.data.version[0]}.{bpy.data.version[1]}")'
    temp_file = "temp_version.py"
    
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(script)
    
    try:
        result = subprocess.run(
            [blender_exec, "-b", filepath, "-P", temp_file],
            capture_output=True, text=True, timeout=30
        )
        for line in result.stdout.splitlines():
            if "V:" in line:
                return line.split("V:")[1].strip()
        return "Неизвестно"
    except Exception as e:
        return f"Ошибка: {e}"
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def choose_blender_version():
    """Позволяет пользователю выбрать версию Blender."""
    versions = sorted(BLENDER_VERSIONS.keys())
    print("\nДоступные версии Blender:")
    for i, ver in enumerate(versions, 1):
        print(f"{i}. Blender {ver}")
    
    while True:
        choice = input(f"\nВыберите версию (1-{len(versions)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(versions):
            selected = versions[int(choice) - 1]
            return BLENDER_VERSIONS[selected]
        print("Неверный выбор, попробуйте снова.")

def generate_script(level, filepath, compress):
    """Генерирует Python-скрипт для Blender."""
    safe_path = filepath.replace("\\", "/")
    
    return f"""
import bpy, os

def purge_orphans(n=5):
    for _ in range(n):
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

def delete_extras():
    for b in list(bpy.data.brushes): bpy.data.brushes.remove(b)
    for p in list(bpy.data.palettes): bpy.data.palettes.remove(p)
    for ls in list(bpy.data.linestyles): bpy.data.linestyles.remove(ls)

def remove_fake_users():
    for col in [bpy.data.meshes, bpy.data.materials, bpy.data.textures, bpy.data.curves,
                bpy.data.armatures, bpy.data.actions, bpy.data.node_groups, bpy.data.images,
                bpy.data.lights, bpy.data.cameras, bpy.data.fonts, bpy.data.metaballs,
                bpy.data.lattices, bpy.data.speakers, bpy.data.lightprobes]:
        for item in col:
            if item.use_fake_user:
                item.use_fake_user = False

level = {level}
if level >= 2: delete_extras()
if level == 3: remove_fake_users()

purge_orphans()

if level == 3:
    temp = r"{safe_path}" + ".temp.blend"
    bpy.ops.wm.save_as_mainfile(filepath=temp, compress=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    with bpy.data.libraries.load(temp) as (d_from, d_to):
        d_to.collections = d_from.collections
        d_to.scenes = d_from.scenes
        d_to.objects = d_from.objects
    
    # Создаём словарь для отслеживания родительских коллекций
    collection_hierarchy = {{}}
    for col in d_to.collections:
        # Проверяем, является ли коллекция дочерней для другой коллекции
        is_child = False
        for other_col in d_to.collections:
            if col != other_col and col.name in [c.name for c in other_col.children]:
                is_child = True
                collection_hierarchy[col.name] = other_col.name
                break
        
        # Линкуем только коллекции верхнего уровня (не вложенные)
        if not is_child and col.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(col)
    
    # Линкуем объекты, которые не принадлежат ни одной коллекции
    for obj in d_to.objects:
        obj_in_collection = False
        for col in d_to.collections:
            if obj.name in [o.name for o in col.objects]:
                obj_in_collection = True
                break
        
        if not obj_in_collection and obj.name not in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.link(obj)
    
    if os.path.exists(temp): os.remove(temp)

path = r"{safe_path}"
name, ext = os.path.splitext(os.path.basename(path))
new_path = os.path.join(os.path.dirname(path), f"{{name}}_L{level}{{ext}}")
bpy.ops.wm.save_as_mainfile(filepath=new_path, compress={compress})
print(f"Saved: {{new_path}}")
"""

def process_file(filepath, level, compress, blender_exec):
    """Обрабатывает .blend файл."""
    temp_script = "temp_process.py"
    
    with open(temp_script, "w", encoding="utf-8") as f:
        f.write(generate_script(level, filepath, compress))
    
    print(f"\n🚀 Обработка (Уровень {level})...")
    if level == 3:
        print("ℹ️ Уровень 3: пересоздание файла (может занять время)")
    
    try:
        result = subprocess.run(
            [blender_exec, "-b", filepath, "-P", temp_script],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("\n✅ Готово!")
            for line in result.stdout.splitlines():
                if "Saved:" in line:
                    print(line)
        else:
            print("\n❌ Ошибка:")
            print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    finally:
        if os.path.exists(temp_script):
            os.remove(temp_script)
        temp_blend = filepath + ".temp.blend"
        if os.path.exists(temp_blend):
            os.remove(temp_blend)

def main():
    print("=== Blender Feather #14 ===\n")
    
    # Получаем путь к файлу
    filepath = parse_filepath(input("Перетащите .blend файл: "))
    
    if not os.path.exists(filepath):
        print(f"❌ Файл не найден: {filepath}")
        return
    if not filepath.lower().endswith('.blend'):
        print("❌ Это не .blend файл")
        return
    
    # Определяем версию файла
    print("\n🔍 Определение версии файла...")
    version = get_blend_version(filepath, BLENDER_VERSIONS[max(BLENDER_VERSIONS.keys())])
    print(f"📌 Файл сохранён в Blender {version}")
    
    # Выбираем версию Blender
    blender_exec = choose_blender_version()
    
    # Выбор уровня
    print("\nУровни оптимизации:")
    print("1. Очистка неиспользуемых данных")
    print("2. Уровень 1 + Удаление кистей, палитр, line styles")
    print("3. Уровень 2 + Удаление fake users + Пересоздание через Append")
    
    choice = input("\nУровень (1-3): ").strip()
    if choice not in ['1', '2', '3']:
        print("Неверный выбор.")
        return
    
    # Сжатие
    compress = input("\nСжать файл? (y/n): ").strip().lower() in ['y', 'yes', 'д', 'да']
    print(f"🗜️ Сжатие: {'Вкл' if compress else 'Выкл'}")
    
    process_file(filepath, int(choice), compress, blender_exec)

if __name__ == "__main__":
    main()
    input("\nEnter для выхода...")