"""
Rhino geometry → Blender mesh conversion.

Handles: Brep, Extrusion, Mesh, SubD.

Key details:
- Breps use pre-baked render meshes (GetMesh), NOT live tessellation
- Rhino stores triangles as (a, b, c, c) — must strip duplicate index
- Coordinate transform: Rhino Y-up → Blender Z-up
"""

import bpy
import rhino3dm


def _transform_vertex(pt, scale):
    """
    Transform a point from Rhino coordinate system to Blender.

    .3dm files use Y-up convention in their stored geometry.
    Y-up to Z-up: (x, y, z) → (x, -z, y)
    """
    return (pt.X * scale, -pt.Z * scale, pt.Y * scale)


def _build_face_list(rh_mesh):
    """
    Extract faces from a rhino3dm Mesh, normalizing triangles.

    Rhino always stores 4 indices per face. Triangles have the last
    index duplicated: (a, b, c, c). We detect and strip this.
    """
    faces = []
    for i in range(len(rh_mesh.Faces)):
        a, b, c, d = rh_mesh.Faces[i]
        if c == d:
            faces.append((a, b, c))
        else:
            faces.append((a, b, c, d))
    return faces


def _extract_render_meshes(geometry):
    """
    Extract pre-baked render meshes from a Rhino geometry object.

    Returns:
        tuple: (list of rhino3dm.Mesh, int count of missing meshes)
    """
    meshes = []
    missing = 0

    if isinstance(geometry, rhino3dm.Brep):
        for f in range(len(geometry.Faces)):
            m = geometry.Faces[f].GetMesh(rhino3dm.MeshType.Any)
            if m is not None:
                meshes.append(m)
            else:
                missing += 1

    elif isinstance(geometry, rhino3dm.Extrusion):
        m = geometry.GetMesh(rhino3dm.MeshType.Any)
        if m is not None:
            meshes.append(m)
        else:
            missing += 1

    elif isinstance(geometry, rhino3dm.Mesh):
        meshes.append(geometry)

    elif isinstance(geometry, rhino3dm.SubD):
        # SubD: try to get mesh representation
        if hasattr(geometry, 'ToMesh'):
            m = geometry.ToMesh()
            if m is not None:
                meshes.append(m)
            else:
                missing += 1
        else:
            # Fallback: try render mesh
            m = geometry.GetMesh(rhino3dm.MeshType.Any) if hasattr(geometry, 'GetMesh') else None
            if m is not None:
                meshes.append(m)
            else:
                missing += 1

    return meshes, missing


def _extract_vertex_colors(rh_mesh):
    """
    Extract vertex colors from a Rhino mesh if available.

    Returns:
        list of (R, G, B, A) tuples normalized to 0-1, or None
    """
    if not hasattr(rh_mesh, 'VertexColors') or len(rh_mesh.VertexColors) == 0:
        return None

    colors = []
    for i in range(len(rh_mesh.VertexColors)):
        c = rh_mesh.VertexColors[i]
        colors.append((c.R / 255.0, c.G / 255.0, c.B / 255.0, c.A / 255.0))
    return colors


def convert_to_mesh(geometry, name, unit_scale, validate=True):
    """
    Convert a Rhino geometry object to a Blender mesh.

    Args:
        geometry: rhino3dm geometry object (Brep, Extrusion, Mesh, SubD)
        name: Object name for the mesh
        unit_scale: Scale factor from units.get_scale()
        validate: Run mesh.validate() to clean degenerate geometry

    Returns:
        tuple: (bpy.types.Mesh or None, list of warning strings)
    """
    warnings = []

    rh_meshes, missing = _extract_render_meshes(geometry)

    if missing > 0:
        warnings.append(
            f"'{name}': {missing} face(s) had no render mesh. "
            f"Re-save the .3dm file from Rhino with render meshes enabled."
        )

    if not rh_meshes:
        return None, warnings

    # Merge all sub-meshes into combined vertex/face lists
    all_verts = []
    all_faces = []
    all_colors = []
    has_colors = False
    vert_offset = 0

    for rm in rh_meshes:
        # Vertices
        verts = [
            _transform_vertex(rm.Vertices[i], unit_scale)
            for i in range(len(rm.Vertices))
        ]

        # Faces
        faces = _build_face_list(rm)
        offset_faces = [
            tuple(vi + vert_offset for vi in f)
            for f in faces
        ]

        # Vertex colors
        colors = _extract_vertex_colors(rm)
        if colors is not None:
            has_colors = True
            all_colors.extend(colors)
        else:
            # Pad with default white if other sub-meshes have colors
            all_colors.extend([(1.0, 1.0, 1.0, 1.0)] * len(verts))

        all_verts.extend(verts)
        all_faces.extend(offset_faces)
        vert_offset += len(verts)

    # Create Blender mesh
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(all_verts, [], all_faces)

    if validate:
        mesh.validate()

    # Apply vertex colors if present
    if has_colors and all_colors:
        _apply_vertex_colors(mesh, all_colors, all_faces)

    mesh.update()

    # Smooth shading
    for poly in mesh.polygons:
        poly.use_smooth = True

    return mesh, warnings


def _apply_vertex_colors(mesh, vertex_colors, faces):
    """Apply per-vertex colors to a Blender mesh via a color attribute."""
    if not faces or not vertex_colors:
        return

    color_attr = mesh.color_attributes.new(
        name='RhinoColor',
        type='FLOAT_COLOR',
        domain='CORNER',
    )

    # Map vertex colors to face corners (loop colors)
    loop_idx = 0
    for face in faces:
        for vi in face:
            if vi < len(vertex_colors):
                color_attr.data[loop_idx].color = vertex_colors[vi]
            loop_idx += 1
