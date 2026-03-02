# Phase 7.4: 智能搜索增强 - 需求概述

## 文档信息

| 项目 | 说明 |
|------|------|
| PRD版本 | v1.0 |
| 创建日期 | 2025-01-20 |
| 模块名称 | 智能搜索增强 (SmartSearch) |
| 依赖模块 | Phase 1.4 Asset CRUD、Phase 7.3 Asset Tags、Elasticsearch |

---

## 1. 业务背景与痛点

### 1.1 现状分析

当前GZEAMS的搜索功能基于数据库LIKE查询，存在以下限制：

| 痛点 | 描述 | 影响 |
|------|------|------|
| **搜索速度慢** | 大数据量时LIKE查询性能差 | 用户体验差 |
| **不支持模糊匹配** | 必须完全匹配关键词 | 查找困难 |
| **无搜索联想** | 用户需输入完整关键词 | 输入成本高 |
| **无搜索历史** | 无法重复历史搜索 | 效率低下 |
| **无高级搜索** | 无法保存复杂搜索条件 | 重复操作多 |

### 1.2 解决方案

引入全文搜索引擎（Elasticsearch），实现：

1. **全文检索** - 对资产名称、编号、规格等进行全文索引
2. **模糊匹配** - 支持拼音、缩写、纠错
3. **搜索联想** - 输入时实时提示
4. **搜索历史** - 记录和推荐搜索历史
5. **高级搜索保存** - 保存常用搜索条件
6. **聚合统计** - 搜索结果按分类、状态等聚合

---

## 2. 技术架构

### 2.1 搜索架构

```
┌─────────────────────────────────────────────────────────────┐
│                         搜索层                            │
├─────────────────────────────────────────────────────────────┤
│  搜索API     搜索建议    高级搜索    搜索历史              │
│     │            │           │           │                 │
│     ▼            ▼           ▼           ▼                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              SearchService                         │   │
│  │  - 查询解析  - 结果聚合  - 高亮显示  - 排序        │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                │
│                          ▼                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Elasticsearch                          │   │
│  │  - 全文索引  - 聚合  - 高亮   - 建议           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ 同步
│  ┌─────────────────────────────────────────────────────┐   │
│  │              PostgreSQL (源数据)                    │   │
│  │  - Asset表   - 其他业务表                          │   │
│  └─────────────────────────────────────────────────────┘   │
```

### 2.2 技术选型

| 组件 | 选型 | 说明 |
|------|------|------|
| 搜索引擎 | Elasticsearch 8.x | 成熟的全文搜索方案 |
| 同步工具 | Logstash / Django信号 | 数据同步到ES |
| Python客户端 | elasticsearch-py | Python ES客户端 |
| 分词器 | ik_max_word | 中文分词支持 |

---

## 3. 功能范围

### 3.1 功能清单

| 功能 | 说明 | 优先级 |
|------|------|--------|
| 全文检索 | 对资产名称、编号、规格进行全文索引 | P0 |
| 搜索建议 | 输入时实时提示搜索关键词 | P0 |
| 搜索历史 | 记录用户搜索历史，快速重复搜索 | P1 |
| 高级搜索 | 保存常用搜索条件 | P1 |
| 结果高亮 | 搜索关键词高亮显示 | P1 |
| 聚合筛选 | 搜索结果按分类、状态等聚合 | P2 |
| 拼音搜索 | 支持拼音搜索资产 | P2 |

---

## 4. 数据模型

### 4.1 SearchHistory（搜索历史）

```python
class SearchHistory(BaseModel):
    """搜索历史"""
    user = models.ForeignKey('accounts.User')
    search_type = models.CharField(max_length=20)  # asset/project/...
    keyword = models.CharField(max_length=200)
    filters = models.JSONField(default=dict)  # 保存的筛选条件
    result_count = models.IntegerField(default=0)
    search_count = models.IntegerField(default=1)  # 搜索次数
```

### 4.2 SavedSearch（保存的搜索）

```python
class SavedSearch(BaseModel):
    """保存的搜索"""
    user = models.ForeignKey('accounts.User')
    name = models.CharField(max_length=100)
    search_type = models.CharField(max_length=20)
    keyword = models.CharField(max_length=200, blank=True)
    filters = models.JSONField(default=dict)
    is_public = models.BooleanField(default=False)  # 是否公开给其他人
```

---

## 5. API接口设计

