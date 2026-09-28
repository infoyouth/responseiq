from responseiq.services.tag_parser import extract_tag_block


def test_debug_patch():
    llm_output = """
    <PATCH>
    --- a/foo.py
    +++ b/foo.py
    @@ ...
    </PATCH>
    <REPRO_TEST>
    def test_bug():
        assert True
    </REPRO_TEST>
    """
    patch = extract_tag_block(llm_output, "PATCH")
    test = extract_tag_block(llm_output, "REPRO_TEST")
    print(f"PATCH: {patch!r}")
    print(f"TEST: {test!r}")
    assert patch is not None
    assert test is not None
