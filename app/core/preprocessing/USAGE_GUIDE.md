# Preprocessing System Usage Guide

## 🚀 入口函数和完整使用指南

### 📋 **主要入口点**

#### 1. **ProcessingPipeline** - 基础处理管道
```python
from core.preprocessing.pipeline import ProcessingPipeline
from core.preprocessing.config_loader import ConfigLoader

# 自动加载配置
config = ConfigLoader()
processing_config = config.get_processing_config()

# 初始化管道
pipeline = ProcessingPipeline(**processing_config)
```

#### 2. **AutoUpdatePipeline** - 自动更新管道 (带法规获取)
```python
from core.preprocessing.pipeline import AutoUpdatePipeline

# 自动配置初始化
pipeline = AutoUpdatePipeline(
    data_dir="data",
    output_dir="rag_data",
    days_back=30  # 查找过去30天的新法规
)
```

#### 3. **IncrementalManager** - 底层 CRUD 管理器
```python
from core.preprocessing.incremental_manager import IncrementalManager

# 直接使用底层管理器
manager = IncrementalManager(
    data_directory="data",
    output_directory="rag_data"
)
```

---

## 🔧 **CRUD 功能详细使用**

### ➕ **Create (增加)**

#### **1. 处理新文件**
```python
# 方式一：通过 Pipeline
pipeline = ProcessingPipeline(**config.get_processing_config())

# 处理单个文件
result = pipeline.process_files(["MPFS/2025_MPFS_final.xml"])
print(f"处理结果: {result['files_processed']} 文件, 成本: ${result['total_cost']:.4f}")

# 处理多个文件
result = pipeline.process_files([
    "MPFS/2025_MPFS_final.xml",
    "HOSPICE/2024_HOSPICE_final.xml",
    "SNF/2025_SNF_proposed.xml"
])
```

#### **2. 增量更新 (处理所有新文件)**
```python
# 自动检测并处理所有新文件和修改的文件
result = pipeline.run_incremental_update()

if result['status'] == 'success':
    print(f"✅ 增量更新完成!")
    print(f"   - 处理文件: {result['files_processed']}")
    print(f"   - 删除文件: {result['files_removed']}")
    print(f"   - 总成本: ${result['total_cost']:.4f}")
    print(f"   - 处理成本: ${result['processing_cost']:.4f}")
    print(f"   - 清理成本: ${result['cleanup_cost']:.4f}")
```

#### **3. 底层文件处理**
```python
# 使用 IncrementalManager 直接处理
manager = IncrementalManager(data_directory="data", output_directory="rag_data")

# 处理单个文件
result = manager.process_file("MPFS/2025_MPFS_final.xml")
print(f"新增 chunks: {result['chunks_added']}, 成本: ${result['cost']:.4f}")
```

---

### 📖 **Read (查询)**

#### **1. 系统状态查询**
```python
# 获取完整系统状态
status = pipeline.get_system_status()

print(f"系统健康: {'✅' if status['healthy'] else '❌'}")
print(f"模型: {status['model']}")
print(f"数据目录: {status['data_directory']}")
print(f"输出目录: {status['output_directory']}")

# 统计信息
stats = status['statistics']
print(f"总 chunks: {stats['total_chunks']}")
print(f"索引大小: {stats['index_size']}")
print(f"总成本: ${stats['total_cost']:.4f}")
print(f"跟踪文件: {stats['files_tracked']}")
print(f"待处理变更: {stats['pending_changes']}")
print(f"待删除文件: {stats['pending_deletions']}")
```

#### **2. 成本估算**
```python
# 估算增量更新成本
estimate = pipeline.estimate_update_cost()

print(f"估算结果:")
print(f"  - 需要处理的文件: {estimate['estimated_files']}")
print(f"  - 预计 chunks: {estimate['estimated_chunks']}")
print(f"  - 预计成本: ${estimate['total_estimated_cost']:.4f}")
```

