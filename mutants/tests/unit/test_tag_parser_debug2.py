from bs4 import BeautifulSoup

from responseiq.services.tag_parser import extract_tag_block


def test_bs4_tag_names():
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
    soup = BeautifulSoup(llm_output, "lxml")
    print([tag.name for tag in soup.find_all()])
    patch = extract_tag_block(llm_output, "PATCH")
    print(f"PATCH: {patch!r}")
    assert patch is not None