### 5.1 搜索接口

| 接口 | 说明 |
|------|------|
| POST /api/search/assets/ | 全文搜索资产 |
| GET /api/search/suggestions/ | 获取搜索建议 |
| POST /api/search/save/ | 保存搜索条件 |
| GET /api/search/history/ | 获取搜索历史 |
| GET /api/search/saved/ | 获取保存的搜索 |

### 5.2 搜索请求示例

```json
POST /api/search/assets/
{
    "keyword": "笔记本",
    "filters": {
        "category": "电子设备",
        "status": "in_use"
    },
    "sort": "relevance",  // relevance/date/price
    "page": 1,
    "page_size": 20
}
```

### 5.3 搜索响应示例

```json
{
    "success": true,
    "data": {
        "total": 15,
        "results": [
            {
                "id": "uuid",
                "asset_code": "ZC001",
                "asset_name": "<em>笔记本</em>电脑",
                "highlight": {
                    "asset_name": "<em>笔记本</em>电脑"
                },
                "score": 2.5,
                "category": "电子设备",
                "status": "in_use"
            }
        ],
        "aggregations": {
            "category": {
                "电子设备": 10,
                "办公设备": 5
            },
            "status": {
                "在用": 8,
                "闲置": 7
            }
        }
    }
}
```

---

## 6. Elasticsearch索引结构

```json
PUT /assets
{
  "mappings": {
    "properties": {
      "asset_code": {
        "type": "text",
        "fields": {
          "keyword": {"type": "keyword"}
        }
      },
      "asset_name": {
        "type": "text",
        "analyzer": "ik_max_word",
        "fields": {
          "keyword": {"type": "keyword"},
          "pinyin": {"type": "text", "analyzer": "pinyin"}
        }
      },
      "specification": {
        "type": "text",
        "analyzer": "ik_max_word"
      },
      "category": {
        "type": "keyword"
      },
      "status": {
        "type": "keyword"
      },
      "purchase_price": {
        "type": "double"
      },
      "location": {
        "type": "keyword"
      },
      "tags": {
        "type": "keyword"
      },
      "organization_id": {
        "type": "keyword"
      }
    }
  },
  "settings": {
    "analysis": {
      "analyzer": {
        "pinyin": {
          "tokenizer": "pinyin",
          "filter": ["lowercase"]
        }
      }
    }
  }
}
```

---

## 7. 前端组件

### 7.1 SmartSearchBox

```vue
<template>
  <div class="smart-search-box">
    <el-autocomplete
      v-model="keyword"
      :fetch-suggestions="querySearch"
      :placeholder="placeholder"
      :trigger-on-focus="false"
      @select="handleSelect"
      @keyup.enter="handleSearch"
      clearable
    >
      <template #default="{ item }">
        <div class="search-item">
          <span class="icon" v-if="item.type === 'history'">
            <el-icon><Clock /></el-icon>
          </span>
          <span class="label">{{ item.label }}</span>
          <span class="count" v-if="item.count">({{ item.count }})</span>
        </div>
      </template>
      <template #suffix>
        <el-button @click="showAdvancedSearch = true">
          <el-icon><Setting /></el-icon>
        </el-button>
      </template>
    </el-autocomplete>

    <!-- 高级搜索对话框 -->
    <AdvancedSearchDialog
      v-model="showAdvancedSearch"
      @search="handleAdvancedSearch"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Clock, Setting } from '@element-plus/icons-vue'
import { searchAssets, getSearchSuggestions, getSearchHistory } from '@/api/search'

const router = useRouter()

const keyword = ref('')
const showAdvancedSearch = ref(false)
const searchHistory = ref([])

const querySearch = async (queryString, cb) => {
  if (!queryString) {
    // 显示搜索历史
    const history = await getSearchHistory({ limit: 10 })
    cb(history.data.map(item => ({
      label: item.keyword,
      value: item.keyword,
      type: 'history'
    })))
    return
  }

  // 获取搜索建议
  const response = await getSearchSuggestions(queryString)
  cb(response.data.map(item => ({
    label: item.suggestion,
    value: item.suggestion,
    type: 'suggestion',
    count: item.count
  })))
}

const handleSelect = (item) => {
  handleSearch(item.value)
}

const handleSearch = (value) => {
  router.push({
    name: 'AssetList',
    query: { keyword: value }
  })
}
</script>
```

---

## 8. 搜索服务

