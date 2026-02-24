"""
Rhino curves → Blender curve objects.

Handles: NurbsCurve, PolylineCurve, LineCurve, ArcCurve.

Limitations:
- Blender NURBS splines cannot store explicit non-uniform knot vectors.
  Curves with exotic knots will be approximated using endpoint clamping.
- ArcCurves are approximated by converting to NurbsCurve first.
"""

import bpy
import rhino3dm


def _transform_point(pt, scale):
    """Rhino Y-up → Blender Z-up coordinate transform."""
    return (pt.X * scale, -pt.Z * scale, pt.Y * scale)


def _is_clamped(nc):
    """
    Check if a NURBS curve has a clamped (endpoint-interpolating) knot vector.

    A clamped curve has knot multiplicity >= degree at both ends.
    """
    degree = nc.Degree
    knots = nc.Knots
    if knots.Count < 2:
        return True

    # Check start multiplicity
    start_val = knots[0]
    start_mult = sum(1 for i in range(knots.Count) if abs(knots[i] - start_val) < 1e-10)

    # Check end multiplicity
    end_val = knots[knots.Count - 1]
    end_mult = sum(1 for i in range(knots.Count) if abs(knots[i] - end_val) < 1e-10)

    return start_mult >= degree and end_mult >= degree


def _add_nurbs_spline(curve_data, nc, scale, warnings, name):
    """Add a NURBS spline to a Blender curve data block."""
    spline = curve_data.splines.new('NURBS')
    pts = nc.Points

    # splines.new() creates 1 point by default, add the rest
    spline.points.add(pts.Count - 1)

    for i in range(pts.Count):
        cp = pts[i]
        x, y, z = _transform_point(cp, scale)
        w = cp.W if hasattr(cp, 'W') else 1.0
        spline.points[i].co = (x, y, z, w)

    spline.order_u = nc.Degree + 1
    spline.use_cyclic_u = nc.IsClosed

    # Blender approximates clamped knots with use_endpoint_u
    clamped = _is_clamped(nc)
    spline.use_endpoint_u = clamped

    if not clamped:
        warnings.append(
            f"'{name}': Non-uniform knot vector detected. "
            f"Blender approximates this with endpoint clamping — "
            f"curve shape may differ from Rhino."
        )


def _add_poly_spline(curve_data, polyline_curve, scale):
    """Add a polyline as a POLY spline to a Blender curve data block."""
    spline = curve_data.splines.new('POLY')

    # Get polyline points
    pt_count = polyline_curve.PointCount
    spline.points.add(pt_count - 1)

    for i in range(pt_count):
        pt = polyline_curve.Point(i)
        x, y, z = _transform_point(pt, scale)
        spline.points[i].co = (x, y, z, 1.0)

    spline.use_cyclic_u = polyline_curve.IsClosed


def _add_line_as_poly(curve_data, line_curve, scale):
    """Add a line as a 2-point POLY spline."""
    spline = curve_data.splines.new('POLY')
    spline.points.add(1)  # 2 points total

    pt_from = line_curve.PointAtStart
    pt_to = line_curve.PointAtEnd

    x0, y0, z0 = _transform_point(pt_from, scale)
    x1, y1, z1 = _transform_point(pt_to, scale)

    spline.points[0].co = (x0, y0, z0, 1.0)
    spline.points[1].co = (x1, y1, z1, 1.0)


def convert_curve(geometry, name, unit_scale):
    """
    Convert a Rhino curve to a Blender curve data block.

    Args:
        geometry: rhino3dm curve geometry
        name: Object name
        unit_scale: Scale factor from units.get_scale()

    Returns:
        tuple: (bpy.types.Curve or None, list of warning strings)
    """
    warnings = []

    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 12

    if isinstance(geometry, rhino3dm.NurbsCurve):
        _add_nurbs_spline(curve_data, geometry, unit_scale, warnings, name)

    elif isinstance(geometry, rhino3dm.PolylineCurve):
        _add_poly_spline(curve_data, geometry, unit_scale)

    elif isinstance(geometry, rhino3dm.LineCurve):
        _add_line_as_poly(curve_data, geometry, unit_scale)

    elif isinstance(geometry, rhino3dm.ArcCurve):
        # Convert arc to NURBS, then import as NURBS spline
        nc = geometry.ToNurbsCurve()
        if nc:
            _add_nurbs_spline(curve_data, nc, unit_scale, warnings, name)
        else:
            # Fallback: sample points along the arc
            _add_sampled_curve(curve_data, geometry, unit_scale)

    else:
        # Generic fallback: try ToNurbsCurve()
        nc = None
        if hasattr(geometry, 'ToNurbsCurve'):
            nc = geometry.ToNurbsCurve()

        if nc:
            _add_nurbs_spline(curve_data, nc, unit_scale, warnings, name)
        else:
            bpy.data.curves.remove(curve_data)
            geom_type = type(geometry).__name__
            warnings.append(
                f"'{name}': Unsupported curve type '{geom_type}', skipped."
            )
            return None, warnings

    return curve_data, warnings


def _add_sampled_curve(curve_data, geometry, scale, samples=32):
    """Fallback: sample points along a curve and create a POLY spline."""
    spline = curve_data.splines.new('POLY')
    spline.points.add(samples - 1)

    domain = geometry.Domain
    t_start = domain.T0
    t_end = domain.T1

    for i in range(samples):
        t = t_start + (t_end - t_start) * (i / (samples - 1))
        pt = geometry.PointAt(t)
        x, y, z = _transform_point(pt, scale)
        spline.points[i].co = (x, y, z, 1.0)

    spline.use_cyclic_u = geometry.IsClosed
