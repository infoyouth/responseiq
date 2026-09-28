from tree_sitter_language_pack import get_language, get_parser

try:
    print("Testing get_language('python')...")
    python_lang = get_language("python")
    print("Language object:", python_lang)
    print("Testing get_parser('python')...")
    python_parser = get_parser("python")
    print("Parser object:", python_parser)
    print("SUCCESS: tree-sitter-language-pack basic usage works.")
except Exception as e:
    print("ERROR:", e)
    import traceback
    traceback.print_exc()