```python
# apps/search/services.py

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

class SmartSearchService:
    """智能搜索服务"""

    def __init__(self):
        self.es = Elasticsearch(['http://localhost:9200'])
        self.index = 'assets'

    def search_assets(self, keyword, filters, sort_by='relevance', page=1, page_size=20):
        """搜索资产"""
        from django.conf import settings

        # 构建查询
        query = {
            "bool": {
                "must": [],
                "filter": [
                    {"term": {"organization_id": str(filters.get('organization_id'))}},
                    {"term": {"is_deleted": False}}
                ]
            }
        }

        # 关键词搜索
        if keyword:
            query["bool"]["must"].append({
                "multi_match": {
                    "query": keyword,
                    "fields": ["asset_code^2", "asset_name^3", "specification"],
                    "fuzziness": "AUTO",
                    "prefix_length": 1
                }
            })

        # 额外过滤
        if filters.get('category'):
            query["bool"]["filter"].append({
                "term": {"category": filters['category']}
            })

        # 排序
        sort = []
        if sort_by == 'relevance':
            sort.append("_score")
        elif sort_by == 'date':
            sort.append({"purchase_date": "desc"})
        elif sort_by == 'price':
            sort.append({"purchase_price": "desc"})

        # 高亮
        highlight = {
            "fields": {
                "asset_name": {},
                "asset_code": {},
                "specification": {}
            },
            "pre_tags": ["<em>"],
            "post_tags": ["</em>"]
        }

        # 聚合
        aggs = {
            "category": {
                "terms": {"field": "category"}}
            },
            "status": {
                "terms": {"field": "status"}}
            }
        }

        # 执行搜索
        try:
            response = self.es.search(
                index=self.index,
                body={
                    "query": query,
                    "sort": sort,
                    "highlight": highlight,
                    "aggs": aggs,
                    "from": (page - 1) * page_size,
                    "size": page_size
                }
            )
            return self._parse_response(response)
        except NotFoundError:
            return {"total": 0, "results": []}

    def get_suggestions(self, keyword, organization_id):
        """获取搜索建议"""
        try:
            response = self.es.search(
                index=self.index,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "multi_match": {
                                        "query": keyword,
                                        "fields": ["asset_name^2", "asset_code"],
                                        "prefix_length": 1
                                    }
                                }
                            ],
                            "filter": [
                                {"term": {"organization_id": str(organization_id)}},
                                {"term": {"is_deleted": False}}
                            ]
                        }
                    },
                    "aggs": {
                        "suggestions": {
                            "terms": {
                                "field": "asset_name.keyword",
                                "size": 10
                            }
                        }
                    },
                    "size": 0
                }
            )

            suggestions = []
            for bucket in response['aggregations']['suggestions']['buckets']:
                suggestions.append({
                    'suggestion': bucket['key'],
                    'count': bucket['doc_count']
                })

            return suggestions
        except NotFoundError:
            return []
```

---

## 9. 数据同步

### 9.1 同步策略

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| **实时同步** | Django信号触发，立即同步到ES | 数据量小，实时性要求高 |
| **定时同步** | Celery定时任务，批量同步 | 数据量大，允许延迟 |
| **Logstash** | Logstash管道同步 | 生产环境推荐 |

### 9.2 实时同步示例

```python
# apps/assets/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.search.services import SyncService

@receiver(post_save, sender=Asset)
def sync_asset_to_es(sender, instance, created, **kwargs):
    """资产保存时同步到ES"""
    SyncService().sync_asset(instance)

@receiver(post_delete, sender=Asset)
def delete_asset_from_es(sender, instance, **kwargs):
    """资产删除时从ES删除"""
    SyncService().delete_asset(instance.id)
```

---

## 10. 性能优化

| 优化项 | 方案 | 预期效果 |
|--------|------|---------|
| 索引优化 | 使用合适的分词器、索引字段 | 搜索速度提升5-10倍 |
| 缓存 | Redis缓存热门搜索 | 热门搜索响应<100ms |
| 分页限制 | 限制最大结果数（如1000） | 避免大结果集 |
| 异步搜索 | Celery异步执行复杂搜索 | 不阻塞UI |

---

## 11. 部署说明

### 11.1 Docker Compose配置

```yaml
services:
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

volumes:
  es_data:
```

### 11.2 Python依赖

```
elasticsearch>=8.0.0
```
