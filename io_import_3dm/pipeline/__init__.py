"""
Import pipeline orchestrator.

Five-phase import:
1. File read and context initialization
2. Unit scale calculation
3. Layer → collection hierarchy
4. Material conversion
5. Object conversion (meshes, curves, instances)
"""

import bpy
import rhino3dm

from . import curves, instances, layers, materials, meshes, units


def read_3dm(filepath, options, context):
    """
    Read a .3dm file and import all objects into the current Blender scene.

    Args:
        filepath: Path to the .3dm file
        options: dict with import options from the operator
        context: Blender context

    Returns:
        list: Warning strings accumulated during import
    """
    warnings = []

    # --- Phase 1: File read ---
    model = rhino3dm.File3dm.Read(filepath)
    if model is None:
        raise ValueError(f'Could not read file: {filepath}')

    # --- Phase 2: Unit scale ---
    unit_scale = options.get('scale_override', 0.0)
    if unit_scale <= 0:
        unit_scale = units.get_scale(model.Settings.ModelUnitSystem)

    # --- Phase 3: Layers → Collections ---
    scene_collection = context.scene.collection
    layer_collections = layers.build(model, scene_collection, options)

    # --- Phase 4: Materials ---
    materials.reset_cache()
    mat_map = materials.build(model)

    # --- Phase 5: Object conversion ---
    import_hidden = options.get('import_hidden_objects', False)
    import_instances_opt = options.get('import_instances', True)
    validate = options.get('validate_meshes', True)
    curve_as_mesh = options.get('curve_as_mesh', False)

    # Pre-build instance definitions if needed
    idef_collections = {}
    if import_instances_opt:
        idef_collections = instances.build_instance_defs(model)

    # Track object count for reporting
    imported_count = 0
    skipped_count = 0

    for obj_entry in model.Objects:
        og = obj_entry.Geometry
        oa = obj_entry.Attributes

        # Skip hidden objects unless option is set
        if not oa.Visible and not import_hidden:
            skipped_count += 1
            continue

        # Skip objects on hidden layers (if layer was not imported)
        layer_col = layer_collections.get(oa.LayerIndex)
        if layer_col is None:
            skipped_count += 1
            continue

        # Determine object name
        name = oa.Name if oa.Name else f'RhinoObject_{imported_count}'

        obj_type = og.ObjectType

        # --- Mesh types: Brep, Extrusion, Mesh, SubD ---
        if obj_type in (
            rhino3dm.ObjectType.Brep,
            rhino3dm.ObjectType.Extrusion,
            rhino3dm.ObjectType.Mesh,
            rhino3dm.ObjectType.SubD,
        ):
            mesh_data, mesh_warnings = meshes.convert_to_mesh(
                og, name, unit_scale, validate=validate,
            )
            warnings.extend(mesh_warnings)

            if mesh_data is None:
                skipped_count += 1
                continue

            obj = bpy.data.objects.new(name, mesh_data)

            # Assign material
            mat = materials.get_for_object(oa, model, layer_collections, mat_map)
            if mat is not None:
                obj.data.materials.append(mat)

            layer_col.objects.link(obj)
            imported_count += 1

        # --- Curves ---
        elif obj_type == rhino3dm.ObjectType.Curve:
            if curve_as_mesh:
                # Tessellate curve to mesh edges
                mesh_data, curve_warnings = _curve_to_mesh(og, name, unit_scale)
                warnings.extend(curve_warnings)
                if mesh_data is not None:
                    obj = bpy.data.objects.new(name, mesh_data)
                    layer_col.objects.link(obj)
                    imported_count += 1
                else:
                    skipped_count += 1
            else:
                curve_data, curve_warnings = curves.convert_curve(
                    og, name, unit_scale,
                )
                warnings.extend(curve_warnings)

                if curve_data is None:
                    skipped_count += 1
                    continue

                obj = bpy.data.objects.new(name, curve_data)

                # Assign material for curve color
                mat = materials.get_for_object(
                    oa, model, layer_collections, mat_map,
                )
                if mat is not None:
                    obj.data.materials.append(mat)

                layer_col.objects.link(obj)
                imported_count += 1

        # --- Instance References (Blocks) ---
        elif obj_type == rhino3dm.ObjectType.InstanceReference:
            if not import_instances_opt:
                skipped_count += 1
                continue

            inst_obj, inst_warnings = instances.place_instance(
                og, name, idef_collections, unit_scale, layer_col,
            )
            warnings.extend(inst_warnings)

            if inst_obj is not None:
                imported_count += 1
            else:
                skipped_count += 1

        # --- Point sets ---
        elif obj_type == rhino3dm.ObjectType.Point:
            # Import as empty at point location
            pt = og.Location if hasattr(og, 'Location') else None
            if pt is not None:
                empty = bpy.data.objects.new(name, None)
                empty.empty_display_type = 'PLAIN_AXES'
                empty.empty_display_size = 0.1
                empty.location = (
                    pt.X * unit_scale,
                    -pt.Z * unit_scale,
                    pt.Y * unit_scale,
                )
                layer_col.objects.link(empty)
                imported_count += 1
            else:
                skipped_count += 1

        else:
            skipped_count += 1

    # Summary
    if skipped_count > 0:
        warnings.append(
            f'Import complete: {imported_count} objects imported, '
            f'{skipped_count} skipped (hidden, unsupported, or missing mesh).'
        )

    return warnings


def _curve_to_mesh(geometry, name, unit_scale, samples=64):
    """Tessellate a curve into a mesh of edges (for curve_as_mesh option)."""
    warnings = []

    if not hasattr(geometry, 'Domain'):
        warnings.append(f"'{name}': Cannot sample curve, skipped.")
        return None, warnings

    domain = geometry.Domain
    t_start = domain.T0
    t_end = domain.T1

    verts = []
    edges = []

    for i in range(samples):
        t = t_start + (t_end - t_start) * (i / (samples - 1))
        pt = geometry.PointAt(t)
        x = pt.X * unit_scale
        y = -pt.Z * unit_scale
        z = pt.Y * unit_scale
        verts.append((x, y, z))
        if i > 0:
            edges.append((i - 1, i))

    if geometry.IsClosed:
        edges.append((samples - 1, 0))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, edges, [])
    mesh.update()

    return mesh, warnings