#### **3. 系统验证**
```python
# 验证系统健康状态
validation = pipeline.get_system_status()['validation']

if validation['valid']:
    print("✅ 系统验证通过")
else:
    print("❌ 系统验证失败")
    for issue in validation['issues']:
        print(f"   问题: {issue}")
    for warning in validation['warnings']:
        print(f"   警告: {warning}")
```

#### **4. 查询特定文件状态**
```python
# 使用 manager 查询详细信息
manager = IncrementalManager(data_directory="data", output_directory="rag_data")

# 获取完整状态
status = manager.get_status()
print(f"数据一致性: {status['data_consistency']}")
print(f"文件存在性: {status['files_exist']}")
```

---

### ✏️ **Update (修改)**

#### **1. 文件修改更新**
```python
# 当文件内容被修改后，自动检测并更新
# 文件跟踪器会检测到文件时间戳变化

# 方式一：增量更新 (推荐)
result = pipeline.run_incremental_update()
# 自动处理所有变化的文件

# 方式二：手动更新特定文件
result = pipeline.process_files(["MPFS/2025_MPFS_final.xml"])
# 会覆盖该文件的旧数据
```

#### **2. 底层文件更新**
```python
# 使用 manager 的更新方法
result = manager.update_file("MPFS/2025_MPFS_final.xml")

print(f"更新结果:")
print(f"  - 删除的 chunks: {result['chunks_removed']}")
print(f"  - 新增的 chunks: {result['chunks_added']}")
print(f"  - 净变化: {result['net_change']}")
print(f"  - 成本: ${result['cost']:.4f}")
```

#### **3. 配置更新**
```python
# 动态更新配置
config = ConfigLoader({
    'embedding': {
        'model': 'text-embedding-3-large',  # 切换到更高质量模型
        'batch_size': 100
    },
    'chunking': {
        'chunk_words': 300  # 使用更小的 chunk
    }
})

# 使用新配置创建管道
pipeline = ProcessingPipeline(**config.get_processing_config())
```

---

### 🗑️ **Delete (删除)**

#### **1. 删除特定文件**
```python
# 删除文件及其所有相关数据
result = pipeline.remove_files([
    "MPFS/old_document.xml",
    "HOSPICE/deprecated_rule.xml"
])

print(f"删除结果:")
print(f"  - 删除文件: {result['files_removed']}")
print(f"  - 删除 chunks: {result['total_chunks_removed']}")
print(f"  - 删除 embeddings: {result['total_embeddings_removed']}")
print(f"  - 重建成本: ${result['total_rebuild_cost']:.4f}")
```

#### **2. 底层文件删除**
```python
# 使用 manager 删除单个文件
result = manager.remove_file("MPFS/old_document.xml")

print(f"删除的 chunks: {result['chunks_removed']}")
print(f"剩余 chunks: {result['remaining_chunks']}")
print(f"重建成本: ${result['rebuild_cost']:.4f}")
```

#### **3. 清理删除的文件**
```python
# 增量更新会自动清理已删除的文件
result = pipeline.run_incremental_update()

# 检查清理结果
cleanup_results = result['cleanup_results']
for cleanup in cleanup_results:
    if cleanup['status'] == 'success':
        print(f"✅ 清理: {cleanup['file_path']}")
```

---

## 🎯 **完整工作流示例**

### **场景1: 日常增量更新**
```python
from core.preprocessing.pipeline import ProcessingPipeline
from core.preprocessing.config_loader import ConfigLoader

# 1. 初始化
config = ConfigLoader()
pipeline = ProcessingPipeline(**config.get_processing_config())

# 2. 检查系统状态
status = pipeline.get_system_status()
print(f"系统健康: {'✅' if status['healthy'] else '❌'}")
print(f"待处理变更: {status['statistics']['pending_changes']}")

# 3. 估算成本
estimate = pipeline.estimate_update_cost()
print(f"预计成本: ${estimate['total_estimated_cost']:.4f}")

# 4. 执行增量更新
if estimate['total_estimated_cost'] < 1.0:  # 成本控制
    result = pipeline.run_incremental_update()
    print(f"✅ 更新完成: {result['files_processed']} 文件, ${result['total_cost']:.4f}")
else:
    print("⚠️ 成本过高，跳过更新")
```

