#!/usr/bin/env python3
"""
测试增量流程 - 删除文件后运行增量更新看是否恢复
"""

import sys
import shutil
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'app'))

from app.core.preprocessing.incremental_manager import IncrementalManager

def test_incremental_flow():
    """测试删除 + 增量流程"""
    print("🧪 删除 + 增量流程测试")
    print("=" * 50)
    
    # 初始化管理器
    manager = IncrementalManager('data', 'rag_data')
    
    # 创建备份
    output_dir = Path('rag_data')
    backup_dir = Path('test_backup_simple')
    backup_dir.mkdir(exist_ok=True)
    
    print("📦 创建备份...")
    for filename in ['chunks.json', 'faiss.index', 'faiss_metadata.json', 'file_tracking.json']:
        source = output_dir / filename
        if source.exists():
            shutil.copy2(source, backup_dir / f"{filename}.backup")
            print(f"  ✅ 备份: {filename}")
    
    try:
        # 步骤1: 获取初始状态
        chunks = manager._load_chunks()
        initial_count = len(chunks)
        print(f"\n📊 初始状态: {initial_count:,} chunks")
        
        # 步骤2: 选择要删除的文件
        file_counts = {}
        for chunk in chunks:
            source_file = chunk.get('metadata', {}).get('source_file', 'UNKNOWN')
            file_counts[source_file] = file_counts.get(source_file, 0) + 1
        
        # 选择最小的文件
        suitable_files = [(f, c) for f, c in file_counts.items() 
                         if f != 'UNKNOWN' and f.endswith('.xml') and c > 0]
        test_file, chunk_count = min(suitable_files, key=lambda x: x[1])
        
        print(f"🎯 选择删除: {test_file} ({chunk_count} chunks)")
        
        # 步骤3: 手动删除（绕过装饰器问题）
        print("\n🗑️ 执行删除...")
        chunks = manager._load_chunks()
        filtered_chunks, chunks_removed = manager._remove_file_chunks(chunks, test_file)
        manager._save_chunks(filtered_chunks)
        
        # 重组索引
        reorganize_result = manager._rebuild_index_by_reorganization(chunks, filtered_chunks, chunks_removed)
        print(f"  删除结果: 移除 {chunks_removed} chunks, {reorganize_result.get('vectors_reorganized', 0)} vectors")
        
        # 保存索引
        manager.faiss_builder.save_index(manager.index_path, manager.metadata_path)
        
        # 验证删除
        after_delete_chunks = manager._load_chunks()
        print(f"  删除后: {len(after_delete_chunks):,} chunks")
        
        # 验证文件已被删除
        remaining = sum(1 for chunk in after_delete_chunks 
                       if chunk.get('metadata', {}).get('source_file') == test_file)
        print(f"  目标文件剩余chunks: {remaining}")
        
        if remaining == 0:
            print("  ✅ 文件已完全删除")
        else:
            print("  ❌ 文件未完全删除")
            return False
        
        # 步骤4: 运行增量更新
        print("\n🔄 运行增量更新...")
        update_result = manager.full_incremental_update()
        
        if update_result['status'] == 'success':
            print(f"  ✅ 增量更新成功")
            print(f"  处理文件: {update_result.get('files_processed', 0)}")
            print(f"  总成本: ${update_result.get('total_cost', 0):.4f}")
        else:
            print(f"  ❌ 增量更新失败: {update_result.get('error')}")
            return False
        
        # 步骤5: 检查文件是否恢复
        print("\n🔍 检查文件恢复...")
        final_chunks = manager._load_chunks()
        final_count = len(final_chunks)
        
        # 检查目标文件是否恢复
        restored_chunks = sum(1 for chunk in final_chunks 
                            if chunk.get('metadata', {}).get('source_file') == test_file)
        
        print(f"📊 最终状态:")
        print(f"  最终chunks: {final_count:,}")
        print(f"  chunks变化: {final_count - initial_count:+,}")
        print(f"  目标文件恢复chunks: {restored_chunks}")
        
        if restored_chunks > 0:
            print(f"  ✅ 文件已恢复 ({restored_chunks}/{chunk_count} chunks)")
            restoration_percent = (restored_chunks / chunk_count * 100) if chunk_count > 0 else 0
            print(f"  恢复率: {restoration_percent:.1f}%")
            
            if restoration_percent >= 90:  # 允许小幅差异
                print("🎉 测试成功: 删除和增量恢复流程正常工作!")
                return True
            else:
                print("⚠️ 恢复不完整")
                return False
        else:
            print("❌ 文件未恢复")
            return False
    
    except Exception as e:
        print(f"💥 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 恢复备份
        print("\n🔄 恢复备份...")
        for backup_file in backup_dir.glob("*.backup"):
            original_name = backup_file.name.replace('.backup', '')
            restore_path = output_dir / original_name
            shutil.copy2(backup_file, restore_path)
            print(f"  ✅ 恢复: {original_name}")

if __name__ == "__main__":
    success = test_incremental_flow()
    print("\n" + "=" * 50)
    if success:
        print("🎉 整体测试通过!")
    else:
        print("❌ 测试失败")
    sys.exit(0 if success else 1)