import pytest
from lxml import etree
from xml_auto_headings_analysis import get_text, is_heading, count_tokens, build_section_tree

def test_get_text():
    elem = etree.Element('p')
    elem.text = 'This is a test of the get_text function.'
    assert get_text(elem, 3) == 'This is a ...'
    assert get_text(elem, 10) == 'This is a test of the get_text function.'
    assert get_text(None) == ''
    elem2 = etree.Element('p')
    assert get_text(elem2) == ''

def test_is_heading():
    assert is_heading('CHAPTER I')
    assert is_heading('1. Introduction')
    assert is_heading('Section 2.1')
    assert not is_heading('This is a normal sentence.')
    assert is_heading('Short Title')
    assert not is_heading('')

def test_count_tokens():
    text = 'This is a test.'
    n = count_tokens(text)
    assert n > 0
    assert isinstance(n, int)
    assert count_tokens('') == 0

def test_build_section_tree():
    xml = '''<root><HD>Title</HD><FP>Preface</FP><AMDPAR>Amendment</AMDPAR><FP>Another</FP></root>'''
    root = etree.fromstring(xml)
    tree = build_section_tree(root)
    assert isinstance(tree, list)
    assert len(tree) == 4  # 2 FP, 1 HD, 1 AMDPAR
    tags = [n['tag'] for n in tree]
    assert set(tags) == {'HD', 'FP', 'AMDPAR', 'FP'}
    for node in tree:
        assert 'tag' in node and 'text' in node and 'children' in node 