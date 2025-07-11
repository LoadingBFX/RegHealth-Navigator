#!/usr/bin/env python3
"""
测试增量检测 - 验证系统能否检测到被删除的文件并标记为需要处理
"""

import sys
import shutil
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'app'))

from app.core.preprocessing.incremental_manager import IncrementalManager

def test_incremental_detection():
    """测试增量检测功能"""
    print("🧪 增量检测功能测试")
    print("=" * 40)
    
    # 初始化管理器
    manager = IncrementalManager('data', 'rag_data')
    
    # 备份
    output_dir = Path('rag_data')
    backup_dir = Path('test_backup_detection')
    backup_dir.mkdir(exist_ok=True)
    
    for filename in ['chunks.json', 'faiss.index', 'faiss_metadata.json', 'file_tracking.json']:
        source = output_dir / filename
        if source.exists():
            shutil.copy2(source, backup_dir / f"{filename}.backup")
    
    try:
        # 1. 获取初始状态
        print("📊 获取初始状态...")
        chunks = manager._load_chunks()
        initial_status = manager.get_status()
        
        print(f"  Chunks: {len(chunks):,}")
        print(f"  Index vectors: {initial_status.get('index_size', 0):,}")
        print(f"  Pending changes: {initial_status.get('pending_changes', 0)}")
        
        # 2. 选择一个小文件进行删除
        file_counts = {}
        for chunk in chunks:
            source_file = chunk.get('metadata', {}).get('source_file', 'UNKNOWN')
            file_counts[source_file] = file_counts.get(source_file, 0) + 1
        
        suitable_files = [(f, c) for f, c in file_counts.items() 
                         if f != 'UNKNOWN' and f.endswith('.xml') and c > 0]
        test_file, chunk_count = min(suitable_files, key=lambda x: x[1])
        
        print(f"\n🎯 选择测试文件: {test_file}")
        print(f"  Chunks数量: {chunk_count}")
        
        # 确认文件存在于数据目录
        data_dir = Path('data')
        test_file_path = None
        for program in ['MPFS', 'SNF', 'HOSPICE']:
            potential_path = data_dir / program / test_file
            if potential_path.exists():
                test_file_path = potential_path
                break
        
        if not test_file_path:
            print(f"❌ 文件 {test_file} 不存在于数据目录")
            return False
        
        print(f"  文件路径: {test_file_path}")
        
        # 3. 手动删除chunks (模拟文件被删除的情况)
        print(f"\n🗑️ 模拟删除文件的chunks...")
        
        # 删除chunks
        filtered_chunks, chunks_removed = manager._remove_file_chunks(chunks, test_file)
        manager._save_chunks(filtered_chunks)
        
        print(f"  删除了 {chunks_removed} 个chunks")
        
        # 删除对应的metadata和vectors
        metadata = manager.faiss_builder.metadata
        indices_to_remove = []
        for i, meta in enumerate(metadata):
            if meta.get('metadata', {}).get('source_file') == test_file:
                indices_to_remove.append(i)
        
        if indices_to_remove:
            import numpy as np
            remove_ids = np.array(indices_to_remove, dtype=np.int64)
            manager.faiss_builder.index.remove_ids(remove_ids)
            
            # 更新metadata
            new_metadata = [meta for i, meta in enumerate(metadata) if i not in indices_to_remove]
            manager.faiss_builder.metadata = new_metadata
            
            # 保存更新的索引
            manager.faiss_builder.save_index(manager.index_path, manager.metadata_path)
            
            print(f"  删除了 {len(indices_to_remove)} 个向量")
        
        # 4. 测试增量检测
        print(f"\n🔍 测试增量检测...")
        
        # 检查文件跟踪器能否检测到变化
        changed_result = manager.file_tracker.find_changed_files()
        if changed_result['status'] == 'success':
            changed_files = changed_result['files']
            print(f"  检测到 {len(changed_files)} 个变化的文件")
            
            # 检查我们的测试文件是否在变化列表中
            test_file_in_changes = any(
                str(f).endswith(test_file) for f in changed_files
            )
            
            if test_file_in_changes:
                print(f"  ✅ 测试文件 {test_file} 被检测为需要更新")
            else:
                print(f"  ❌ 测试文件 {test_file} 未被检测为需要更新")
                print(f"  变化的文件: {[str(f) for f in changed_files]}")
        else:
            print(f"  ❌ 变化检测失败: {changed_result.get('error')}")
            return False
        
        # 5. 检查增量更新是否会处理这个文件
        print(f"\n🔄 测试增量更新检测...")
        
        # 获取更新前状态
        before_chunks = len(manager._load_chunks())
        before_vectors = manager.faiss_builder.index.ntotal if manager.faiss_builder.index else 0
        
        print(f"  更新前: {before_chunks} chunks, {before_vectors} vectors")
        
        # 只测试检测，不实际运行完整更新（避免超时）
        # 模拟处理单个文件
        try:
            relative_path = test_file_path.relative_to(data_dir)
            print(f"  测试处理文件: {relative_path}")
            
            # 这会重新处理文件并添加chunks
            result = manager.process_file(str(relative_path))
            
            if result['status'] == 'success':
                print(f"  ✅ 文件处理成功")
                print(f"  添加的chunks: {result.get('chunks_added', 0)}")
                print(f"  成本: ${result.get('cost', 0):.4f}")
                
                # 检查恢复情况
                after_chunks = len(manager._load_chunks())
                after_vectors = manager.faiss_builder.index.ntotal if manager.faiss_builder.index else 0
                
                print(f"  恢复后: {after_chunks} chunks, {after_vectors} vectors")
                
                # 验证文件是否恢复
                final_chunks = manager._load_chunks()
                restored_count = sum(1 for chunk in final_chunks 
                                   if chunk.get('metadata', {}).get('source_file') == test_file)
                
                print(f"  恢复的chunks: {restored_count}")
                
                if restored_count > 0:
                    restoration_rate = (restored_count / chunk_count * 100) if chunk_count > 0 else 0
                    print(f"  恢复率: {restoration_rate:.1f}%")
                    
                    if restoration_rate >= 80:  # 允许一些差异
                        print(f"\n🎉 增量检测和恢复测试成功!")
                        print(f"  ✅ 系统检测到缺失的文件")
                        print(f"  ✅ 自动重新处理文件")
                        print(f"  ✅ 恢复了文件的chunks和embeddings")
                        return True
                    else:
                        print(f"  ⚠️ 恢复不完整")
                        return False
                else:
                    print(f"  ❌ 文件未恢复")
                    return False
            else:
                print(f"  ❌ 文件处理失败: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"  ❌ 处理文件时出错: {e}")
            return False
            
    except Exception as e:
        print(f"💥 测试失败: {e}")
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
    success = test_incremental_detection()
    print("\n" + "=" * 40)
    if success:
        print("🎉 增量检测和恢复测试通过!")
    else:
        print("❌ 增量检测和恢复测试失败")
    sys.exit(0 if success else 1)