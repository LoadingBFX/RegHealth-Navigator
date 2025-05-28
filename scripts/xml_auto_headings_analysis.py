"""
xml_auto_headings_analysis.py

Script to analyze XML tags, print tag frequencies, sample contents, auto-infer likely title, heading, and paragraph tags, and count total words/tokens.

Usage:
    python scripts/xml_auto_headings_analysis.py data/2025-06008.xml
"""
import sys
from lxml import etree
from collections import Counter, defaultdict
import re

def get_text(elem, max_words=8):
    if elem is None or elem.text is None:
        return ''
    words = elem.text.strip().split()
    if len(words) > max_words:
        return ' '.join(words[:max_words]) + ' ...'
    return ' '.join(words)

def is_heading(text):
    if not text:
        return False
    # Heuristic: all caps, short, or starts with number/letter and dot
    if text.isupper() and len(text.split()) <= 10:
        return True
    if re.match(r'^[A-Z]?[0-9]+[\.-]', text):
        return True
    if len(text.split()) <= 8 and text.istitle():
        return True
    return False

def main(xml_path):
    tree = etree.parse(xml_path)
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
            total_tokens += word_count  # Simple whitespace tokenization

    print('=== Tag Frequency & Sample Content ===')
    for tag, count in tag_counter.most_common():
        print(f'- {tag}: {count}')
        for i, sample in enumerate(tag_samples[tag]):
            print(f'    Sample {i+1}: {sample}')
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

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python scripts/xml_auto_headings_analysis.py <xml_file>')
        sys.exit(1)
    main(sys.argv[1]) 