# 🚀 Preprocessing System Quick Start Guide

## 入口函数

### 🎯 **主要入口点**

#### 1. **ProcessingPipeline** - 推荐使用
```python
from core.preprocessing.pipeline import ProcessingPipeline
from core.preprocessing.config_loader import ConfigLoader

# 自动配置 (推荐)
config = ConfigLoader()
pipeline = ProcessingPipeline(**config.get_processing_config())
```

#### 2. **AutoUpdatePipeline** - 带法规自动获取
```python
from core.preprocessing.pipeline import AutoUpdatePipeline

pipeline = AutoUpdatePipeline(
    data_dir="data",
    output_dir="rag_data",
    days_back=30
)
```

---

## 🔧 CRUD 操作

### ➕ **Create (创建/处理文件)**

```python
# 处理单个文件
result = pipeline.process_files(["MPFS/2025_MPFS_final.xml"])

# 处理多个文件
result = pipeline.process_files([
    "MPFS/2025_MPFS_final.xml",
    "HOSPICE/2024_HOSPICE_final.xml"
])

# 增量更新 (处理所有新文件)
result = pipeline.run_incremental_update()
```

### 📖 **Read (查询状态)**

```python
# 系统状态
status = pipeline.get_system_status()
print(f"健康状态: {'✅' if status['healthy'] else '❌'}")
print(f"总chunks: {status['statistics']['total_chunks']}")
print(f"待处理变更: {status['statistics']['pending_changes']}")

# 成本估算
estimate = pipeline.estimate_update_cost()
print(f"预计成本: ${estimate['total_estimated_cost']:.4f}")
```

### ✏️ **Update (更新文件)**

```python
# 增量更新 (推荐 - 自动检测变化)
result = pipeline.run_incremental_update()

# 手动更新特定文件
result = pipeline.process_files(["MPFS/updated_file.xml"])
```

### 🗑️ **Delete (删除文件)**

```python
# 删除文件及其数据
result = pipeline.remove_files([
    "MPFS/old_document.xml",
    "HOSPICE/deprecated_rule.xml"
])

print(f"删除chunks: {result['total_chunks_removed']}")
print(f"重建成本: ${result['total_rebuild_cost']:.4f}")
```

---

## 💻 命令行使用

```bash
cd app/core/preprocessing

# 增量更新
python pipeline.py --data-dir ../../data --output-dir ../../../rag_data --incremental

# 处理特定文件
python pipeline.py --data-dir ../../data --output-dir ../../../rag_data \
    --process-files MPFS/2025_final.xml

# 系统状态
python pipeline.py --data-dir ../../data --output-dir ../../../rag_data --status

# 成本估算
python pipeline.py --data-dir ../../data --output-dir ../../../rag_data --estimate
```

---

## 🎯 **典型工作流**

### **场景1: 日常维护**
```python
from core.preprocessing.pipeline import ProcessingPipeline
from core.preprocessing.config_loader import ConfigLoader

# 1. 初始化
config = ConfigLoader()
pipeline = ProcessingPipeline(**config.get_processing_config())

# 2. 检查状态
status = pipeline.get_system_status()
print(f"待处理变更: {status['statistics']['pending_changes']}")

# 3. 估算成本
estimate = pipeline.estimate_update_cost()
print(f"预计成本: ${estimate['total_estimated_cost']:.4f}")

# 4. 执行更新 (如果成本合理)
if estimate['total_estimated_cost'] < 1.0:
    result = pipeline.run_incremental_update()
    print(f"✅ 处理完成: {result['files_processed']} 文件")
```

### **场景2: 处理紧急文件**
```python
# 快速处理单个重要文件
result = pipeline.process_files(["MPFS/urgent_update.xml"])

if result['status'] == 'success':
    print(f"✅ 紧急文件处理完成, 成本: ${result['total_cost']:.4f}")
```

### **场景3: 清理维护**
```python
# 删除过期文件
old_files = ["MPFS/2020_old.xml", "HOSPICE/deprecated.xml"]
result = pipeline.remove_files(old_files)

print(f"清理完成: 删除 {result['files_removed']} 文件")
```

---

## ⚙️ **配置选项**

### **基础配置**
```python
# 使用默认配置
config = ConfigLoader()

# 自定义配置
config = ConfigLoader({
    'embedding': {
        'model': 'text-embedding-3-large',  # 更高质量
        'batch_size': 100
    },
    'chunking': {
        'chunk_words': 300  # 更小的chunk
    }
})
```

### **环境配置**
- ✅ API Key 自动从 `.env` 文件加载
- ✅ 模型配置从 `app/config/development.yml` 加载
- ✅ 路径配置与主应用统一

---

## 🛡️ **错误处理**

```python
try:
    result = pipeline.run_incremental_update()
    
    if result['status'] != 'success':
        print(f"更新失败: {result.get('error')}")
        # 检查详细错误
        for error in result.get('errors', []):
            print(f"  - {error}")
    else:
        print(f"✅ 更新成功!")
        
except Exception as e:
    print(f"系统错误: {e}")
```

---

## 📊 **监控建议**

### **定期检查**
```python
# 系统健康检查
status = pipeline.get_system_status()
if not status['healthy']:
    print("⚠️ 系统需要维护")

# 数据一致性检查
if status['statistics']['pending_changes'] > 50:
    print("⚠️ 待处理文件过多，建议运行增量更新")
```

### **成本控制**
```python
# 设置成本上限
MAX_DAILY_COST = 5.0

estimate = pipeline.estimate_update_cost()
if estimate['total_estimated_cost'] > MAX_DAILY_COST:
    print("成本过高，考虑分批处理")
else:
    pipeline.run_incremental_update()
```

---

## 🚀 **现在开始使用！**

**最简单的开始方式：**

```python
from core.preprocessing.pipeline import ProcessingPipeline
from core.preprocessing.config_loader import ConfigLoader

# 一行初始化
pipeline = ProcessingPipeline(**ConfigLoader().get_processing_config())

# 一行更新
result = pipeline.run_incremental_update()

# 查看结果
print(f"处理完成: {result['files_processed']} 文件, ${result['total_cost']:.4f}")
```

🎉 **就这么简单！您的 preprocessing 系统已经准备就绪！**