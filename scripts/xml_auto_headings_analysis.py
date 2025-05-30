"""
xml_auto_headings_analysis.py

Script to analyze XML tags, print tag frequencies, sample contents, auto-infer likely title, heading, and paragraph tags, count total words/tokens, and build a section tree for structural tags (e.g., HD, FP, AMDPAR).

Usage:
    python scripts/xml_auto_headings_analysis.py data/2025-06008.xml

Data format for section tree:
    {
        'tag': str,  # e.g., 'HD'
        'text': str, # text content
        'children': [ ... ] # list of child nodes (same structure)
    }
"""
import sys
from lxml import etree
from collections import Counter, defaultdict
import re

try:
    import tiktoken
except ImportError:
    tiktoken = None
    print("Warning: tiktoken not installed, token count will be word count.")

SECTION_TAGS = {'HD', 'FP', 'AMDPAR'}  # 可根据实际需要扩展

# Tag priority levels for section tree construction
TAG_LEVELS = {
    'RULE': 0,
    'PREAMB': 1, 'SUPLINF': 1, 'REGTEXT': 1,
    'HD': 2,
    'FP': 3, 'AMDPAR': 3, 'SECTION': 3, 'SUBPART': 3,
    'P': 4, 'E': 4, 'FTNT': 4, 'NOTE': 4,
    'PRTPAGE': 5, 'GID': 5, 'BILCOD': 5, 'AUTH': 5
}

# Helper to get tag level, default to 99 for unknown tags
get_tag_level = lambda tag: TAG_LEVELS.get(tag, 99)

def get_text(elem, max_words=8):
    """
    Get a short preview of element text.
    """
    if elem is None or elem.text is None:
        return ''
    words = elem.text.strip().split()
    if len(words) > max_words:
        return ' '.join(words[:max_words]) + ' ...'
    return ' '.join(words)

def is_heading(text):
    """
    Heuristic to determine if text looks like a heading.
    """
    if not text:
        return False
    if text.isupper() and len(text.split()) <= 10:
        return True
    if re.match(r'^[A-Z]?[0-9]+[\.-]', text):
        return True
    if len(text.split()) <= 8 and text.istitle():
        return True
    return False

def count_tokens(text, encoding_name='cl100k_base'):
    """
    Count tokens using tiktoken if available, else fallback to word count.
    >>> count_tokens('This is a test.') > 0
    True
    """
    if not text:
        return 0
    if tiktoken:
        enc = tiktoken.get_encoding(encoding_name)
        return len(enc.encode(text))
    else:
        return len(text.strip().split())

def build_section_tree(elem, parent_level=-1):
    """
    Build a nested section tree according to tag priority levels.
    Returns a list of section nodes.
    Each node: {'tag': str, 'text': str, 'children': list}
    """
    nodes = []
    for child in elem:
        tag = child.tag
        level = get_tag_level(tag)
        node = {
            'tag': tag,
            'text': get_text(child, 20),
            'children': build_section_tree(child, level)
        }
        nodes.append(node)
    return nodes

def print_section_tree(nodes, level=0, max_words=5, max_per_tag=3):
    """
    Pretty print the section tree, showing structure and a short content preview.
    At each level, group by tag, show up to max_per_tag examples per tag, recursively.
    Each node shows only the first max_words words of its text, with ellipsis if longer.
    """
    tag_groups = defaultdict(list)
    for node in nodes:
        tag_groups[node['tag']].append(node)
    for tag, group in tag_groups.items():
        for i, node in enumerate(group):
            if i >= max_per_tag:
                print('  ' * level + f"... ({len(group) - max_per_tag} more {tag})")
                break
            words = node['text'].split()
            text = ' '.join(words[:max_words])
            if len(words) > max_words:
                text += ' ...'
            print('  ' * level + f"- {node['tag']}: {text}")
            print_section_tree(node['children'], level+1, max_words, max_per_tag)

