"""Tests for unit scale conversion."""

import sys
import os

# Add deps to path so rhino3dm can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'deps', '_extracted'))

import rhino3dm

from io_import_3dm.pipeline.units import get_scale


def test_millimeters():
    assert get_scale(rhino3dm.UnitSystem.Millimeters) == 0.001


def test_centimeters():
    assert get_scale(rhino3dm.UnitSystem.Centimeters) == 0.01


def test_meters():
    assert get_scale(rhino3dm.UnitSystem.Meters) == 1.0


def test_inches():
    assert abs(get_scale(rhino3dm.UnitSystem.Inches) - 0.0254) < 1e-10


def test_feet():
    assert abs(get_scale(rhino3dm.UnitSystem.Feet) - 0.3048) < 1e-10


def test_kilometers():
    assert get_scale(rhino3dm.UnitSystem.Kilometers) == 1000.0


def test_unknown_returns_1():
    """Unknown unit system should default to scale 1.0."""
    assert get_scale(rhino3dm.UnitSystem.None_) == 1.0
