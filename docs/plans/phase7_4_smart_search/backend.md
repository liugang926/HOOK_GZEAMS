# Phase 7.4: 智能搜索增强 - 后端实现

## 1. 功能概述

### 1.1 业务场景

引入Elasticsearch全文搜索引擎，实现资产快速检索、搜索建议、历史记录等功能。

| 业务类型 | 场景 | 核心价值 |
|---------|------|----------|
| **全文搜索** | 对资产名称、编号、规格进行全文索引 | 快速定位资产 |
| **搜索联想** | 输入时实时提示搜索关键词 | 减少输入成本 |
| **搜索历史** | 记录用户搜索历史 | 快速重复搜索 |
| **高级搜索** | 保存常用搜索条件 | 提高工作效率 |
| **结果高亮** | 搜索关键词高亮显示 | 突出显示匹配内容 |
| **聚合筛选** | 搜索结果按分类、状态等聚合 | 逐步精确定位 |

### 1.2 用户角色与权限

| 角色 | 权限 |
|------|------|
| **所有用户** | 使用搜索功能、查看搜索历史、保存个人搜索 |
| **系统管理员** | 配置搜索索引、管理同义词、查看搜索统计 |

---

## 2. 公共模型引用声明

### 2.1 后端公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| **Model** | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、custom_fields |
| **Serializer** | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化、custom_fields序列化 |
| **ViewSet** | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作、审计字段设置 |
| **Filter** | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤、状态过滤 |
| **Service** | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一CRUD方法、组织隔离、分页查询 |

---

## 3. 数据模型设计

### 3.1 SearchHistory（搜索历史）

**Model Definition**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **关联** |
| user | FK(User) | CASCADE, related_name='search_histories' | 用户 |
| **搜索信息** |
| search_type | string | max_length=20, choices | 搜索类型: asset/project/... |
| keyword | string | max_length=200 | 搜索关键词 |
| filters | JSONField | default=dict | 保存的筛选条件 |
| **统计** |
| result_count | int | default=0 | 搜索结果数量 |
| search_count | int | default=1 | 搜索次数（重复搜索累加） |
| **时间** |
| last_searched_at | datetime | auto_now=True | 最后搜索时间 |

**索引**：
- `user + search_type`
- `keyword` (支持模糊搜索)

### 3.2 SavedSearch（保存的搜索）

**Model Definition**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **关联** |
| user | FK(User) | CASCADE, related_name='saved_searches' | 用户 |
| **基础信息** |
| name | string | max_length=100 | 搜索名称 |
| search_type | string | max_length=20, choices | 搜索类型 |
| **搜索条件** |
| keyword | string | max_length=200, blank=True | 搜索关键词 |
| filters | JSONField | default=dict | 筛选条件 |
| **设置** |
| is_public | boolean | default=False | 是否公开给其他人 |
| **统计** |
| use_count | int | default=0 | 使用次数 |

**复合唯一索引**：`(user, name)`

---

## 4. Elasticsearch索引设计

### 4.1 资产索引（assets）

```json
PUT /assets
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "analysis": {
      "analyzer": {
        "ik_max_word": {
          "type": "custom",
          "tokenizer": "ik_max_word"
        },
        "ik_smart": {
          "type": "custom",
          "tokenizer": "ik_smart"
        },
        "pinyin_analyzer": {
          "tokenizer": "ik_max_word",
          "filter": ["lowercase", "pinyin"]
        }
      },
      "filter": {
        "pinyin": {
          "type": "pinyin",
          "keep_separate_first_letter": false,
          "keep_full_pinyin": true,
          "keep_original": true,
          "limit_first_letter_length": 16
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "asset_id": {
        "type": "keyword"
      },
      "asset_code": {
        "type": "text",
        "fields": {
          "keyword": {"type": "keyword"}
        },
        "analyzer": "ik_max_word"
      },
      "asset_name": {
        "type": "text",
        "analyzer": "ik_max_word",
        "fields": {
          "keyword": {"type": "keyword"},
          "pinyin": {
            "type": "text",
            "analyzer": "pinyin_analyzer"
          }
        }
      },
      "specification": {
        "type": "text",
        "analyzer": "ik_max_word"
      },
      "category": {
        "type": "keyword"
      },
      "category_name": {
        "type": "text",
        "fields": {
          "keyword": {"type": "keyword"}
        },
        "analyzer": "ik_max_word"
      },
      "status": {
        "type": "keyword"
      },
      "status_display": {
        "type": "keyword"
      },
      "purchase_price": {
        "type": "double"
      },
      "location": {
        "type": "keyword"
      },
      "location_name": {
        "type": "text",
        "analyzer": "ik_max_word",
        "fields": {
          "keyword": {"type": "keyword"}
        }
      },
      "custodian": {
        "type": "keyword"
      },
      "custodian_name": {
        "type": "text",
        "fields": {
          "keyword": {"type": "keyword"}
        },
        "analyzer": "ik_max_word"
      },
      "manufacturer": {
        "type": "text",
        "analyzer": "ik_max_word"
      },
      "model": {
        "type": "text",
        "analyzer": "ik_max_word"
      },
      "tags": {
        "type": "keyword"
      },
      "tag_names": {
        "type": "text",
        "fields": {
          "keyword": {"type": "keyword"}
        },
        "analyzer": "ik_max_word"
      },
      "organization_id": {
        "type": "keyword"
      },
      "is_deleted": {
        "type": "boolean"
      },
      "created_at": {
        "type": "date"
      },
      "updated_at": {
        "type": "date"
      }
    }
  }
}
```

