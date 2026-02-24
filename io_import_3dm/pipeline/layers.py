"""
Rhino layers → Blender collection hierarchy.

Rhino layers are stored flat with parent references via ParentLayerId (UUID).
This module reconstructs the tree and creates a matching Blender collection
hierarchy.
"""

import bpy


def _color_to_tuple(color):
    """Convert a rhino3dm Color (ARGB int) to an (R, G, B, A) float tuple."""
    r = color.R / 255.0 if hasattr(color, 'R') else 0.8
    g = color.G / 255.0 if hasattr(color, 'G') else 0.8
    b = color.B / 255.0 if hasattr(color, 'B') else 0.8
    a = color.A / 255.0 if hasattr(color, 'A') else 1.0
    return (r, g, b, a)


def build(model, scene_collection, options):
    """
    Build Blender collections from Rhino layers.

    Args:
        model: rhino3dm.File3dm instance
        scene_collection: bpy.context.scene.collection
        options: dict with import options

    Returns:
        dict: {layer_index: bpy.types.Collection}
    """
    import_hidden_layers = options.get('import_hidden_layers', False)

    # Build UUID → (index, layer) lookup
    layers_by_id = {}
    for i in range(len(model.Layers)):
        layer = model.Layers[i]
        layers_by_id[str(layer.Id)] = (i, layer)

    collections = {}

    def get_or_create(index):
        if index in collections:
            return collections[index]

        layer = model.Layers[index]

        # Skip hidden layers unless option is set
        if not layer.Visible and not import_hidden_layers:
            collections[index] = None
            return None

        col = bpy.data.collections.new(layer.Name)

        # Set visibility
        col.hide_viewport = not layer.Visible

        # Store layer color as custom property
        col['rhino_layer_color'] = _color_to_tuple(layer.Color)

        # Resolve parent
        parent_id = str(layer.ParentLayerId)
        # Check if parent exists and isn't self-referencing
        if parent_id in layers_by_id:
            parent_idx, _parent_layer = layers_by_id[parent_id]
            if parent_idx != index:
                parent_col = get_or_create(parent_idx)
                if parent_col is not None:
                    parent_col.children.link(col)
                else:
                    scene_collection.children.link(col)
            else:
                scene_collection.children.link(col)
        else:
            scene_collection.children.link(col)

        collections[index] = col
        return col

    for i in range(len(model.Layers)):
        get_or_create(i)

    return collections
