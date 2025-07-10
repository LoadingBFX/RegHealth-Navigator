#!/usr/bin/env python3
"""
test_optimized_chunker.py

测试优化后的XML chunker功能。

Author: Fanxing Bu
Date: 2024-12-19
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.optimized_xml_chunker import OptimizedXMLChunker
from app.config.xml_labels_config import xml_label_config

def test_label_config():
    """测试标签配置功能。"""
    print("=== 测试标签配置 ===")
    
    # 测试标签分类
    test_labels = ["P", "AGENCY", "PRTPAGE", "E", "HD", "SECTION"]
    
    for label in test_labels:
        category = xml_label_config.get_label_category(label)
        should_include = xml_label_config.should_include_in_chunk(label)
        should_metadata = xml_label_config.should_extract_metadata(label)
        
        print(f"{label}: category={category.value}, include_in_chunk={should_include}, metadata={should_metadata}")
    
    print()

def test_chunker_on_sample_file():
    """测试chunker在样本文件上的表现。"""
    print("=== 测试优化Chunker ===")
    
    chunker = OptimizedXMLChunker(chunk_size=800, overlap=100)
    
    # 测试单个文件
    test_file = "data/HOSPICE/2022_HOSPICE_final_2021-16311.xml"
    
    if os.path.exists(test_file):
        print(f"处理文件: {test_file}")
        chunks = chunker.process_file(test_file)
        
        print(f"生成了 {len(chunks)} 个chunks")
        
        # 显示前3个chunks的详细信息
        for i, chunk in enumerate(chunks[:3]):
            print(f"\nChunk {i}:")
            print(f"  Type: {chunk['metadata'].get('chunk_type', 'unknown')}")
            print(f"  Section: {chunk['metadata'].get('section', 'unknown')}")
            print(f"  Size: {len(chunk['text'])} characters")
            print(f"  Text preview: {chunk['text'][:100]}...")
    else:
        print(f"测试文件不存在: {test_file}")
    
    print()

def test_chunk_types():
    """测试不同chunk类型的生成。"""
    print("=== 测试Chunk类型 ===")
    
    chunker = OptimizedXMLChunker(chunk_size=1000, overlap=200)
    
    # 创建测试XML
    test_xml = """<?xml version="1.0"?>
<RULE>
    <PREAMB>
        <AGENCY>Test Agency</AGENCY>
        <SUBJECT>Test Subject for Chunking</SUBJECT>
        <SUM>
            <P>This is a summary paragraph that should be included in the summary chunk.</P>
        </SUM>
        <DATES>
            <P>Effective date: January 1, 2024</P>
        </DATES>
    </PREAMB>
    <SUPLINF>
        <HD SOURCE="HED">Main Section</HD>
        <P>This is a regular paragraph with <E T="03">important text</E> that should be chunked.</P>
        <HD SOURCE="HD1">Subsection</HD>
        <P>Another paragraph with <SU>1</SU> footnote reference.</P>
        <FTNT>
            <P>This is footnote content that should be included.</P>
        </FTNT>
    </SUPLINF>
</RULE>"""
    
    # 保存测试XML
    test_file = "test_sample.xml"
    with open(test_file, "w") as f:
        f.write(test_xml)
    
    try:
        chunks = chunker.process_file(test_file)
        
        print(f"生成了 {len(chunks)} 个chunks")
        
        # 分析chunk类型
        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk['metadata'].get('chunk_type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        print("Chunk类型分布:")
        for chunk_type, count in chunk_types.items():
            print(f"  {chunk_type}: {count}")
        
        # 显示每个chunk的详细信息
        for i, chunk in enumerate(chunks):
            print(f"\nChunk {i} ({chunk['metadata'].get('chunk_type', 'unknown')}):")
            print(f"  Section: {chunk['metadata'].get('section', 'unknown')}")
            print(f"  Size: {len(chunk['text'])} characters")
            print(f"  Content: {chunk['text'][:150]}...")
    
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
    
    print()

def main():
    """主测试函数。"""
    print("🧪 优化XML Chunker测试")
    print("=" * 50)
    
    test_label_config()
    test_chunker_on_sample_file()
    test_chunk_types()
    
    print("✅ 测试完成")

if __name__ == "__main__":
    main() 