import pytest

from pseudo_fslab import (
    normalize_spaces,
    parse_dict,
    hex_to_int,
    is_in_same_page
)

# --- Test normalize_spaces ---
# Create a list of test cases: (input, expected_output)
normalize_test_cases = [
    ("hello   world", "hello world"),               # 1. Basic case: multiple spaces
    ("  hello world", "hello world"),               # 2. Leading spaces
    ("hello world  ", "hello world"),               # 3. Trailing spaces
    ("  hello   world  ", "hello world"),           # 4. Leading and trailing spaces
    ("\thello\nworld\r\n", "hello world"),          # 5. Mixed whitespace (tab, newline)
    ("  \t hello \n  world \r\n ", "hello world"),  # 6. Complex mixed whitespace
    ("hello world", "hello world"),                 # 7. String requiring no change
    ("hello", "hello"),                             # 8. Single word
    ("", ""),                                       # 9. Empty string
    ("   \t \n ", ""),                              # 10. Whitespace only
]

@pytest.mark.parametrize("input_text, expected_output", normalize_test_cases)
def test_normalize_spaces(input_text, expected_output):
    """
    Test that normalize_spaces correctly handles various whitespace characters.
    """
    assert normalize_spaces(input_text) == expected_output


# --- Test hex_to_int ---
@pytest.mark.parametrize("hex_str, expected_int", [
    ("0xff", 255),
    ("FF", 255),
    ("0x100", 256),
    ("100", 256),
    ("0", 0),
    ("0x0", 0),
    ("0xaB", 171),
])
def test_hex_to_int_valid(hex_str, expected_int):
    """
    Test hex_to_int with valid hexadecimal strings.
    """
    assert hex_to_int(hex_str) == expected_int

@pytest.mark.parametrize("invalid_str", [
    "G",          # Contains invalid characters
    "0xG",
    "",           # Empty string
    "1 2",        # Contains spaces
])
def test_hex_to_int_invalid(invalid_str):
    """
    Test that hex_to_int raises an AssertionError for invalid input.
    """
    # Check that an AssertionError is raised
    with pytest.raises(AssertionError, match="Invalid hex string"):
        hex_to_int(invalid_str)


# --- Test is_in_same_page ---
# 4095 == 0xFFF (4KB page size - 1)
@pytest.mark.parametrize("addr_a, addr_b, expected", [
    (0x1000, 0x1001, True),     # Same page
    (0x1000, 0x1FFF, True),     # Same page (boundary)
    (0x1FFF, 0x2000, False),    # Different page (boundary)
    (0x0, 0xFFF, True),         # Zero Page
    (0x0, 0x1000, False),       # Zero Page vs Page 1
    (0x8011c000, 0x8011c008, True), # Addresses from example logs
    (0x8011c000, 0x8011d000, False),# Addresses from example logs (different page)
])
def test_is_in_same_page(addr_a, addr_b, expected):
    """
    Test if is_in_same_page correctly identifies 4KB page boundaries.
    """
    assert is_in_same_page(addr_a, addr_b) == expected


# --- Test parse_dict ---
def test_parse_dict_simple():
    """
    Test parse_dict with a standard, valid dictionary string.
    """
    s = "{ 'freelist': 0x123, 'nxt': 0x456, 'name': 'test' }"
    expected = {'freelist': 0x123, 'nxt': 0x456, 'name': 'test'}
    assert parse_dict(s) == expected

def test_parse_dict_with_undefined_names():
    """
    Test parse_dict's ability to handle the special eval/exec logic
    from the original code (e.g., PIPE may not be a defined Python variable).
    """
    # Example from SlabPrintfObjStatusData
    s = "{ 'tp': 0, 'ref': 1, 'type': PIPE }"
    
    # 'PIPE' is expected to be treated as the string "PIPE"
    expected = {'tp': 0, 'ref': 1, 'type': "PIPE"}
    assert parse_dict(s) == expected

def test_parse_dict_invalid_syntax():
    """
    Test parse_dict with invalid Python syntax.
    """
    s = "{ 'a': 1, " # Missing closing brace
    
    # Check that an AssertionError is raised
    with pytest.raises(AssertionError, match="Invalid string"):
        parse_dict(s)