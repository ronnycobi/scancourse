from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from . import client


class SearchView(APIView):
    """Unified search endpoint — supports single-index or all-indexes."""
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'detail': 'Provide a query with ?q='}, status=400)

        index_name = request.query_params.get('index')  # courses | institutions | bursaries | None=all
        limit = min(int(request.query_params.get('limit', 20)), 50)

        # Build optional filter from query params
        filter_parts = []
        for key in ('field', 'province', 'institution_type', 'funding_type', 'level'):
            val = request.query_params.get(key)
            if val:
                filter_parts.append(f'{key} = "{val}"')
        min_aps = request.query_params.get('min_aps')
        max_aps = request.query_params.get('max_aps')
        if min_aps:
            filter_parts.append(f'min_aps >= {int(min_aps)}')
        if max_aps:
            filter_parts.append(f'min_aps <= {int(max_aps)}')
        filter_str = ' AND '.join(filter_parts) if filter_parts else None

        try:
            if index_name in client.INDEXES:
                results = client.search(index_name, query, filters=filter_str, limit=limit)
                return Response(results)
            else:
                results = client.multi_search(query, limit=limit)
                return Response(results)
        except Exception as e:
            return Response({'detail': f'Search error: {e}'}, status=500)


class SearchSuggestView(APIView):
    """Lightweight autocomplete — top 5 hits with just names."""
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return Response([])

        try:
            results = client.multi_search(query, limit=4)
            suggestions = []
            for index_result in results.get('results', []):
                index_uid = index_result.get('indexUid')
                for hit in index_result.get('hits', [])[:4]:
                    suggestions.append({
                        'type': index_uid,
                        'id': hit.get('id'),
                        'name': hit.get('name'),
                    })
            return Response(suggestions[:10])
        except Exception:
            return Response([])
