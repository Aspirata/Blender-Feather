import bpy, os

# These variables are injected by the launcher
LEVEL = {{LEVEL}}
FILEPATH = r"{{FILEPATH}}"
COMPRESS = {{COMPRESS}}
DELETE_WORLDS = {{DELETE_WORLDS}}
EXP_APPEND = {{EXP_APPEND}}


def purge_orphans(n=5):
    """Removes unused data blocks (repeats n times for deep cleanup)"""
    for _ in range(n):
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)


def delete_extras():
    """Removes brushes, palettes and line styles"""
    for b in list(bpy.data.brushes):
        bpy.data.brushes.remove(b)
    for p in list(bpy.data.palettes):
        bpy.data.palettes.remove(p)
    for ls in list(bpy.data.linestyles):
        bpy.data.linestyles.remove(ls)


def delete_all_worlds():
    """Removes all world materials"""
    for w in list(bpy.data.worlds):
        bpy.data.worlds.remove(w)


def remove_fake_users():
    """Disables fake user for all data blocks"""
    collections = [
        bpy.data.meshes, bpy.data.materials, bpy.data.textures, bpy.data.curves,
        bpy.data.armatures, bpy.data.actions, bpy.data.node_groups, bpy.data.images,
        bpy.data.lights, bpy.data.cameras, bpy.data.fonts, bpy.data.metaballs,
        bpy.data.lattices, bpy.data.speakers, bpy.data.lightprobes
    ]
    for col in collections:
        for item in col:
            if item.use_fake_user:
                item.use_fake_user = False


# Logic Flow
if DELETE_WORLDS:
    delete_all_worlds()

purge_orphans()

if LEVEL >= 2:
    delete_extras()

if LEVEL == 3:
    remove_fake_users()
    
    temp = FILEPATH + ".temp.blend"
    
    # Save temporary file
    bpy.ops.wm.save_as_mainfile(filepath=temp, compress=False)
    
    # Reset Blender to empty state
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Append everything back (automatically skips data without users)
    with bpy.data.libraries.load(temp) as (d_from, d_to):
        original_scenes = set(d_from.scenes) if hasattr(d_from, 'scenes') else set()
        d_to.collections = d_from.collections
        d_to.scenes = d_from.scenes
        if EXP_APPEND:
            d_to.objects = d_from.objects
    
    for scene in list(bpy.data.scenes):
        if scene.name not in original_scenes:
            bpy.data.scenes.remove(scene)
    
    # Restore collection hierarchy
    for col in d_to.collections:
        is_child = False
        # Check if collection is someone's child
        for other in d_to.collections:
            if col != other and col.name in [c.name for c in other.children]:
                is_child = True
                break
        
        # Link only top-level collections
        if not is_child and col.name not in bpy.context.scene.collection.children:
            try:
                bpy.context.scene.collection.children.link(col)
            except RuntimeError:
                pass  # Already linked
    
    # Link objects that aren't in any collection (only if experimental append is on)
    if EXP_APPEND:
        for obj in d_to.objects:
            in_collection = False
            for col in d_to.collections:
                if obj.name in [o.name for o in col.objects]:
                    in_collection = True
                    break
            
            if not in_collection and obj.name not in bpy.context.scene.collection.objects:
                try:
                    bpy.context.scene.collection.objects.link(obj)
                except RuntimeError:
                    pass

# Generate new filename
name, ext = os.path.splitext(os.path.basename(FILEPATH))
new_path = os.path.join(os.path.dirname(FILEPATH), f"{name}_L{LEVEL}{ext}")

# Save result
bpy.ops.wm.save_as_mainfile(filepath=new_path, compress=COMPRESS)
print(f"Saved: {new_path}")