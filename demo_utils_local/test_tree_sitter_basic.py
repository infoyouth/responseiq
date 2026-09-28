from tree_sitter_languages import get_language, get_parser

try:
    print("Testing get_language('python')...")
    language = get_language('python')
    print("Language object:", language)
    print("Testing get_parser('python')...")
    parser = get_parser('python')
    print("Parser object:", parser)
    print("SUCCESS: tree-sitter-languages basic usage works.")
except Exception as e:
    print("ERROR:", e)
    import traceback
    traceback.print_exc()
