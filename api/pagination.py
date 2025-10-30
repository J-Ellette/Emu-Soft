"""Result pagination for API responses."""

from typing import Any, Dict, List, Optional, TypeVar, Generic
from math import ceil

T = TypeVar("T")


class PaginationResult(Generic[T]):
    """Container for paginated results."""

    def __init__(
        self,
        items: List[T],
        page: int,
        page_size: int,
        total_items: int,
        total_pages: int,
    ) -> None:
        """Initialize pagination result.

        Args:
            items: List of items for current page
            page: Current page number
            page_size: Number of items per page
            total_items: Total number of items
            total_pages: Total number of pages
        """
        self.items = items
        self.page = page
        self.page_size = page_size
        self.total_items = total_items
        self.total_pages = total_pages

    def has_next(self) -> bool:
        """Check if there's a next page.

        Returns:
            True if next page exists
        """
        return self.page < self.total_pages

    def has_previous(self) -> bool:
        """Check if there's a previous page.

        Returns:
            True if previous page exists
        """
        return self.page > 1

    def next_page(self) -> Optional[int]:
        """Get next page number.

        Returns:
            Next page number or None
        """
        return self.page + 1 if self.has_next() else None

    def previous_page(self) -> Optional[int]:
        """Get previous page number.

        Returns:
            Previous page number or None
        """
        return self.page - 1 if self.has_previous() else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with pagination metadata
        """
        return {
            "items": self.items,
            "page": self.page,
            "page_size": self.page_size,
            "total_items": self.total_items,
            "total_pages": self.total_pages,
            "has_next": self.has_next(),
            "has_previous": self.has_previous(),
            "next_page": self.next_page(),
            "previous_page": self.previous_page(),
        }


class Paginator:
    """Basic paginator for lists of items."""

    def __init__(self, items: List[Any], page_size: int = 10) -> None:
        """Initialize paginator.

        Args:
            items: List of all items to paginate
            page_size: Number of items per page
        """
        self.items = items
        self.page_size = max(1, page_size)
        self.total_items = len(items)
        self.total_pages = ceil(self.total_items / self.page_size)

    def get_page(self, page: int = 1) -> PaginationResult:
        """Get a specific page of items.

        Args:
            page: Page number (1-indexed)

        Returns:
            PaginationResult for the requested page
        """
        # Ensure page is within valid range
        page = max(1, min(page, self.total_pages if self.total_pages > 0 else 1))

        # Calculate start and end indices
        start_idx = (page - 1) * self.page_size
        end_idx = start_idx + self.page_size

        # Get items for this page
        page_items = self.items[start_idx:end_idx]

        return PaginationResult(
            items=page_items,
            page=page,
            page_size=self.page_size,
            total_items=self.total_items,
            total_pages=self.total_pages,
        )

    def paginate(self, page: int = 1) -> PaginationResult:
        """Alias for get_page.

        Args:
            page: Page number

        Returns:
            PaginationResult
        """
        return self.get_page(page)


class PageNumberPagination:
    """Page number pagination with query parameter support."""

    page_size: int = 10
    page_query_param: str = "page"
    page_size_query_param: str = "page_size"
    max_page_size: int = 100

    def __init__(
        self,
        page_size: Optional[int] = None,
        max_page_size: Optional[int] = None,
    ) -> None:
        """Initialize pagination settings.

        Args:
            page_size: Default page size
            max_page_size: Maximum allowed page size
        """
        if page_size is not None:
            self.page_size = page_size
        if max_page_size is not None:
            self.max_page_size = max_page_size

    def get_page_number(self, query_params: Dict[str, Any]) -> int:
        """Extract page number from query parameters.

        Args:
            query_params: Dictionary of query parameters

        Returns:
            Page number (defaults to 1)
        """
        try:
            page = int(query_params.get(self.page_query_param, 1))
            return max(1, page)
        except (ValueError, TypeError):
            return 1

    def get_page_size(self, query_params: Dict[str, Any]) -> int:
        """Extract page size from query parameters.

        Args:
            query_params: Dictionary of query parameters

        Returns:
            Page size (respects max_page_size limit)
        """
        try:
            size = int(query_params.get(self.page_size_query_param, self.page_size))
            return max(1, min(size, self.max_page_size))
        except (ValueError, TypeError):
            return self.page_size

    def paginate(
        self,
        items: List[Any],
        query_params: Optional[Dict[str, Any]] = None,
    ) -> PaginationResult:
        """Paginate items based on query parameters.

        Args:
            items: List of items to paginate
            query_params: Query parameters from request

        Returns:
            PaginationResult
        """
        query_params = query_params or {}

        page = self.get_page_number(query_params)
        page_size = self.get_page_size(query_params)

        paginator = Paginator(items, page_size)
        return paginator.get_page(page)

    def paginate_response(
        self,
        items: List[Any],
        query_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Paginate and return response dictionary.

        Args:
            items: List of items to paginate
            query_params: Query parameters from request

        Returns:
            Dictionary with results and pagination metadata
        """
        result = self.paginate(items, query_params)
        return result.to_dict()


class CursorPagination:
    """Cursor-based pagination for large datasets."""

    page_size: int = 10
    cursor_query_param: str = "cursor"
    ordering: str = "id"

    def __init__(self, page_size: Optional[int] = None) -> None:
        """Initialize cursor pagination.

        Args:
            page_size: Number of items per page
        """
        if page_size is not None:
            self.page_size = page_size

    def encode_cursor(self, value: Any) -> str:
        """Encode cursor value.

        Args:
            value: Value to encode

        Returns:
            Encoded cursor string
        """
        import base64

        cursor_str = str(value)
        return base64.b64encode(cursor_str.encode()).decode()

    def decode_cursor(self, cursor: str) -> Optional[Any]:
        """Decode cursor value.

        Args:
            cursor: Encoded cursor string

        Returns:
            Decoded value or None
        """
        import base64

        try:
            decoded = base64.b64decode(cursor.encode()).decode()
            return decoded
        except Exception:
            return None

    def paginate(
        self,
        items: List[Any],
        query_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Paginate items using cursor.

        Args:
            items: List of items to paginate
            query_params: Query parameters from request

        Returns:
            Dictionary with results and cursor metadata
        """
        query_params = query_params or {}
        cursor = query_params.get(self.cursor_query_param)

        # If cursor provided, find starting position
        start_idx = 0
        if cursor:
            decoded_cursor = self.decode_cursor(cursor)
            if decoded_cursor:
                # Find position in list
                for idx, item in enumerate(items):
                    if str(getattr(item, self.ordering, None)) == decoded_cursor:
                        start_idx = idx + 1
                        break

        # Get page of items
        end_idx = start_idx + self.page_size
        page_items = items[start_idx:end_idx]

        # Generate next cursor
        next_cursor = None
        if end_idx < len(items) and page_items:
            last_item = page_items[-1]
            next_value = getattr(last_item, self.ordering, None)
            if next_value:
                next_cursor = self.encode_cursor(next_value)

        return {
            "items": page_items,
            "next_cursor": next_cursor,
            "has_more": end_idx < len(items),
        }