### 4.2 索引配置说明

| 字段配置 | 说明 |
|---------|------|
| ik_max_word | 中文分词器，细粒度分词 |
| ik_smart | 中文分词器，粗粒度分词 |
| pinyin | 拼音分词，支持拼音搜索 |
| keyword子字段 | 精确匹配和聚合 |
| text类型 | 全文搜索 |

---

## 5. 序列化器设计

### 5.1 SearchHistorySerializer

```python
from apps.common.serializers.base import BaseModelSerializer
from apps.accounts.serializers import UserSerializer

class SearchHistorySerializer(BaseModelSerializer):
    """搜索历史序列化器"""

    user_detail = UserSerializer(source='user', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = SearchHistory
        fields = BaseModelSerializer.Meta.fields + [
            'user', 'user_detail',
            'search_type', 'keyword', 'filters',
            'result_count', 'search_count',
            'last_searched_at'
        ]

    def create(self, validated_data):
        """创建或更新搜索历史"""
        from django.db.models import Q

        user = validated_data.get('user')
        keyword = validated_data.get('keyword')
        search_type = validated_data.get('search_type')
        filters = validated_data.get('filters', {})

        # 查找是否已有相同搜索
        history = SearchHistory.objects.filter(
            user=user,
            search_type=search_type,
            keyword=keyword
        ).first()

        if history:
            # 更新搜索次数
            history.search_count += 1
            history.filters = filters
            history.last_searched_at = timezone.now()
            history.save()
            return history

        return super().create(validated_data)
```

### 5.2 SavedSearchSerializer

```python
class SavedSearchSerializer(BaseModelSerializer):
    """保存的搜索序列化器"""

    user_detail = UserSerializer(source='user', read_only=True)
    search_type_display = serializers.CharField(source='get_search_type_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = SavedSearch
        fields = BaseModelSerializer.Meta.fields + [
            'user', 'user_detail',
            'name', 'search_type', 'search_type_display',
            'keyword', 'filters', 'is_public',
            'use_count'
        ]

    def validate(self, data):
        """验证"""
        user = self.context['request'].user
        name = data.get('name')

        # 检查同名
        if SavedSearch.objects.filter(
            user=user,
            name=name
        ).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError({'name': '已存在同名搜索'})

        return data
```

### 5.3 SearchRequestSerializer

```python
class SearchRequestSerializer(serializers.Serializer):
    """搜索请求序列化器"""

    keyword = serializers.CharField(max_length=200, required=False, allow_blank=True)
    filters = serializers.JSONField(default=dict)
    sort_by = serializers.ChoiceField(
        choices=['relevance', 'date', 'price', 'code'],
        default='relevance'
    )
    sort_order = serializers.ChoiceField(
        choices=['asc', 'desc'],
        default='desc'
    )
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100)

    def validate_filters(self, value):
        """验证筛选条件"""
        # 定义允许的筛选字段
        allowed_fields = {
            'category', 'status', 'location', 'manufacturer',
            'purchase_price_min', 'purchase_price_max',
            'purchase_date_from', 'purchase_date_to'
        }

        for key in value:
            if key not in allowed_fields:
                raise serializers.ValidationError(f'不支持的筛选条件: {key}')

        return value
```

