from src.extractors.python import PythonExtractor


def test_python_extractor(tmp_path):
    # Setup python file
    src = tmp_path / "src"
    src.mkdir()
    f = src / "test.py"
    f.write_text("""
import os

class MyClass:
    def method(self):
        pass

def func():
    pass
""")

    extractor = PythonExtractor()
    nodes = list(extractor.extract(tmp_path))

    types = [n["type"] for n in nodes]
    assert "File" in types
    assert "Module" in types
    assert "Class" in types
    assert "Function" in types

    # Check properties
    cls = next(n for n in nodes if n["type"] == "Class")
    assert cls["properties"]["name"] == "MyClass"

    func = next(n for n in nodes if n["type"] == "Function")
    assert func["properties"]["name"] == "func"


def test_python_relationships(tmp_path):
    f = tmp_path / "main.py"
    f.write_text("import utils")

    extractor = PythonExtractor()
    rels = list(extractor.extract_relationships(tmp_path))

    assert len(rels) > 0
    assert rels[0]["type"] == "IMPORTS"
