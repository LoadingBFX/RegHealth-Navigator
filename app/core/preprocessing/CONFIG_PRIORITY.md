# 配置优先级和参数说明

## 🎯 **配置优先级 (从高到低)**

```
1. 命令行参数          ← 最高优先级
   ↓
2. 环境变量/.env文件    ← API keys等敏感信息
   ↓  
3. app/config/development.yml  ← 项目配置文件
   ↓
4. 代码默认值          ← 最低优先级
```

## 📁 **配置来源详解**

### **1. 命令行参数 (最高优先级)**
```bash
python pipeline.py \
    --data-dir /custom/data \           # 覆盖配置文件中的路径
    --chunk-words 300 \                 # 覆盖默认的500
    --days-back 7 \                     # 覆盖默认的30天
    --model text-embedding-3-large      # 覆盖默认模型
```

### **2. 环境变量/.env文件**
```bash
# .env 文件内容
OPENAI_API_KEY=sk-xxxxx...             # API密钥自动加载
```

### **3. app/config/development.yml (主配置文件)**
```yaml
# 路径配置
docs_data:
  path: data/                          # 数据目录

build_faiss:
  output_folder: rag_data              # 输出目录

# 处理配置
chunking:
  chunk_words: 500                     # 默认chunk大小
  overlap_sentences: 1                 # 默认重叠句数

regulation_fetch:
  days_back: 30                        # 默认查找天数

embedding:
  default_model: text-embedding-3-small # 默认模型
  models:
    text-embedding-3-small:
      price_per_1k_tokens: 0.00002
      dimension: 1536
```

### **4. 代码默认值 (兜底)**
```python
# 如果配置文件缺失，使用这些默认值
DEFAULT_VALUES = {
    'chunk_words': 500,
    'overlap_sentences': 1,
    'days_back': 30,
    'model': 'text-embedding-3-small',
    'data_dir': 'data',
    'output_dir': 'rag_data'
}
```

## ⚙️ **所有可配置参数**

### **📂 路径配置**
| 参数 | 命令行 | 配置文件路径 | 默认值 | 说明 |
|------|--------|-------------|--------|------|
| 数据目录 | `--data-dir` | `docs_data.path` | `data/` | 存放XML文件的目录 |
| 输出目录 | `--output-dir` | `build_faiss.output_folder` | `rag_data/` | 存放处理结果的目录 |

### **🔑 认证配置**
| 参数 | 命令行 | 环境变量 | 默认值 | 说明 |
|------|--------|----------|--------|------|
| API密钥 | `--api-key` | `OPENAI_API_KEY` | 无 | OpenAI API密钥 |

### **🕒 时间配置**
| 参数 | 命令行 | 配置文件路径 | 默认值 | 说明 |
|------|--------|-------------|--------|------|
| 查找天数 | `--days-back` | `regulation_fetch.days_back` | `30` | 查找新法规的天数 |

### **🔧 处理配置**
| 参数 | 命令行 | 配置文件路径 | 默认值 | 说明 |
|------|--------|-------------|--------|------|
| Chunk大小 | `--chunk-words` | `chunking.chunk_words` | `500` | 每个chunk的词数 |
| 重叠句数 | `--overlap` | `chunking.overlap_sentences` | `1` | 相邻chunk的重叠句数 |
| 嵌入模型 | `--model` | `embedding.default_model` | `text-embedding-3-small` | 使用的嵌入模型 |

## 🎯 **使用示例**

### **场景1: 使用默认配置**
```bash
# 只需要指定必要的路径，其他使用配置文件
python pipeline.py --data-dir ../../data --output-dir ../../../rag_data --incremental
```
**实际使用的配置:**
- chunk_words: 500 (来自 development.yml)
- days_back: 30 (来自 development.yml)
- model: text-embedding-3-small (来自 development.yml)
- API key: 自动从 .env 加载

### **场景2: 部分覆盖配置**
```bash
# 只覆盖特定参数
python pipeline.py --data-dir ../../data --output-dir ../../../rag_data \
    --chunk-words 300 --days-back 7 --incremental
```
**实际使用的配置:**
- chunk_words: 300 (命令行覆盖)
- days_back: 7 (命令行覆盖)
- model: text-embedding-3-small (来自 development.yml)
- overlap: 1 (来自 development.yml)

### **场景3: 完全自定义配置**
```bash
# 覆盖所有关键参数
python pipeline.py \
    --data-dir /custom/data \
    --output-dir /custom/output \
    --chunk-words 300 \
    --overlap 2 \
    --days-back 7 \
    --model text-embedding-3-large \
    --incremental
```

### **场景4: 代码中使用配置**
```python
from core.preprocessing.pipeline import ProcessingPipeline
from core.preprocessing.config_loader import ConfigLoader

# 方式1: 使用默认配置
config = ConfigLoader()
pipeline = ProcessingPipeline(**config.get_processing_config())

# 方式2: 部分覆盖配置
config = ConfigLoader({
    'chunking': {'chunk_words': 300},
    'regulation_fetch': {'days_back': 7}
})
pipeline = ProcessingPipeline(**config.get_processing_config())

# 方式3: 直接传参 (最高优先级)
pipeline = ProcessingPipeline(
    data_dir="/custom/data",
    chunk_words=300,
    days_back=7
)
```

## 🔍 **配置验证**

### **检查当前配置**
```python
from core.preprocessing.config_loader import ConfigLoader

config = ConfigLoader()
validation = config.validate_config()

if validation['valid']:
    print("✅ 配置验证通过")
else:
    print("❌ 配置问题:")
    for issue in validation['issues']:
        print(f"  - {issue}")
```

### **查看配置来源**
```python
config = ConfigLoader()
validation = config.validate_config()

print("配置来源:")
print(f"  - 主配置加载: {validation['config_sources']['app_config_loaded']}")
print(f"  - 手动覆盖: {validation['config_sources']['override_provided']}")
```

## ✅ **配置一致性修复**

### **修复前的问题:**
- ❌ `auto_update_pipeline.py` 默认 365天
- ❌ `preprocessing/pipeline.py` 默认 30天
- ❌ `development.yml` 没有相关配置

### **修复后的统一配置:**
- ✅ 所有组件都从 `development.yml` 读取
- ✅ 统一默认值: 30天
- ✅ 命令行参数可以覆盖所有配置
- ✅ 配置优先级清晰明确

## 🎉 **总结**

现在所有配置都遵循统一的优先级系统:

1. **命令行参数** - 临时覆盖，适合测试
2. **环境变量** - 敏感信息，如API密钥
3. **配置文件** - 项目默认设置
4. **代码默认** - 兜底保证

这样既保持了灵活性，又确保了配置的一致性和可维护性！