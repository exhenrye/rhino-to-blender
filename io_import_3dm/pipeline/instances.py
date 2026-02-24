"""
Rhino block instances → Blender collection instances.

Rhino's InstanceDefinitions contain geometry templates.
InstanceReferences place them in the scene with a transform matrix.
These map to Blender's collection instances (empty with instance_type='COLLECTION').
"""

import math

import bpy
import mathutils
import rhino3dm


# Y-up to Z-up rotation matrix (-90 degrees around X)
_Y_TO_Z_UP = mathutils.Matrix.Rotation(-math.pi / 2, 4, 'X')


def build_instance_defs(model):
    """
    Pre-pass: create a Blender collection for each Rhino InstanceDefinition.

    The geometry within each definition is converted later in the main
    object loop (when the object's parent idef is identified).

    Args:
        model: rhino3dm.File3dm instance

    Returns:
        dict: {idef_id_str: bpy.types.Collection}
    """
    idef_collections = {}

    for idef in model.InstanceDefinitions:
        name = idef.Name if idef.Name else f'Block_{idef.Id}'
        col = bpy.data.collections.new(f'Block::{name}')
        idef_collections[str(idef.Id)] = col

    return idef_collections


def place_instance(geometry, name, idef_collections, unit_scale, parent_collection):
    """
    Create a Blender collection instance (empty) for a Rhino InstanceReference.

    Args:
        geometry: rhino3dm.InstanceReference
        name: Object name
        idef_collections: dict from build_instance_defs()
        unit_scale: Scale factor
        parent_collection: Blender collection to link the empty into

    Returns:
        tuple: (bpy.types.Object or None, list of warning strings)
    """
    warnings = []

    idef_id = str(geometry.ParentIdefId)
    if idef_id not in idef_collections:
        warnings.append(f"'{name}': Instance definition not found, skipped.")
        return None, warnings

    col = idef_collections[idef_id]

    # Ensure the idef collection is linked to the scene somewhere
    # (it needs to exist in the scene for instance_collection to work)
    if col.name not in bpy.context.scene.collection.children:
        found = False
        for scene_col in bpy.data.collections:
            if col.name in [c.name for c in scene_col.children]:
                found = True
                break
        if not found:
            bpy.context.scene.collection.children.link(col)
            # Hide the definition collection — only instances should be visible
            col.hide_viewport = True
            col.hide_render = True

    # Create empty object as instance placeholder
    empty = bpy.data.objects.new(name, None)
    empty.instance_type = 'COLLECTION'
    empty.instance_collection = col

    # Apply transform matrix from the InstanceReference
    xf = geometry.Xform
    rhino_matrix = mathutils.Matrix([
        [xf.M00, xf.M01, xf.M02, xf.M03 * unit_scale],
        [xf.M10, xf.M11, xf.M12, xf.M13 * unit_scale],
        [xf.M20, xf.M21, xf.M22, xf.M23 * unit_scale],
        [xf.M30, xf.M31, xf.M32, xf.M33],
    ])

    # Apply Y-up → Z-up correction
    empty.matrix_world = _Y_TO_Z_UP @ rhino_matrix

    parent_collection.objects.link(empty)

    return empty, warnings