### 5.4 SearchResultSerializer

```python
class SearchResultSerializer(serializers.Serializer):
    """搜索结果序列化器"""

    id = serializers.CharField()
    asset_code = serializers.CharField()
    asset_name = serializers.CharField()
    highlight = serializers.JSONField()
    score = serializers.FloatField()
    category = serializers.CharField()
    category_name = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    purchase_price = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True)
    location = serializers.CharField(allow_null=True)
    location_name = serializers.CharField(allow_null=True)
    custodian = serializers.CharField(allow_null=True)
    custodian_name = serializers.CharField(allow_null=True)
    tags = serializers.ListField(child=serializers.CharField())
```

---

## 6. ViewSet 设计

### 6.1 SearchViewSet

```python
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.search.services import SmartSearchService

class SearchViewSet(BaseModelViewSetWithBatch):
    """搜索ViewSet"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_service = SmartSearchService()

    @action(detail=False, methods=['post'])
    def assets(self, request):
        """搜索资产"""
        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = self.search_service.search_assets(
            organization=request.user.organization,
            **serializer.validated_data
        )

        return Response({
            'success': True,
            'data': result
        })

    @action(detail=False, methods=['get'])
    def suggestions(self, request):
        """获取搜索建议"""
        keyword = request.query_params.get('keyword', '')
        search_type = request.query_params.get('type', 'asset')

        if len(keyword) < 1:
            return Response({
                'success': True,
                'data': []
            })

        suggestions = self.search_service.get_suggestions(
            keyword=keyword,
            search_type=search_type,
            organization=request.user.organization
        )

        return Response({
            'success': True,
            'data': suggestions
        })

    @action(detail=False, methods=['get'])
    def history(self, request):
        """获取搜索历史"""
        from apps.search.models import SearchHistory
        from apps.search.serializers import SearchHistorySerializer

        search_type = request.query_params.get('type', 'asset')
        limit = int(request.query_params.get('limit', 10))

        histories = SearchHistory.objects.filter(
            user=request.user,
            search_type=search_type
        ).order_by('-last_searched_at')[:limit]

        serializer = SearchHistorySerializer(histories, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def save(self, request):
        """保存搜索"""
        from apps.search.models import SavedSearch
        from apps.search.serializers import SavedSearchSerializer

        serializer = SavedSearchSerializer(data={
            **request.data,
            'user': request.user.id
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'success': True,
            'message': '搜索保存成功',
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def saved(self, request):
        """获取保存的搜索"""
        from apps.search.models import SavedSearch
        from apps.search.serializers import SavedSearchSerializer

        search_type = request.query_params.get('type', 'asset')

        # 获取自己的和公开的搜索
        searches = SavedSearch.objects.filter(
            models.Q(user=request.user) | models.Q(is_public=True),
            search_type=search_type
        ).distinct().order_by('-created_at')

        serializer = SavedSearchSerializer(searches, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
```

### 6.2 SearchHistoryViewSet

```python
class SearchHistoryViewSet(BaseModelViewSetWithBatch):
    """搜索历史ViewSet"""

    queryset = SearchHistory.objects.all()
    serializer_class = SearchHistorySerializer

    def get_queryset(self):
        """只返回当前用户的历史"""
        return super().get_queryset().filter(user=self.request.user)

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """清空搜索历史"""
        search_type = request.query_params.get('type')

        qs = self.get_queryset()
        if search_type:
            qs = qs.filter(search_type=search_type)

        count, _ = qs.delete()
        return Response({
            'success': True,
            'message': f'已删除{count}条历史记录'
        })
```

### 6.3 SavedSearchViewSet

```python
class SavedSearchViewSet(BaseModelViewSetWithBatch):
    """保存的搜索ViewSet"""

    queryset = SavedSearch.objects.all()
    serializer_class = SavedSearchSerializer

    def get_queryset(self):
        """只返回当前用户的搜索和公开搜索"""
        return super().get_queryset().filter(
            models.Q(user=self.request.user) | models.Q(is_public=True)
        )

    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """使用保存的搜索"""
        saved_search = self.get_object()
        saved_search.use_count += 1
        saved_search.save()

        return Response({
            'success': True,
            'data': {
                'id': saved_search.id,
                'name': saved_search.name,
                'keyword': saved_search.keyword,
                'filters': saved_search.filters
            }
        })
```

