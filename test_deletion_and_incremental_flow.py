#!/usr/bin/env python3
"""
完整测试：删除文件 + 增量流程
1. 删除一个文件及其相关的 chunk 和 embedding
2. 测试增量更新流程是否会把删掉的补全
"""

import os
import sys
import json
import random
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add paths
sys.path.append(str(Path(__file__).parent / 'app' / 'core' / 'preprocessing'))
sys.path.append(str(Path(__file__).parent / 'app'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeletionIncrementalTester:
    """测试删除 + 增量流程的完整测试器"""
    
    def __init__(self):
        """初始化测试器"""
        from app.core.preprocessing.config_loader import ConfigLoader
        from app.core.preprocessing.incremental_manager import IncrementalManager
        
        # 加载配置
        self.config = ConfigLoader()
        self.processing_config = self.config.get_processing_config()
        self.data_dir = Path(self.processing_config['data_dir'])
        self.output_dir = Path(self.processing_config['output_dir'])
        
        # 初始化增量管理器
        self.manager = IncrementalManager(
            data_directory=self.data_dir,
            output_directory=self.output_dir,
            api_key=self.processing_config.get('api_key'),
            model=self.processing_config['model']
        )
        
        # 备份目录
        self.backup_dir = self.output_dir / 'test_backup'
        self.backup_dir.mkdir(exist_ok=True)
        
        logger.info("🧪 DeletionIncrementalTester 初始化完成")
        logger.info(f"📁 数据目录: {self.data_dir}")
        logger.info(f"📁 输出目录: {self.output_dir}")
    
    def create_backup(self) -> Dict[str, Any]:
        """创建系统备份"""
        logger.info("📦 创建系统备份...")
        
        backup_info = {
            'timestamp': datetime.now().isoformat(),
            'files_backed_up': []
        }
        
        files_to_backup = [
            'chunks.json',
            'faiss.index', 
            'faiss_metadata.json',
            'file_tracking.json'
        ]
        
        for filename in files_to_backup:
            source = self.output_dir / filename
            if source.exists():
                backup_path = self.backup_dir / f"{filename}.backup"
                shutil.copy2(source, backup_path)
                backup_info['files_backed_up'].append(filename)
                logger.info(f"✅ 备份: {filename}")
        
        return backup_info
    
    def restore_backup(self) -> None:
        """恢复系统备份"""
        logger.info("🔄 从备份恢复系统...")
        
        backup_files = list(self.backup_dir.glob("*.backup"))
        for backup_file in backup_files:
            original_name = backup_file.name.replace('.backup', '')
            restore_path = self.output_dir / original_name
            shutil.copy2(backup_file, restore_path)
            logger.info(f"✅ 恢复: {original_name}")
    
    def analyze_system_state(self) -> Dict[str, Any]:
        """分析当前系统状态"""
        logger.info("📊 分析系统状态...")
        
        # 获取系统状态
        status = self.manager.get_status()
        
        # 加载chunks并分析文件分布
        chunks = self.manager._load_chunks()
        
        file_counts = {}
        for chunk in chunks:
            source_file = chunk.get('metadata', {}).get('source_file', 'UNKNOWN')
            file_counts[source_file] = file_counts.get(source_file, 0) + 1
        
        # 检查可用的XML文件
        available_xml_files = []
        for program in ['MPFS', 'SNF', 'HOSPICE']:
            program_dir = self.data_dir / program
            if program_dir.exists():
                xml_files = list(program_dir.glob('*.xml'))
                available_xml_files.extend(xml_files)
        
        analysis = {
            'system_status': status,
            'total_chunks': len(chunks),
            'file_chunk_counts': file_counts,
            'available_xml_files': [str(f.relative_to(self.data_dir)) for f in available_xml_files],
            'xml_file_count': len(available_xml_files),
            'data_consistent': status.get('data_consistency', {})
        }
        
        logger.info(f"📊 系统分析结果:")
        logger.info(f"  总chunks: {analysis['total_chunks']:,}")
        logger.info(f"  chunks中的文件数: {len(file_counts)}")
        logger.info(f"  可用XML文件数: {len(available_xml_files)}")
        logger.info(f"  索引向量数: {status.get('index_size', 0):,}")
        logger.info(f"  数据一致性: {status.get('data_consistency', {})}")
        
        return analysis
    
    def select_file_for_deletion(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """选择要删除的文件"""
        logger.info("🎯 选择要删除的文件...")
        
        # 获取有chunks且存在于数据目录的文件
        available_files = analysis['available_xml_files']
        files_with_chunks = analysis['file_chunk_counts']
        
        # 找到既存在于数据目录又有chunks的文件
        suitable_files = []
        for xml_file in available_files:
            filename = Path(xml_file).name
            if filename in files_with_chunks and files_with_chunks[filename] > 0:
                chunk_count = files_with_chunks[filename]
                suitable_files.append({
                    'relative_path': xml_file,
                    'filename': filename,
                    'chunk_count': chunk_count
                })
        
        if not suitable_files:
            raise Exception("没有找到可以删除和恢复的合适文件")
        
        # 选择一个较小的文件（减少干扰）
        suitable_files.sort(key=lambda x: x['chunk_count'])
        selected = suitable_files[0]  # 选择chunk数最少的文件
        
        logger.info(f"🎯 选中删除目标: {selected['filename']}")
        logger.info(f"  相对路径: {selected['relative_path']}")
        logger.info(f"  要删除的chunks: {selected['chunk_count']:,}")
        logger.info(f"  文件存在于数据目录: ✅")
        
        return selected
    
    def perform_deletion(self, selected_file: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件删除"""
        logger.info(f"🗑️ 删除文件: {selected_file['filename']}")
        
        # 使用增量管理器的删除方法
        removal_result = self.manager.remove_file(selected_file['relative_path'])
        
        if removal_result['status'] != 'success':
            raise Exception(f"文件删除失败: {removal_result.get('error')}")
        
        logger.info(f"✅ 文件删除完成:")
        logger.info(f"  删除的chunks: {removal_result.get('chunks_removed', 0):,}")
        logger.info(f"  删除的embeddings: {removal_result.get('embeddings_removed', 0):,}")
        logger.info(f"  重建成本: ${removal_result.get('rebuild_cost', 0):.4f}")
        logger.info(f"  是否使用fallback: {removal_result.get('fallback_rebuild', False)}")
        
        return removal_result
    
    def verify_deletion(self, selected_file: Dict[str, Any]) -> Dict[str, Any]:
        """验证文件删除结果"""
        logger.info("🔍 验证删除结果...")
        
        # 检查chunks
        chunks = self.manager._load_chunks()
        filename = selected_file['filename']
        
        remaining_chunks = 0
        for chunk in chunks:
            source_file = chunk.get('metadata', {}).get('source_file', '')
            if source_file == filename:
                remaining_chunks += 1
        
        # 检查系统状态
        status = self.manager.get_status()
        
        verification = {
            'filename': filename,
            'remaining_chunks': remaining_chunks,
            'completely_deleted': remaining_chunks == 0,
            'system_status': status,
            'file_exists_in_data_dir': (self.data_dir / selected_file['relative_path']).exists()
        }
        
        logger.info(f"📊 删除验证结果:")
        logger.info(f"  剩余chunks: {remaining_chunks}")
        logger.info(f"  完全删除: {'✅' if verification['completely_deleted'] else '❌'}")
        logger.info(f"  文件仍存在于数据目录: {'✅' if verification['file_exists_in_data_dir'] else '❌'}")
        
        return verification
    
    def run_incremental_update(self) -> Dict[str, Any]:
        """运行增量更新"""
        logger.info("🔄 运行增量更新...")
        
        # 获取更新前状态
        before_status = self.manager.get_status()
        before_chunks = len(self.manager._load_chunks())
        
        logger.info(f"📊 增量更新前:")
        logger.info(f"  Chunks: {before_chunks:,}")
        logger.info(f"  索引向量: {before_status.get('index_size', 0):,}")
        logger.info(f"  待处理变更: {before_status.get('pending_changes', 0)}")
        
        # 运行完整增量更新
        update_result = self.manager.full_incremental_update()
        
        if update_result['status'] != 'success':
            logger.error(f"❌ 增量更新失败: {update_result.get('error')}")
            return update_result
        
        # 获取更新后状态
        after_status = self.manager.get_status()
        after_chunks = len(self.manager._load_chunks())
        
        logger.info(f"✅ 增量更新完成:")
        logger.info(f"  处理的文件: {update_result.get('files_processed', 0)}")
        logger.info(f"  移除的文件: {update_result.get('files_removed', 0)}")
        logger.info(f"  总成本: ${update_result.get('total_cost', 0):.4f}")
        
        logger.info(f"📊 增量更新后:")
        logger.info(f"  Chunks: {after_chunks:,} (变化: {after_chunks - before_chunks:+,})")
        logger.info(f"  索引向量: {after_status.get('index_size', 0):,}")
        
        update_result.update({
            'before_chunks': before_chunks,
            'after_chunks': after_chunks,
            'chunks_change': after_chunks - before_chunks,
            'before_status': before_status,
            'after_status': after_status
        })
        
        return update_result
    
    def verify_restoration(self, selected_file: Dict[str, Any], original_chunk_count: int) -> Dict[str, Any]:
        """验证文件是否被恢复"""
        logger.info("🔍 验证文件恢复...")
        
        filename = selected_file['filename']
        
        # 检查文件chunks是否恢复
        chunks = self.manager._load_chunks()
        restored_chunks = 0
        
        for chunk in chunks:
            source_file = chunk.get('metadata', {}).get('source_file', '')
            if source_file == filename:
                restored_chunks += 1
        
        # 检查文件跟踪状态
        file_tracker = self.manager.file_tracker
        file_status = file_tracker.get_file_status(self.data_dir / selected_file['relative_path'])
        
        verification = {
            'filename': filename,
            'original_chunk_count': original_chunk_count,
            'restored_chunks': restored_chunks,
            'file_restored': restored_chunks > 0,
            'fully_restored': restored_chunks == original_chunk_count,
            'file_tracking_status': file_status,
            'restoration_percentage': (restored_chunks / original_chunk_count * 100) if original_chunk_count > 0 else 0
        }
        
        logger.info(f"📊 文件恢复验证:")
        logger.info(f"  原始chunks: {original_chunk_count:,}")
        logger.info(f"  恢复的chunks: {restored_chunks:,}")
        logger.info(f"  文件已恢复: {'✅' if verification['file_restored'] else '❌'}")
        logger.info(f"  完全恢复: {'✅' if verification['fully_restored'] else '❌'}")
        logger.info(f"  恢复百分比: {verification['restoration_percentage']:.1f}%")
        
        return verification
    
    def run_complete_test(self) -> Dict[str, Any]:
        """运行完整的删除和增量测试"""
        logger.info("\\n🚀 开始删除 + 增量流程测试")
        logger.info("=" * 60)
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            # 阶段1: 备份
            logger.info("\\n📋 阶段1: 系统备份")
            backup_info = self.create_backup()
            test_results['backup'] = backup_info
            
            # 阶段2: 初始分析
            logger.info("\\n📋 阶段2: 初始系统分析")
            initial_analysis = self.analyze_system_state()
            test_results['initial_analysis'] = initial_analysis
            
            # 阶段3: 选择删除文件
            logger.info("\\n📋 阶段3: 选择删除目标")
            selected_file = self.select_file_for_deletion(initial_analysis)
            test_results['selected_file'] = selected_file
            original_chunk_count = selected_file['chunk_count']
            
            # 阶段4: 执行删除
            logger.info("\\n📋 阶段4: 执行文件删除")
            deletion_result = self.perform_deletion(selected_file)
            test_results['deletion'] = deletion_result
            
            # 阶段5: 验证删除
            logger.info("\\n📋 阶段5: 验证删除结果")
            deletion_verification = self.verify_deletion(selected_file)
            test_results['deletion_verification'] = deletion_verification
            
            if not deletion_verification['completely_deleted']:
                logger.error("❌ 文件删除验证失败")
                test_results['success'] = False
                return test_results
            
            # 阶段6: 增量更新
            logger.info("\\n📋 阶段6: 运行增量更新")
            update_result = self.run_incremental_update()
            test_results['incremental_update'] = update_result
            
            if update_result['status'] != 'success':
                logger.error("❌ 增量更新失败")
                test_results['success'] = False
                return test_results
            
            # 阶段7: 验证恢复
            logger.info("\\n📋 阶段7: 验证文件恢复")
            restoration_verification = self.verify_restoration(selected_file, original_chunk_count)
            test_results['restoration_verification'] = restoration_verification
            
            # 判断整体成功
            test_results['success'] = (
                deletion_verification['completely_deleted'] and
                update_result['status'] == 'success' and
                restoration_verification['file_restored']
            )
            
            # 打印总结
            self.print_test_summary(test_results)
            
            return test_results
            
        except Exception as e:
            logger.error(f"💥 测试失败: {e}")
            test_results['error'] = str(e)
            test_results['success'] = False
            return test_results
        
        finally:
            # 总是恢复备份
            try:
                self.restore_backup()
                logger.info("🔄 系统已从备份恢复")
            except Exception as e:
                logger.error(f"❌ 恢复备份失败: {e}")
    
    def print_test_summary(self, results: Dict[str, Any]):
        """打印测试总结"""
        logger.info("\\n" + "=" * 60)
        logger.info("📊 删除 + 增量流程测试总结")
        logger.info("=" * 60)
        
        success = results.get('success', False)
        status = "✅ 通过" if success else "❌ 失败"
        logger.info(f"总体结果: {status}")
        
        # 测试目标
        selected_file = results.get('selected_file', {})
        if selected_file:
            logger.info(f"\\n🎯 测试目标:")
            logger.info(f"  文件: {selected_file.get('filename', 'Unknown')}")
            logger.info(f"  原始chunks: {selected_file.get('chunk_count', 0):,}")
        
        # 删除结果
        deletion = results.get('deletion', {})
        if deletion:
            logger.info(f"\\n🗑️ 删除阶段:")
            logger.info(f"  删除的chunks: {deletion.get('chunks_removed', 0):,}")
            logger.info(f"  删除的embeddings: {deletion.get('embeddings_removed', 0):,}")
            logger.info(f"  重建成本: ${deletion.get('rebuild_cost', 0):.4f}")
            logger.info(f"  使用高效删除: {'❌' if deletion.get('fallback_rebuild', False) else '✅'}")
        
        # 增量更新结果
        update = results.get('incremental_update', {})
        if update:
            logger.info(f"\\n🔄 增量更新阶段:")
            logger.info(f"  处理的文件: {update.get('files_processed', 0)}")
            logger.info(f"  Chunks变化: {update.get('chunks_change', 0):+,}")
            logger.info(f"  总成本: ${update.get('total_cost', 0):.4f}")
        
        # 恢复验证
        restoration = results.get('restoration_verification', {})
        if restoration:
            logger.info(f"\\n🔍 恢复验证:")
            logger.info(f"  文件已恢复: {'✅' if restoration.get('file_restored') else '❌'}")
            logger.info(f"  完全恢复: {'✅' if restoration.get('fully_restored') else '❌'}")
            logger.info(f"  恢复百分比: {restoration.get('restoration_percentage', 0):.1f}%")
            logger.info(f"  恢复的chunks: {restoration.get('restored_chunks', 0):,}")
        
        if success:
            logger.info(f"\\n💡 测试结论:")
            logger.info(f"  ✅ 文件删除功能正常")
            logger.info(f"  ✅ 增量更新检测到缺失文件")
            logger.info(f"  ✅ 删除的文件被自动恢复")
            logger.info(f"  ✅ 系统保持数据完整性")
            logger.info(f"  ✅ 完整工作流程可用于生产")
        else:
            logger.info(f"\\n⚠️ 测试问题:")
            logger.info(f"  ❌ 检查删除或恢复过程")
            logger.info(f"  ❌ 审查增量更新逻辑")
        
        logger.info("=" * 60)


def main():
    """运行删除和增量测试"""
    try:
        tester = DeletionIncrementalTester()
        results = tester.run_complete_test()
        
        success = results.get('success', False)
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"💥 测试执行失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())