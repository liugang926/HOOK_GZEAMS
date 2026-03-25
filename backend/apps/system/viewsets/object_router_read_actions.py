from contextlib import contextmanager

from rest_framework.response import Response


class ObjectRouterReadActionsMixin:
    @contextmanager
    def _override_delegate_filter_queryset(self, request):
        lookup_search_params = self._get_lookup_search_params(request)
        constrained_search_params = self._get_constrained_search_params(request)
        delegate = getattr(self, '_delegate_viewset', None)
        original_filter_queryset = None

        if delegate is not None and hasattr(delegate, 'filter_queryset'):
            if lookup_search_params:
                original_filter_queryset = delegate.filter_queryset

                def _lookup_filter_wrapper(queryset):
                    filtered = self._filter_queryset_without_query_params(
                        request=request,
                        filter_callable=original_filter_queryset,
                        queryset=queryset,
                        keys_to_strip=['search'],
                    )
                    return self._apply_lookup_scoped_search(filtered, lookup_search_params)

                delegate.filter_queryset = _lookup_filter_wrapper
            elif constrained_search_params:
                original_filter_queryset = delegate.filter_queryset

                def _constrained_search_filter_wrapper(queryset):
                    filtered = self._filter_queryset_without_query_params(
                        request=request,
                        filter_callable=original_filter_queryset,
                        queryset=queryset,
                        keys_to_strip=['search', 'search_fields', 'searchFields'],
                    )
                    return self._apply_constrained_search(request, filtered, constrained_search_params)

                delegate.filter_queryset = _constrained_search_filter_wrapper

        try:
            yield
        finally:
            if delegate is not None and original_filter_queryset is not None:
                delegate.filter_queryset = original_filter_queryset

    def _build_paginated_list_payload(self, items):
        return {
            'success': True,
            'data': {
                'count': len(items),
                'next': None,
                'previous': None,
                'results': items,
            },
        }

    def _normalize_list_response(self, response):
        try:
            if isinstance(response, Response) and isinstance(getattr(response, 'data', None), dict):
                payload = response.data
                if payload.get('success') is True:
                    if isinstance(payload.get('data'), list):
                        response.data = self._build_paginated_list_payload(payload.get('data') or [])
                    return response

                if 'count' in payload and 'results' in payload:
                    response.data = {'success': True, 'data': payload}
        except Exception:
            pass

        try:
            if isinstance(response, Response) and isinstance(getattr(response, 'data', None), list):
                response.data = self._build_paginated_list_payload(response.data or [])
        except Exception:
            pass

        return response

    def _set_delegate_lookup_pk(self, kwargs):
        if 'id' not in kwargs or not getattr(self, '_delegate_viewset', None):
            return

        delegate_kwargs = dict(getattr(self._delegate_viewset, 'kwargs', {}) or {})
        delegate_kwargs['pk'] = kwargs['id']
        self._delegate_viewset.kwargs = delegate_kwargs

    def list(self, request, *args, **kwargs):
        """
        List objects with pagination, filtering, and search.

        GET /api/objects/{code}/
        """
        with self._override_delegate_filter_queryset(request):
            response = self._delegate_viewset.list(request, *args, **kwargs)
        return self._normalize_list_response(response)

    def retrieve(self, request, *args, **kwargs):
        """
        Get a single object by ID.

        GET /api/objects/{code}/{id}/
        """
        self._set_delegate_lookup_pk(kwargs)
        return self._delegate_viewset.retrieve(request, *args, **kwargs)