---

## 7. Service 设计

### 7.1 SmartSearchService

```python
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError, RequestError
from django.conf import settings
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class SmartSearchService:
    """智能搜索服务"""

    def __init__(self):
        self.es = Elasticsearch(
            settings.ELASTICSEARCH.get('hosts', ['http://localhost:9200']),
            **settings.ELASTICSEARCH.get('options', {})
        )
        self.index_prefix = settings.ELASTICSEARCH.get('index_prefix', 'gzeams')

    def _get_index_name(self, search_type: str) -> str:
        """获取索引名称"""
        return f'{self.index_prefix}_{search_type}'

    def search_assets(self, organization, keyword='', filters=None,
                     sort_by='relevance', sort_order='desc',
                     page=1, page_size=20) -> Dict[str, Any]:
        """搜索资产"""
        index = self._get_index_name('asset')

        # 构建查询
        query = self._build_query(
            keyword=keyword,
            filters=filters or {},
            organization_id=str(organization.id)
        )

        # 构建排序
        sort = self._build_sort(sort_by, sort_order, keyword)

        # 高亮配置
        highlight = {
            "fields": {
                "asset_name": {},
                "asset_code": {},
                "specification": {},
                "manufacturer": {},
                "model": {}
            },
            "pre_tags": ["<em>"],
            "post_tags": ["</em>"],
            "fragment_size": 150
        }

        # 聚合
        aggs = self._build_aggregations()

        # 执行搜索
        try:
            response = self.es.search(
                index=index,
                body={
                    "query": query,
                    "sort": sort,
                    "highlight": highlight,
                    "aggs": aggs,
                    "from": (page - 1) * page_size,
                    "size": page_size
                }
            )
            return self._parse_search_response(response, page, page_size)
        except NotFoundError:
            # 索引不存在
            return {
                'total': 0,
                'page': page,
                'page_size': page_size,
                'results': [],
                'aggregations': {}
            }
        except RequestError as e:
            logger.error(f"Search error: {e}")
            raise

    def _build_query(self, keyword, filters, organization_id) -> Dict:
        """构建查询"""
        must = []
        filter_ctx = [
            {"term": {"organization_id": organization_id}},
            {"term": {"is_deleted": False}}
        ]

        # 关键词搜索
        if keyword:
            must.append({
                "multi_match": {
                    "query": keyword,
                    "fields": [
                        "asset_name^3",
                        "asset_code^2",
                        "specification^1.5",
                        "manufacturer",
                        "model",
                        "category_name",
                        "location_name",
                        "tag_names"
                    ],
                    "fuzziness": "AUTO",
                    "prefix_length": 1,
                    "operator": "or"
                }
            })

        # 筛选条件
        if 'category' in filters and filters['category']:
            filter_ctx.append({"term": {"category": filters['category']}})

        if 'status' in filters and filters['status']:
            filter_ctx.append({"term": {"status": filters['status']}})

        if 'location' in filters and filters['location']:
            filter_ctx.append({"term": {"location": filters['location']}})

        if 'manufacturer' in filters and filters['manufacturer']:
            filter_ctx.append({"term": {"manufacturer": filters['manufacturer']}})

        if 'tags' in filters and filters['tags']:
            filter_ctx.append({"terms": {"tags": filters['tags']}})

        # 价格范围
        if 'purchase_price_min' in filters:
            filter_ctx.append({
                "range": {"purchase_price": {"gte": filters['purchase_price_min']}}
            })

        if 'purchase_price_max' in filters:
            filter_ctx.append({
                "range": {"purchase_price": {"lte": filters['purchase_price_max']}}
            })

        # 日期范围
        if 'purchase_date_from' in filters or 'purchase_date_to' in filters:
            range_filter = {"range": {"purchase_date": {}}}
            if 'purchase_date_from' in filters:
                range_filter["range"]["purchase_date"]["gte"] = filters['purchase_date_from']
            if 'purchase_date_to' in filters:
                range_filter["range"]["purchase_date"]["lte"] = filters['purchase_date_to']
            filter_ctx.append(range_filter)

        return {
            "bool": {
                "must": must,
                "filter": filter_ctx
            }
        }

    def _build_sort(self, sort_by, sort_order, keyword) -> List:
        """构建排序"""
        order = 'desc' if sort_order == 'desc' else 'asc'

        if sort_by == 'relevance' and keyword:
            # 有关键词时按相关性排序
            return ["_score", {"created_at": {"order": "desc"}}]
        elif sort_by == 'date':
            return [{"purchase_date": {"order": order}}, "_score"]
        elif sort_by == 'price':
            return [{"purchase_price": {"order": order}}, "_score"]
        elif sort_by == 'code':
            return [{"asset_code.keyword": {"order": order}}]
        else:
            return ["_score"]

    def _build_aggregations(self) -> Dict:
        """构建聚合"""
        return {
            "category": {
                "terms": {"field": "category", "size": 50}
            },
            "status": {
                "terms": {"field": "status", "size": 20}
            },
            "location": {
                "terms": {"field": "location", "size": 50}
            },
            "manufacturer": {
                "terms": {"field": "manufacturer", "size": 50}
            },
            "price_ranges": {
                "range": {
                    "field": "purchase_price",
                    "ranges": [
                        {"to": 1000, "key": "under_1k"},
                        {"from": 1000, "to": 5000, "key": "1k_to_5k"},
                        {"from": 5000, "to": 10000, "key": "5k_to_10k"},
                        {"from": 10000, "to": 50000, "key": "10k_to_50k"},
                        {"from": 50000, "key": "over_50k"}
                    ]
                }
            }
        }

    def _parse_search_response(self, response, page, page_size) -> Dict:
        """解析搜索响应"""
        hits = response['hits']
        total = hits['total']['value']

        results = []
        for hit in hits['hits']:
            source = hit['_source']
            results.append({
                'id': source.get('asset_id'),
                'asset_code': source.get('asset_code'),
                'asset_name': source.get('asset_name'),
                'highlight': hit.get('highlight', {}),
                'score': hit['_score'],
                'category': source.get('category'),
                'category_name': source.get('category_name'),
                'status': source.get('status'),
                'status_display': source.get('status_display'),
                'purchase_price': source.get('purchase_price'),
                'location': source.get('location'),
                'location_name': source.get('location_name'),
                'custodian': source.get('custodian'),
                'custodian_name': source.get('custodian_name'),
                'tags': source.get('tags', [])
            })

        # 解析聚合
        aggregations = {}
        for agg_name, agg_data in response.get('aggregations', {}).items():
            if agg_name == 'price_ranges':
                aggregations[agg_name] = {
                    bucket['key']: bucket['doc_count']
                    for bucket in agg_data['buckets']
                }
            else:
                aggregations[agg_name] = {
                    bucket['key']: bucket['doc_count']
                    for bucket in agg_data['buckets']
                }

        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size if total > 0 else 0,
            'results': results,
            'aggregations': aggregations
        }

    def get_suggestions(self, keyword, search_type, organization) -> List[Dict]:
        """获取搜索建议"""
        index = self._get_index_name(search_type)

        if search_type == 'asset':
            field = 'asset_name.keyword'
        else:
            field = 'name.keyword'

        try:
            response = self.es.search(
                index=index,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "prefix": {
                                        field: {
                                            "value": keyword,
                                            "case_insensitive": True
                                        }
                                    }
                                }
                            ],
                            "filter": [
                                {"term": {"organization_id": str(organization.id)}},
                                {"term": {"is_deleted": False}}
                            ]
                        }
                    },
                    "aggs": {
                        "suggestions": {
                            "terms": {
                                "field": field,
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
        except (NotFoundError, RequestError):
            return []

    def sync_asset(self, asset):
        """同步资产到ES"""
        from apps.assets.models import Asset

        index = self._get_index_name('asset')

        try:
            # 获取标签名称
            tag_names = []
            if hasattr(asset, 'tag_relations'):
                tag_names = [
                    rel.tag.name
                    for rel in asset.tag_relations.all()
                ]

            doc = {
                'asset_id': str(asset.id),
                'asset_code': asset.asset_code,
                'asset_name': asset.asset_name,
                'specification': asset.specification or '',
                'category': str(asset.category_id) if asset.category_id else None,
                'category_name': asset.category.name if asset.category else '',
                'status': asset.asset_status,
                'status_display': asset.get_asset_status_display(),
                'purchase_price': float(asset.purchase_price) if asset.purchase_price else None,
                'location': str(asset.location_id) if asset.location_id else None,
                'location_name': asset.location.name if asset.location else '',
                'custodian': str(asset.custodian_id) if asset.custodian_id else None,
                'custodian_name': asset.custodian.get_full_name() if asset.custodian else '',
                'manufacturer': asset.manufacturer or '',
                'model': asset.model or '',
                'organization_id': str(asset.organization_id),
                'is_deleted': asset.is_deleted,
                'tags': [str(rel.tag_id) for rel in asset.tag_relations.all()],
                'tag_names': tag_names,
                'created_at': asset.created_at.isoformat(),
                'updated_at': asset.updated_at.isoformat()
            }

            self.es.index(
                index=index,
                id=str(asset.id),
                body=doc,
                refresh=True
            )
            return True
        except Exception as e:
            logger.error(f"Error syncing asset {asset.id} to ES: {e}")
            return False

    def delete_asset(self, asset_id):
        """从ES删除资产"""
        index = self._get_index_name('asset')

        try:
            self.es.delete(
                index=index,
                id=str(asset_id)
            )
            return True
        except NotFoundError:
            # 文档不存在，视为成功
            return True
        except Exception as e:
            logger.error(f"Error deleting asset {asset_id} from ES: {e}")
            return False

    def bulk_sync_assets(self, assets):
        """批量同步资产"""
        from elasticsearch.helpers import bulk

        index = self._get_index_name('asset')

        actions = []
        for asset in assets:
            try:
                tag_names = [
                    rel.tag.name
                    for rel in asset.tag_relations.all()
                ]

                doc = {
                    '_index': index,
                    '_id': str(asset.id),
                    '_source': {
                        'asset_id': str(asset.id),
                        'asset_code': asset.asset_code,
                        'asset_name': asset.asset_name,
                        'specification': asset.specification or '',
                        'category': str(asset.category_id) if asset.category_id else None,
                        'category_name': asset.category.name if asset.category else '',
                        'status': asset.asset_status,
                        'status_display': asset.get_asset_status_display(),
                        'purchase_price': float(asset.purchase_price) if asset.purchase_price else None,
                        'location': str(asset.location_id) if asset.location_id else None,
                        'location_name': asset.location.name if asset.location else '',
                        'custodian': str(asset.custodian_id) if asset.custodian_id else None,
                        'custodian_name': asset.custodian.get_full_name() if asset.custodian else '',
                        'manufacturer': asset.manufacturer or '',
                        'model': asset.model or '',
                        'organization_id': str(asset.organization_id),
                        'is_deleted': asset.is_deleted,
                        'tags': [str(rel.tag_id) for rel in asset.tag_relations.all()],
                        'tag_names': tag_names,
                        'created_at': asset.created_at.isoformat(),
                        'updated_at': asset.updated_at.isoformat()
                    }
                }
                actions.append(doc)
            except Exception as e:
                logger.error(f"Error preparing asset {asset.id}: {e}")

        try:
            success, failed = bulk(self.es, actions, raise_on_error=False)
            return {'success': success, 'failed': failed}
        except Exception as e:
            logger.error(f"Bulk sync error: {e}")
            return {'success': 0, 'failed': len(actions)}
```

