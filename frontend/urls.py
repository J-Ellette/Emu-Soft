"""URL routing configuration for frontend views."""

from typing import Optional
from framework.routing import Router
from frontend.views import FrontendViews


def create_frontend_routes(
    router: Optional[Router] = None, views: Optional[FrontendViews] = None
) -> Router:
    """Create and configure frontend URL routes.

    Args:
        router: Router instance (creates new one if None)
        views: FrontendViews instance (creates new one if None)

    Returns:
        Configured router with frontend routes
    """
    if router is None:
        router = Router()

    if views is None:
        views = FrontendViews()

    # Homepage
    router.add_route("/", views.home_view, methods=["GET"])

    # Blog post routes
    router.add_route("/posts/", views.post_list_view, methods=["GET"])
    router.add_route("/posts/{slug}", views.post_detail_view, methods=["GET"])

    # Category routes
    router.add_route("/category/{slug}", views.category_view, methods=["GET"])

    # Page routes (catch-all for static pages)
    router.add_route("/{slug}", views.page_detail_view, methods=["GET"])

    return router
