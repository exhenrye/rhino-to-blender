"""
Rhino materials → Blender Principled BSDF materials.

Maps Rhino's material properties to Blender's Principled BSDF shader:
- DiffuseColor → Base Color
- Shine (0-255) → Roughness (inverted, 0-1)
- Reflectivity (0-1) → Metallic
- Transparency (0-1) → Transmission Weight
"""

import bpy


def _argb_to_rgba(color):
    """Convert a rhino3dm Color to (R, G, B, A) float tuple normalized to 0-1."""
    r = color.R / 255.0 if hasattr(color, 'R') else 0.8
    g = color.G / 255.0 if hasattr(color, 'G') else 0.8
    b = color.B / 255.0 if hasattr(color, 'B') else 0.8
    a = color.A / 255.0 if hasattr(color, 'A') else 1.0
    return (r, g, b, a)


def _create_principled_bsdf(name, base_color, roughness=0.5, metallic=0.0,
                             alpha=1.0, transmission=0.0):
    """Create a Blender material with a Principled BSDF shader."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 300)

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 300)

    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    bsdf.inputs['Base Color'].default_value = base_color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Alpha'].default_value = alpha

    if transmission > 0:
        bsdf.inputs['Transmission Weight'].default_value = transmission
        mat.blend_method = 'BLEND' if hasattr(mat, 'blend_method') else None

    return mat


def build(model):
    """
    Build Blender materials from Rhino materials.

    Args:
        model: rhino3dm.File3dm instance

    Returns:
        dict: {material_index: bpy.types.Material}
    """
    mat_map = {}

    for i in range(len(model.Materials)):
        rhino_mat = model.Materials[i]
        name = rhino_mat.Name if rhino_mat.Name else f'RhinoMaterial_{i}'

        r, g, b, a = _argb_to_rgba(rhino_mat.DiffuseColor)

        # Rhino Shine is 0-255, convert to roughness (inverted)
        shine = getattr(rhino_mat, 'Shine', 0)
        roughness = 1.0 - (shine / 255.0) if shine > 0 else 0.5

        metallic = getattr(rhino_mat, 'Reflectivity', 0.0)
        transparency = getattr(rhino_mat, 'Transparency', 0.0)

        mat = _create_principled_bsdf(
            name=name,
            base_color=(r, g, b, 1.0),
            roughness=roughness,
            metallic=metallic,
            alpha=1.0 - transparency,
            transmission=transparency,
        )

        mat_map[i] = mat

    return mat_map


# Cache for layer-color materials to avoid duplicates
_layer_color_materials = {}


def get_for_object(obj_attrs, model, layer_collections, mat_map):
    """
    Get the appropriate material for a Rhino object.

    Resolves material source: per-object material, or fallback to layer color.

    Args:
        obj_attrs: rhino3dm ObjectAttributes
        model: rhino3dm.File3dm instance
        layer_collections: dict from layers.build()
        mat_map: dict from materials.build()

    Returns:
        bpy.types.Material or None
    """
    global _layer_color_materials

    mat_idx = obj_attrs.MaterialIndex

    # Object has an explicit material assignment
    if mat_idx >= 0 and mat_idx in mat_map:
        return mat_map[mat_idx]

    # Fall back to layer color
    layer_idx = obj_attrs.LayerIndex
    if layer_idx < 0 or layer_idx >= len(model.Layers):
        return None

    layer = model.Layers[layer_idx]
    color_key = str(layer.Color)

    if color_key in _layer_color_materials:
        return _layer_color_materials[color_key]

    r, g, b, a = _argb_to_rgba(layer.Color)
    mat = _create_principled_bsdf(
        name=f'Layer::{layer.Name}',
        base_color=(r, g, b, 1.0),
        roughness=0.5,
    )

    _layer_color_materials[color_key] = mat
    return mat


def reset_cache():
    """Clear the layer-color material cache between imports."""
    global _layer_color_materials
    _layer_color_materials = {}
