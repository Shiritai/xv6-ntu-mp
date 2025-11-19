import sys
from fslab_interpreter import interpreter

if __name__ == '__main__':
    output = []
    # Use a default file path, but allow overriding from command line
    file_path = "./meow.txt"
    if len(sys.argv) > 1:
        file_path = sys.argv[1]

    try:
        with open(file_path, "r") as f:
            output = list(map(lambda l: l.strip(), f.readlines()))
    except FileNotFoundError:
        print(f"Error: Could not find file at {file_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    # You can set verbose to True here if needed for debugging
    # e.g., interpreter(output, True)
    try:
        interpreter(output, True)
        print("\n<Info> All checks passed.")
    except AssertionError as e:
        print("\n--- CHECK FAILED ---", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)