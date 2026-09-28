from tree_sitter_language_pack import get_language, get_parser
try:
    print("Getting language python...")
    lang = get_language("python")
    print("Got language: {}".format(lang))
    print("Getting parser python...")
    parser = get_parser("python")
    print("Got parser: {}".format(parser))
except Exception as e:
    print("Error: {}".format(e))
    import traceback
    traceback.print_exc()