---

## 8. 数据同步

### 8.1 Django信号同步

```python
# apps/search/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.search.services import SmartSearchService

search_service = SmartSearchService()

@receiver(post_save, sender=Asset)
def sync_asset_to_es(sender, instance, created, **kwargs):
    """资产保存时同步到ES"""
    search_service.sync_asset(instance)

@receiver(post_delete, sender=Asset)
def delete_asset_from_es(sender, instance, **kwargs):
    """资产删除时从ES删除"""
    search_service.delete_asset(instance.id)
```

### 8.2 Celery批量同步

```python
# apps/search/tasks.py

from celery import shared_task
from apps.search.services import SmartSearchService

@shared_task
def sync_all_assets_to_es():
    """同步所有资产到ES"""
    from apps.assets.models import Asset

    search_service = SmartSearchService()

    # 分批处理
    batch_size = 500
    offset = 0

    total_synced = 0
    while True:
        assets = Asset.objects.filter(is_deleted=False)[offset:offset + batch_size]
        if not assets:
            break

        result = search_service.bulk_sync_assets(assets)
        total_synced += result.get('success', 0)
        offset += batch_size

    return {
        'total_synced': total_synced,
        'status': 'completed'
    }

@shared_task
def rebuild_asset_index():
    """重建资产索引"""
    from apps.search.services import SmartSearchService

    service = SmartSearchService()
    index = service._get_index_name('asset')

    # 删除旧索引
    try:
        service.es.indices.delete(index=index)
    except:
        pass

    # 创建新索引
    # ... 创建索引配置 ...

    # 同步数据
    return sync_all_assets_to_es()
```

