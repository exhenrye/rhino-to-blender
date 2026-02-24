"""Tests for Rhino Y-up → Blender Z-up coordinate transform."""


class _MockPoint:
    """Mock rhino3dm point for testing without the library."""

    def __init__(self, x, y, z):
        self.X = x
        self.Y = y
        self.Z = z


def _transform_vertex(pt, scale):
    """
    Standalone version of meshes._transform_vertex for testing.

    Rhino: X right, Y forward, Z up
    Transform: (x, -z, y) * scale
    """
    return (pt.X * scale, -pt.Z * scale, pt.Y * scale)


def test_origin():
    """Origin should remain at origin regardless of scale."""
    pt = _MockPoint(0, 0, 0)
    assert _transform_vertex(pt, 1.0) == (0, 0, 0)
    assert _transform_vertex(pt, 100.0) == (0, 0, 0)


def test_x_axis_preserved():
    """X axis should map to X axis in Blender."""
    pt = _MockPoint(1, 0, 0)
    result = _transform_vertex(pt, 1.0)
    assert result == (1, 0, 0)


def test_y_axis_maps_to_z():
    """Rhino Y (forward) should map to Blender Z (up)."""
    pt = _MockPoint(0, 1, 0)
    result = _transform_vertex(pt, 1.0)
    assert result == (0, 0, 1)


def test_z_axis_maps_to_neg_y():
    """Rhino Z (up) should map to Blender -Y (into screen)."""
    pt = _MockPoint(0, 0, 1)
    result = _transform_vertex(pt, 1.0)
    assert result == (0, -1, 0)


def test_scale_applied():
    """Scale factor should be applied to all axes."""
    pt = _MockPoint(1, 2, 3)
    result = _transform_vertex(pt, 0.001)
    assert abs(result[0] - 0.001) < 1e-10
    assert abs(result[1] - (-0.003)) < 1e-10
    assert abs(result[2] - 0.002) < 1e-10


def test_negative_coordinates():
    """Negative coordinates should transform correctly."""
    pt = _MockPoint(-5, -10, -15)
    result = _transform_vertex(pt, 1.0)
    assert result == (-5, 15, -10)
