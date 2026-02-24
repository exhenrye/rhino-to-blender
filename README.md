# Rhinoceros 3D Importer for Blender

A Blender 4.0+ add-on that imports Rhinoceros 3D (`.3dm`) files with full fidelity.

## Features

- **Geometry**: Brep, Mesh, Extrusion, SubD → Blender meshes
- **Layers**: Rhino layer hierarchy → Blender collection hierarchy
- **Materials**: Rhino materials → Principled BSDF shaders (diffuse, roughness, metallic, transparency)
- **Curves**: NURBS curves, polylines, arcs → Blender splines
- **Blocks**: Instance definitions → collection instances
- **Names & visibility**: Object names and hidden state preserved

## Requirements

- Blender 4.0 or later (4.2+ recommended for extension support)
- `rhino3dm` Python library (bundled or installed separately)

## Installation

### Option A: Blender 4.2+ Extension (recommended)

1. Download the latest release ZIP
2. In Blender: Edit > Preferences > Get Extensions > Install from Disk
3. Select the ZIP file

### Option B: Classic Add-on Install

1. Download the latest release ZIP
2. In Blender: Edit > Preferences > Add-ons > Install
3. Select the ZIP file
4. Enable "Rhinoceros 3D Importer"
5. **Restart Blender** (required for rhino3dm to load)

### macOS Note

If the add-on fails to load with a module import error, run this in Terminal:

```bash
xattr -rd com.apple.quarantine ~/Library/Application\ Support/Blender/4.*/extensions/
```

This removes the macOS quarantine flag from the bundled native library.

## Usage

File > Import > Rhinoceros 3D (.3dm)

### Import Options

| Option | Default | Description |
|--------|---------|-------------|
| Hidden Objects | Off | Import objects hidden in Rhino |
| Hidden Layers | Off | Import objects on hidden layers |
| Validate Meshes | On | Clean degenerate geometry |
| Curves as Mesh | Off | Tessellate curves to mesh edges |
| Import Blocks | On | Import block instances |
| Scale Override | 0 (auto) | Manual scale factor (0 = use file units) |

## Known Limitations

- **Trimmed NURBS surfaces** are tessellated to meshes (Blender has no trimmed NURBS support)
- **Render meshes required**: Breps without cached render meshes will be skipped. Re-save the `.3dm` file from Rhino with render meshes enabled
- **Non-uniform NURBS knot vectors** are approximated — curve shapes may differ slightly from Rhino
- **No live tessellation**: mesh quality depends on what Rhino saved in the file

## License

MIT
