"""
Blender headless integration test.

Run with:
    blender --background --python io_import_3dm/tests/smoke_test.py -- path/to/test.3dm

This script:
1. Enables the add-on
2. Imports the specified .3dm file
3. Verifies objects were created
4. Reports results
"""

import sys
import os


def main():
    import bpy

    # Find the .3dm file path from command line args (after --)
    argv = sys.argv
    filepath = None
    if '--' in argv:
        args_after = argv[argv.index('--') + 1:]
        if args_after:
            filepath = args_after[0]

    if not filepath:
        print('ERROR: No .3dm file specified.')
        print('Usage: blender --background --python smoke_test.py -- path/to/file.3dm')
        sys.exit(1)

    if not os.path.exists(filepath):
        print(f'ERROR: File not found: {filepath}')
        sys.exit(1)

    # Add the add-on directory to sys.path
    addon_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if addon_dir not in sys.path:
        sys.path.insert(0, addon_dir)

    # Register the add-on
    from io_import_3dm import register
    register()

    # Clear the default scene
    bpy.ops.wm.read_homefile(use_empty=True)

    # Run the import operator
    result = bpy.ops.import_scene.rhinoceros3d(filepath=filepath)

    if result != {'FINISHED'}:
        print(f'ERROR: Import operator returned {result}')
        sys.exit(1)

    # Count imported objects
    obj_count = len(bpy.data.objects)
    mesh_count = len([o for o in bpy.data.objects if o.type == 'MESH'])
    curve_count = len([o for o in bpy.data.objects if o.type == 'CURVE'])
    empty_count = len([o for o in bpy.data.objects if o.type == 'EMPTY'])
    collection_count = len(bpy.data.collections)
    material_count = len(bpy.data.materials)

    print('=' * 60)
    print('SMOKE TEST RESULTS')
    print('=' * 60)
    print(f'File: {filepath}')
    print(f'Objects:     {obj_count}')
    print(f'  Meshes:    {mesh_count}')
    print(f'  Curves:    {curve_count}')
    print(f'  Empties:   {empty_count}')
    print(f'Collections: {collection_count}')
    print(f'Materials:   {material_count}')
    print('=' * 60)

    if obj_count == 0:
        print('WARNING: No objects were imported!')
        sys.exit(1)

    print('PASS: Import completed with objects.')
    sys.exit(0)


if __name__ == '__main__':
    main()
