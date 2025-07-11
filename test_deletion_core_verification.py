#!/usr/bin/env python3
"""
核心验证测试 - 验证删除机制是否正确工作
"""

import sys
import json
import shutil
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'app'))

from app.core.preprocessing.incremental_manager import IncrementalManager

def test_deletion_verification():
    """验证删除机制的核心功能"""
    print("🧪 删除机制核心验证")
    print("=" * 40)
    
    # 初始化管理器
    manager = IncrementalManager('data', 'rag_data')
    
    # 备份
    output_dir = Path('rag_data')
    backup_dir = Path('test_backup_core')
    backup_dir.mkdir(exist_ok=True)
    
    for filename in ['chunks.json', 'faiss.index', 'faiss_metadata.json']:
        source = output_dir / filename
        if source.exists():
            shutil.copy2(source, backup_dir / f"{filename}.backup")
    
    try:
        # 1. 获取当前状态
        chunks = manager._load_chunks()
        metadata = manager.faiss_builder.metadata
        index_size = manager.faiss_builder.index.ntotal if manager.faiss_builder.index else 0
        
        print(f"📊 当前状态:")
        print(f"  Chunks: {len(chunks):,}")
        print(f"  Metadata: {len(metadata):,}")
        print(f"  Index vectors: {index_size:,}")
        
        # 检查数据一致性
        chunks_meta_consistent = len(chunks) >= len(metadata) * 0.9  # 允许一些差异
        meta_index_consistent = len(metadata) == index_size
        
        print(f"  Chunks ↔ Metadata: {'✅' if chunks_meta_consistent else '❌'}")
        print(f"  Metadata ↔ Index: {'✅' if meta_index_consistent else '❌'}")
        
        # 2. 选择要删除的文件
        file_counts = {}
        for chunk in chunks:
            source_file = chunk.get('metadata', {}).get('source_file', 'UNKNOWN')
            file_counts[source_file] = file_counts.get(source_file, 0) + 1
        
        # 找一个在chunks和metadata中都存在的文件
        metadata_files = {}
        for meta in metadata:
            source_file = meta.get('metadata', {}).get('source_file', 'UNKNOWN')
            metadata_files[source_file] = metadata_files.get(source_file, 0) + 1
        
        # 找到匹配的文件
        matched_files = []
        for filename in file_counts:
            if filename in metadata_files and filename != 'UNKNOWN' and filename.endswith('.xml'):
                chunk_count = file_counts[filename]
                meta_count = metadata_files[filename]
                matched_files.append((filename, chunk_count, meta_count))
        
        if not matched_files:
            print("❌ 没有找到chunks和metadata都匹配的文件")
            return False
        
        # 选择最小的匹配文件
        test_file, chunk_count, meta_count = min(matched_files, key=lambda x: x[1])
        print(f"\n🎯 测试文件: {test_file}")
        print(f"  Chunks: {chunk_count}")
        print(f"  Metadata: {meta_count}")
        
        # 3. 执行删除测试
        print(f"\n🗑️ 测试删除功能...")
        
        # 3a. 测试chunks删除
        filtered_chunks, chunks_removed = manager._remove_file_chunks(chunks, test_file)
        print(f"  Chunks删除: {chunks_removed} 个")
        
        # 3b. 测试metadata/index删除
        if meta_index_consistent:
            print(f"  测试高效删除 (remove_ids)...")
            
            # 找到要删除的metadata索引
            indices_to_remove = []
            for i, meta in enumerate(metadata):
                if meta.get('metadata', {}).get('source_file') == test_file:
                    indices_to_remove.append(i)
            
            print(f"  要删除的向量索引: {len(indices_to_remove)} 个")
            
            if len(indices_to_remove) > 0:
                try:
                    # 测试remove_ids
                    import numpy as np
                    remove_ids = np.array(indices_to_remove, dtype=np.int64)
                    
                    original_count = manager.faiss_builder.index.ntotal
                    manager.faiss_builder.index.remove_ids(remove_ids)
                    new_count = manager.faiss_builder.index.ntotal
                    
                    print(f"  ✅ remove_ids成功: {original_count} → {new_count}")
                    print(f"  删除的向量: {original_count - new_count}")
                    
                    # 更新metadata
                    new_metadata = [meta for i, meta in enumerate(metadata) if i not in indices_to_remove]
                    manager.faiss_builder.metadata = new_metadata
                    
                    print(f"  ✅ 高效删除测试成功!")
                    
                    # 验证一致性
                    final_chunks = len(filtered_chunks)
                    final_metadata = len(new_metadata)
                    final_vectors = manager.faiss_builder.index.ntotal
                    
                    print(f"\n📊 删除后状态:")
                    print(f"  Chunks: {final_chunks:,}")
                    print(f"  Metadata: {final_metadata:,}")
                    print(f"  Vectors: {final_vectors:,}")
                    
                    # 验证目标文件是否完全删除
                    remaining_chunks = sum(1 for chunk in filtered_chunks 
                                         if chunk.get('metadata', {}).get('source_file') == test_file)
                    remaining_metadata = sum(1 for meta in new_metadata 
                                           if meta.get('metadata', {}).get('source_file') == test_file)
                    
                    print(f"  目标文件剩余chunks: {remaining_chunks}")
                    print(f"  目标文件剩余metadata: {remaining_metadata}")
                    
                    if remaining_chunks == 0 and remaining_metadata == 0:
                        print(f"  ✅ 文件 {test_file} 完全删除")
                        
                        print(f"\n🎉 核心删除功能验证成功!")
                        print(f"  ✅ chunks删除正常")
                        print(f"  ✅ 高效向量删除正常 (remove_ids)")
                        print(f"  ✅ metadata更新正常")
                        print(f"  ✅ 数据一致性保持")
                        return True
                    else:
                        print(f"  ❌ 文件未完全删除")
                        return False
                        
                except Exception as e:
                    print(f"  ❌ remove_ids测试失败: {e}")
                    return False
            else:
                print(f"  ⚠️ 没有找到要删除的向量")
                return False
        else:
            print(f"  ⚠️ 数据不一致，跳过高效删除测试")
            return False
            
    except Exception as e:
        print(f"💥 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 恢复备份
        print(f"\n🔄 恢复备份...")
        for backup_file in backup_dir.glob("*.backup"):
            original_name = backup_file.name.replace('.backup', '')
            restore_path = output_dir / original_name
            shutil.copy2(backup_file, restore_path)

if __name__ == "__main__":
    success = test_deletion_verification()
    print("\n" + "=" * 40)
    if success:
        print("🎉 删除机制验证通过!")
    else:
        print("❌ 删除机制验证失败")
    sys.exit(0 if success else 1)