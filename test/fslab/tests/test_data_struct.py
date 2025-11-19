import sys
import os
import pytest

from pseudo_fslab import (
    BaseData,
    AddrData,
    SlabCreateData
)

def test_base_data_initialization():
    """
    Test that BaseData correctly stores the 'origin' string upon initialization.
    """
    origin_line = "This is the original log line."
    data = BaseData(origin=origin_line)
    
    assert data.origin == origin_line

def test_base_data_str_representation():
    """
    Test that the __str__ method of BaseData returns the 'origin' string.
    """
    origin_line = "New kmem_cache (name: test, object size: 128)"
    data = BaseData(origin=origin_line)
    
    assert str(data) == origin_line

def test_base_data_with_empty_string():
    """
    Test the edge case where the origin string is empty.
    """
    origin_line = ""
    data = BaseData(origin=origin_line)
    
    assert data.origin == ""
    assert str(data) == ""

def test_base_data_with_complex_string():
    """
    Test with a more complex string containing special characters.
    """
    origin_line = "[ slab 0x80001000 ] { 'freelist': 0, 'nxt': 0 }"
    data = BaseData(origin=origin_line)
    
    assert data.origin == origin_line
    assert str(data) == origin_line