---

## 9. 配置

### 9.1 Django配置

```python
# settings.py

ELASTICSEARCH = {
    'hosts': ['http://localhost:9200'],
    'options': {
        'timeout': 30,
        'max_retries': 3,
        'retry_on_timeout': True
    },
    'index_prefix': 'gzeams'
}
```

### 9.2 Celery配置

```python
# Celery Beat 定时任务
CELERY_BEAT_SCHEDULE = {
    'sync-assets-to-es': {
        'task': 'apps.search.tasks.sync_all_assets_to_es',
        'schedule': crontab(minute=0, hour='*'),  # 每小时执行
    },
}
```

---

## 10. 数据库迁移

```python
# Generated by Django 5.0 on 2025-01-20

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # ========== SearchHistory 模型 ==========
        migrations.CreateModel(
            name='SearchHistory',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('search_type', models.CharField(
                    max_length=20,
                    choices=[
                        ('asset', '资产'),
                        ('project', '项目'),
                        ('loan', '借用'),
                        ('inventory', '盘点')
                    ],
                    default='asset'
                )),
                ('keyword', models.CharField(max_length=200)),
                ('filters', models.JSONField(default=dict)),
                ('result_count', models.IntegerField(default=0)),
                ('search_count', models.IntegerField(default=1)),
                ('last_searched_at', models.DateTimeField(auto_now=True)),
                # BaseModel fields
                ('organization', models.ForeignKey('organizations.Organization', on_delete=models.PROTECT)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey('accounts.User', on_delete=models.PROTECT)),
                ('custom_fields', models.JSONField(default=dict)),
                # Foreign keys
                ('user', models.ForeignKey(
                    'accounts.User',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='search_histories'
                )),
            ],
            options={
                'db_table': 'search_history',
                'indexes': [
                    models.Index(fields=['user', 'search_type']),
                    models.Index(fields=['keyword']),
                    models.Index(fields=['-last_searched_at']),
                ],
            },
        ),

        # ========== SavedSearch 模型 ==========
        migrations.CreateModel(
            name='SavedSearch',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('search_type', models.CharField(
                    max_length=20,
                    choices=[
                        ('asset', '资产'),
                        ('project', '项目'),
                        ('loan', '借用'),
                        ('inventory', '盘点')
                    ],
                    default='asset'
                )),
                ('keyword', models.CharField(max_length=200, blank=True)),
                ('filters', models.JSONField(default=dict)),
                ('is_public', models.BooleanField(default=False)),
                ('use_count', models.IntegerField(default=0)),
                # BaseModel fields
                ('organization', models.ForeignKey('organizations.Organization', on_delete=models.PROTECT)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey('accounts.User', on_delete=models.PROTECT)),
                ('custom_fields', models.JSONField(default=dict)),
                # Foreign keys
                ('user', models.ForeignKey(
                    'accounts.User',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='saved_searches'
                )),
            ],
            options={
                'db_table': 'saved_search',
                'indexes': [
                    models.Index(fields=['user', 'search_type']),
                    models.Index(fields=['-created_at']),
                ],
                'constraints': [
                    models.UniqueConstraint(
                        fields=['user', 'name'],
                        name='unique_user_search_name'
                    ),
                ],
            },
        ),
    ]
```

---

## 11. API错误码

| 错误码 | HTTP状态 | 说明 |
|--------|---------|------|
| `SEARCH_INDEX_UNAVAILABLE` | 503 | 搜索服务不可用 |
| `INVALID_SEARCH_QUERY` | 400 | 搜索查询无效 |
| `SEARCH_TIMEOUT` | 504 | 搜索超时 |
| `SAVED_SEARCH_NOT_FOUND` | 404 | 保存的搜索不存在 |
| `SAVED_SEARCH_NAME_EXISTS` | 400 | 搜索名称已存在 |
