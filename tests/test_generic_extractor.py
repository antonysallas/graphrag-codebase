from src.extractors.generic import GenericExtractor


def test_generic_extractor(tmp_path):
    d = tmp_path / "subdir"
    d.mkdir()
    f = d / "data.txt"
    f.write_text("content")

    extractor = GenericExtractor()
    nodes = list(extractor.extract(tmp_path))

    types = [n["type"] for n in nodes]
    assert "Directory" in types
    assert "File" in types

    f_node = next(n for n in nodes if n["type"] == "File")
    assert f_node["properties"]["name"] == "data.txt"


def test_generic_relationships(tmp_path):
    d = tmp_path / "subdir"
    d.mkdir()
    f = d / "data.txt"
    f.write_text("content")

    extractor = GenericExtractor()
    rels = list(extractor.extract_relationships(tmp_path))

    assert len(rels) > 0
    assert rels[0]["type"] == "CONTAINS"
