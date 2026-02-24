"""
Unit scale conversion from Rhino unit systems to Blender meters.
"""


def get_scale(unit_system):
    """
    Convert a rhino3dm.UnitSystem enum value to a scale factor
    that transforms coordinates into meters (Blender's default unit).

    Args:
        unit_system: rhino3dm.UnitSystem enum value

    Returns:
        float: Scale factor to multiply coordinates by
    """
    import rhino3dm

    UNIT_SCALES = {
        rhino3dm.UnitSystem.Angstroms: 1e-10,
        rhino3dm.UnitSystem.Nanometers: 1e-9,
        rhino3dm.UnitSystem.Microns: 1e-6,
        rhino3dm.UnitSystem.Millimeters: 0.001,
        rhino3dm.UnitSystem.Centimeters: 0.01,
        rhino3dm.UnitSystem.Decimeters: 0.1,
        rhino3dm.UnitSystem.Meters: 1.0,
        rhino3dm.UnitSystem.Dekameters: 10.0,
        rhino3dm.UnitSystem.Hectometers: 100.0,
        rhino3dm.UnitSystem.Kilometers: 1000.0,
        rhino3dm.UnitSystem.Megameters: 1e6,
        rhino3dm.UnitSystem.Gigameters: 1e9,
        rhino3dm.UnitSystem.Microinches: 0.0000000254,
        rhino3dm.UnitSystem.Mils: 0.0000254,
        rhino3dm.UnitSystem.Inches: 0.0254,
        rhino3dm.UnitSystem.Feet: 0.3048,
        rhino3dm.UnitSystem.Yards: 0.9144,
        rhino3dm.UnitSystem.Miles: 1609.344,
        rhino3dm.UnitSystem.NauticalMiles: 1852.0,
    }

    return UNIT_SCALES.get(unit_system, 1.0)