### **场景2: 处理特定文件**
```python
# 1. 处理单个重要文件
result = pipeline.process_files(["MPFS/2025_MPFS_final_urgent.xml"])

if result['status'] == 'success':
    print(f"✅ 紧急文件处理完成")
else:
    print(f"❌ 处理失败: {result['errors']}")

# 2. 验证处理结果
status = pipeline.get_system_status()
print(f"新的总 chunks: {status['statistics']['total_chunks']}")
```

### **场景3: 清理和维护**
```python
# 1. 删除过期文件
old_files = [
    "MPFS/2020_MPFS_proposed.xml",
    "HOSPICE/2019_rules.xml"
]

result = pipeline.remove_files(old_files)
print(f"清理完成: 删除 {result['files_removed']} 文件")

# 2. 系统验证
validation = pipeline.get_system_status()['validation']
if not validation['valid']:
    print("⚠️ 发现问题，执行完整重建...")
    # 可以选择重建整个索引
```

---

## 🔧 **命令行接口**

### **Pipeline CLI**
```bash
# 在 preprocessing 目录下运行
cd app/core/preprocessing

# 增量更新
python pipeline.py --data-dir ../../data --output-dir ../../../rag_data --incremental

# 处理特定文件
python pipeline.py --data-dir ../../data --output-dir ../../../rag_data --process-files MPFS/2025_final.xml

# 删除文件
python pipeline.py --data-dir ../../data --output-dir ../../../rag_data --remove-files old_file.xml

# 系统状态
python pipeline.py --data-dir ../../data --output-dir ../../../rag_data --status

# 成本估算
python pipeline.py --data-dir ../../data --output-dir ../../../rag_data --estimate
```

---

## 💡 **最佳实践**

### **1. 成本控制**
```python
# 始终先估算成本
estimate = pipeline.estimate_update_cost()
if estimate['total_estimated_cost'] > MAX_COST:
    print("成本过高，考虑分批处理")
```

### **2. 错误处理**
```python
try:
    result = pipeline.run_incremental_update()
    if result['status'] != 'success':
        print(f"更新失败: {result.get('error')}")
        # 检查错误详情
        for error in result.get('errors', []):
            print(f"  - {error}")
except Exception as e:
    print(f"系统错误: {e}")
```

### **3. 监控和日志**
```python
import logging
logging.basicConfig(level=logging.INFO)

# 所有操作都有详细日志
result = pipeline.run_incremental_update()
# 查看日志了解详细处理过程
```

### **4. 配置管理**
```python
# 使用不同环境的配置
config = ConfigLoader()

# 开发环境：使用较小的 chunk 和便宜的模型
dev_config = ConfigLoader({
    'embedding': {'model': 'text-embedding-3-small'},
    'chunking': {'chunk_words': 300}
})

# 生产环境：使用最佳质量配置
prod_config = ConfigLoader({
    'embedding': {'model': 'text-embedding-3-large'},
    'chunking': {'chunk_words': 500}
})
```

---

## 🎯 **总结**

新的 preprocessing 系统提供了：

- **🚀 简单的入口点**: `ProcessingPipeline` 和 `AutoUpdatePipeline`
- **🔧 完整的 CRUD**: 创建、查询、更新、删除功能
- **💰 成本控制**: 详细的成本估算和监控
- **🛡️ 错误处理**: 原子操作和回滚机制
- **📊 状态监控**: 详细的系统状态和验证
- **⚙️ 灵活配置**: 支持多种配置方式和环境

使用时只需要选择合适的入口点，然后调用相应的方法即可！