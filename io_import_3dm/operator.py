"""
Blender import operator for Rhinoceros 3D (.3dm) files.

Provides the File > Import > Rhinoceros 3D (.3dm) menu entry
with configurable import options.
"""

import bpy
from bpy.props import BoolProperty, FloatProperty, StringProperty
from bpy_extras.io_utils import ImportHelper


class IMPORT_OT_rhinoceros3d(bpy.types.Operator, ImportHelper):
    """Import a Rhinoceros 3D (.3dm) file"""

    bl_idname = 'import_scene.rhinoceros3d'
    bl_label = 'Import Rhinoceros 3D (.3dm)'
    bl_description = 'Import geometry, layers, materials, and curves from a .3dm file'
    bl_options = {'REGISTER', 'UNDO'}

    # File filter
    filter_glob: StringProperty(
        default='*.3dm',
        options={'HIDDEN'},
    )

    # --- Filtering options ---
    import_hidden_objects: BoolProperty(
        name='Hidden Objects',
        description='Import objects that are hidden in Rhino',
        default=False,
    )

    import_hidden_layers: BoolProperty(
        name='Hidden Layers',
        description='Import objects on layers that are hidden in Rhino',
        default=False,
    )

    # --- Geometry options ---
    validate_meshes: BoolProperty(
        name='Validate Meshes',
        description='Run mesh validation to remove degenerate geometry',
        default=True,
    )

    curve_as_mesh: BoolProperty(
        name='Curves as Mesh',
        description='Tessellate curves into mesh edges instead of NURBS splines',
        default=False,
    )

    import_instances: BoolProperty(
        name='Import Blocks',
        description='Import Rhino block instances as collection instances',
        default=True,
    )

    # --- Scale ---
    scale_override: FloatProperty(
        name='Scale Override',
        description='Override the unit scale (0 = auto-detect from file units)',
        default=0.0,
        min=0.0,
        max=10000.0,
        precision=4,
    )

    def execute(self, context):
        from .deps import ensure_rhino3dm

        ok, err = ensure_rhino3dm()
        if not ok:
            self.report({'ERROR'}, f'rhino3dm unavailable: {err}')
            return {'CANCELLED'}

        from .pipeline import read_3dm

        options = {
            'import_hidden_objects': self.import_hidden_objects,
            'import_hidden_layers': self.import_hidden_layers,
            'validate_meshes': self.validate_meshes,
            'curve_as_mesh': self.curve_as_mesh,
            'import_instances': self.import_instances,
            'scale_override': self.scale_override,
        }

        try:
            warnings = read_3dm(self.filepath, options, context)
        except Exception as e:
            self.report({'ERROR'}, str(e))
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}

        for w in warnings:
            self.report({'WARNING'}, w)

        if not warnings:
            self.report({'INFO'}, 'Import complete.')

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text='Filtering', icon='FILTER')
        box.prop(self, 'import_hidden_objects')
        box.prop(self, 'import_hidden_layers')

        box = layout.box()
        box.label(text='Geometry', icon='MESH_DATA')
        box.prop(self, 'validate_meshes')
        box.prop(self, 'curve_as_mesh')
        box.prop(self, 'import_instances')

        box = layout.box()
        box.label(text='Scale', icon='OBJECT_ORIGIN')
        box.prop(self, 'scale_override')
        if self.scale_override <= 0:
            box.label(text='(Auto-detect from file units)', icon='INFO')
