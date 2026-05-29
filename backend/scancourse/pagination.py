from rest_framework.pagination import PageNumberPagination


class LargeResultsSetPagination(PageNumberPagination):
    """For browseable catalogues (bursaries, accommodation, courses) where
    the global PAGE_SIZE of 20 was cutting lists off — the mobile screens
    load a page and reveal items client-side, so they need the whole (small)
    catalogue up front. Still capped + page_size-overridable to stay safe.
    """
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500
