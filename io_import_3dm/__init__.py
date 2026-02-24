"""
Rhinoceros 3D Importer — Blender Add-on

Imports .3dm files with full fidelity:
- Geometry (Brep, Mesh, Extrusion, SubD) as meshes
- Layers as Blender collections
- Materials as Principled BSDF shaders
- Curves (NURBS, polylines, arcs) as splines
- Block instances as collection instances
- Object names and visibility
"""

bl_info = {
    'name': 'Rhinoceros 3D Importer',
    'author': 'Enea Henry',
    'version': (1, 0, 0),
    'blender': (4, 0, 0),
    'location': 'File > Import > Rhinoceros 3D (.3dm)',
    'description': 'Import .3dm files with geometry, layers, materials, and curves',
    'category': 'Import-Export',
}


def menu_func_import(self, context):
    self.layout.operator(
        'import_scene.rhinoceros3d',
        text='Rhinoceros 3D (.3dm)',
    )


def register():
    import bpy
    from .operator import IMPORT_OT_rhinoceros3d

    bpy.utils.register_class(IMPORT_OT_rhinoceros3d)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

    # Try to bootstrap rhino3dm early (non-fatal)
    from .deps import ensure_rhino3dm
    ok, err = ensure_rhino3dm()
    if not ok:
        print(f'[Rhinoceros 3D Importer] Warning: {err}')
        print('[Rhinoceros 3D Importer] Import will fail until rhino3dm is available.')


def unregister():
    import bpy
    from .operator import IMPORT_OT_rhinoceros3d

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(IMPORT_OT_rhinoceros3d)


if __name__ == '__main__':
    register()
