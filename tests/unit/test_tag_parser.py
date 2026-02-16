from responseiq.services.tag_parser import extract_tag_block


def test_extract_patch_block():
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
    assert patch.startswith("--- a/foo.py")
    assert "def test_bug()" in test


def test_missing_tag_returns_none():
    llm_output = "No tags here."
    assert extract_tag_block(llm_output, "PATCH") is None
