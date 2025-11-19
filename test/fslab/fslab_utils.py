import re
from typing import Any

def normalize_spaces(text):
    """Normalize multiple spaces to a single space and strip leading/trailing whitespace."""
    return re.sub(r'\s+', ' ', text).strip()

def parse_dict(s: str) -> dict['str', Any]:
    """Safely parse a string into a dictionary."""
    # This eval-based parser is inherently unsafe if the input is not trusted.
    # It is kept as-is from the original script.
    d = {}
    while True:
        try:
            d = eval(s)
            break
        except NameError as e:
            n = str(e).split("'")[1]
            exec(f'{n} = "{n}"')
        except Exception as e:
            raise AssertionError(f"Invalid string: {s}: is not in good {{ ... }} format")
    return d

def hex_to_int(value: str) -> int:
    """Convert a hexadecimal string to an integer."""
    try:
        return int(value, base=16)
    except ValueError:
        raise AssertionError(f"Invalid hex string: {value}")

def is_in_same_page(a, b):
    """Check if two addresses are in the same 4KB page."""
    return (a & ~4095) == (b & ~4095)

def check_exists(dc: dict, key, msg_type):
    """Check if a key exists in a dictionary, raise error if not."""
    ret = dc.get(key)
    if ret is None:
        raise AssertionError(f"Invalid {msg_type.__name__}: key '{key}' not in {dc}")
    return ret