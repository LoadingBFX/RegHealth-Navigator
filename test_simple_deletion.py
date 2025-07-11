#!/usr/bin/env python3
"""
简单删除测试 - 只测试删除功能，不包含复杂的恢复逻辑
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'app'))

from app.core.preprocessing.incremental_manager import IncrementalManager

def test_simple_deletion():
    """简单删除测试"""
    print("🧪 简单删除功能测试")
    print("=" * 40)
    
    # 初始化管理器
    manager = IncrementalManager('data', 'rag_data')
    
    # 获取初始状态
    chunks = manager._load_chunks()
    initial_chunk_count = len(chunks)
    initial_vector_count = manager.faiss_builder.index.ntotal if manager.faiss_builder.index else 0
    
    print(f"🔍 初始状态:")
    print(f"  总chunks: {initial_chunk_count:,}")
    print(f"  索引向量: {initial_vector_count:,}")
    print(f"  元数据条目: {len(manager.faiss_builder.metadata):,}")
    
    # 查找有chunks的文件
    file_counts = {}
    for chunk in chunks:
        source_file = chunk.get('metadata', {}).get('source_file', 'UNKNOWN')
        file_counts[source_file] = file_counts.get(source_file, 0) + 1
    
    # 选择一个小文件进行测试
    suitable_files = [(f, c) for f, c in file_counts.items() 
                     if f != 'UNKNOWN' and f.endswith('.xml') and c > 0]
    
    if not suitable_files:
        print("❌ 没有找到合适的测试文件")
        return
    
    # 选择chunk数最少的文件
    test_file, chunk_count = min(suitable_files, key=lambda x: x[1])
    print(f"\n🎯 测试删除文件: {test_file}")
    print(f"  要删除的chunks: {chunk_count:,}")
    
    # 直接调用删除函数（不通过装饰器）
    try:
        print("\n🗑️ 开始删除...")
        
        # 手动执行删除步骤以避免装饰器干扰
        chunks = manager._load_chunks()
        filtered_chunks, chunks_removed = manager._remove_file_chunks(chunks, test_file)
        
        print(f"  从chunks中移除: {chunks_removed:,}")
        
        # 保存更新的chunks
        save_result = manager._save_chunks(filtered_chunks)
        print(f"  保存chunks结果: {save_result['status']}")
        
        # 尝试重组索引
        reorganize_result = manager._rebuild_index_by_reorganization(chunks, filtered_chunks, chunks_removed)
        print(f"  重组结果: {reorganize_result}")
        
        # 保存索引
        if manager.faiss_builder.index:
            save_index_result = manager.faiss_builder.save_index(
                manager.index_path, 
                manager.metadata_path
            )
            print(f"  保存索引结果: {save_index_result['status']}")
        
        # 检查最终状态
        final_chunks = manager._load_chunks()
        final_vector_count = manager.faiss_builder.index.ntotal if manager.faiss_builder.index else 0
        
        print(f"\n✅ 删除完成:")
        print(f"  最终chunks: {len(final_chunks):,}")
        print(f"  最终向量: {final_vector_count:,}")
        print(f"  chunks变化: {initial_chunk_count - len(final_chunks):,}")
        print(f"  向量变化: {initial_vector_count - final_vector_count:,}")
        
        # 验证文件确实被删除
        remaining_chunks_for_file = 0
        for chunk in final_chunks:
            if chunk.get('metadata', {}).get('source_file') == test_file:
                remaining_chunks_for_file += 1
        
        print(f"  目标文件剩余chunks: {remaining_chunks_for_file}")
        
        if remaining_chunks_for_file == 0:
            print(f"  ✅ 文件 {test_file} 已完全删除")
        else:
            print(f"  ❌ 文件 {test_file} 未完全删除")
        
        # 检查是否使用了高效删除
        if reorganize_result.get('efficient_removal'):
            print(f"  ✅ 使用了高效删除（remove_ids）")
        elif reorganize_result.get('fallback_rebuild'):
            print(f"  ⚠️ 使用了fallback重建")
        
        return True
        
    except Exception as e:
        print(f"❌ 删除失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_deletion()
    sys.exit(0 if success else 1)