def main(xml_path):
    """
    Main analysis function.
    Args:
        xml_path (str): Path to XML file.
    """
    try:
        tree = etree.parse(xml_path)
    except Exception as e:
        print(f"Error parsing XML: {e}")
        sys.exit(1)
    root = tree.getroot()

    tag_counter = Counter()
    tag_samples = defaultdict(list)
    tag_lengths = defaultdict(list)
    total_words = 0
    total_tokens = 0

    # Traverse all elements, collect stats and count words/tokens
    for elem in root.iter():
        tag_counter[elem.tag] += 1
        if elem.text and elem.text.strip():
            sample = get_text(elem, 12)
            if len(tag_samples[elem.tag]) < 3:
                tag_samples[elem.tag].append(sample)
            word_count = len(elem.text.strip().split())
            tag_lengths[elem.tag].append(word_count)
            total_words += word_count
            total_tokens += count_tokens(elem.text)

    print('=== Tag Frequency & Sample Content ===')
    for tag, count in tag_counter.most_common():
        print(f'- {tag}: {count}')
        for i, sample in enumerate(tag_samples[tag]):
            print(f'    Sample {i+1}: {sample}')
    print()

    # Print likely heuristics explanation
    print('=== Heuristics for "Likely" Tags ===')
    print('- Likely title: tag that appears only once and has no more than 15 words.')
    print('- Likely heading: tag that appears 5-200 times, with short text that looks like a heading (all caps, numbered, or title case).')
    print('- Likely paragraph: tag that appears more than 100 times and has at least one sample with more than 10 words.')
    print()

    # Heuristic: likely title tag is the first tag with only one occurrence and short text
    likely_title = None
    for tag, count in tag_counter.items():
        if count == 1 and tag_samples[tag]:
            text = tag_samples[tag][0]
            if len(text.split()) <= 15:
                likely_title = (tag, text)
                break
    print('=== Likely Article Title ===')
    if likely_title:
        print(f'Tag: {likely_title[0]} | Content: {likely_title[1]}')
    else:
        print('Not found')
    print()

    # Heuristic: likely heading tags are those with moderate frequency, short text, and heading-like features
    heading_candidates = []
    for tag, samples in tag_samples.items():
        if 5 <= tag_counter[tag] <= 200:
            for s in samples:
                if is_heading(s):
                    heading_candidates.append((tag, s))
                    break
    heading_tags = sorted(set([t for t, _ in heading_candidates]))
    print('=== Likely Heading Tags ===')
    for tag in heading_tags:
        print(f'- {tag} (count: {tag_counter[tag]})')
        for s in tag_samples[tag]:
            if is_heading(s):
                print(f'    Example: {s}')
    print()

    # Heuristic: likely paragraph tags are those with high frequency and long text
    para_candidates = []
    for tag, lens in tag_lengths.items():
        if tag_counter[tag] > 100 and sum(l > 10 for l in lens) > 0:
            para_candidates.append(tag)
    print('=== Likely Paragraph Tags ===')
    for tag in para_candidates:
        print(f'- {tag} (count: {tag_counter[tag]})')
        for s in tag_samples[tag]:
            print(f'    Example: {s}')
    print()

    # Print summary
    print('=== Summary ===')
    print(f'Article title tag: {likely_title[0] if likely_title else "Not found"}')
    print(f'Heading tags: {", ".join(heading_tags) if heading_tags else "Not found"}')
    print(f'Paragraph tags: {", ".join(para_candidates) if para_candidates else "Not found"}')
    print()

    # Print total word/token count
    print('=== Word/Token Count ===')
    print(f'Total words: {total_words}')
    print(f'Total tokens: {total_tokens}')
    print()

    # Build and print section tree (all tags)
    print('=== Section Tree (all tags, grouped, up to 3 per tag per level) ===')
    section_tree = build_section_tree(root)
    if section_tree:
        print_section_tree(section_tree)
    else:
        print('No section structure found.')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python scripts/xml_auto_headings_analysis.py <xml_file>')
        sys.exit(1)
    main(sys.argv[1]) 