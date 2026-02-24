"""Tests for Rhino face index normalization."""


def _build_face_list_standalone(faces_raw):
    """
    Standalone version of meshes._build_face_list for testing without bpy.

    Takes raw 4-tuples and normalizes triangles.
    """
    faces = []
    for a, b, c, d in faces_raw:
        if c == d:
            faces.append((a, b, c))
        else:
            faces.append((a, b, c, d))
    return faces


def test_triangle_detection():
    """Rhino triangles stored as (a, b, c, c) should become (a, b, c)."""
    raw = [(0, 1, 2, 2)]
    result = _build_face_list_standalone(raw)
    assert result == [(0, 1, 2)]


def test_quad_passthrough():
    """Quads with 4 distinct indices should pass through unchanged."""
    raw = [(0, 1, 2, 3)]
    result = _build_face_list_standalone(raw)
    assert result == [(0, 1, 2, 3)]


def test_mixed_faces():
    """Mix of triangles and quads should be handled correctly."""
    raw = [
        (0, 1, 2, 2),    # triangle
        (3, 4, 5, 6),    # quad
        (7, 8, 9, 9),    # triangle
        (10, 11, 12, 13),  # quad
    ]
    result = _build_face_list_standalone(raw)
    assert result == [
        (0, 1, 2),
        (3, 4, 5, 6),
        (7, 8, 9),
        (10, 11, 12, 13),
    ]


def test_degenerate_zero_indices():
    """Face where c == d == 0 (all zeros) should still be detected as triangle."""
    raw = [(0, 1, 0, 0)]
    result = _build_face_list_standalone(raw)
    assert result == [(0, 1, 0)]
