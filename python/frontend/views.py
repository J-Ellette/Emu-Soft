"""Public-facing views for pages and posts."""

from typing import Any, Optional
from framework.request import Request
from framework.response import Response, HTMLResponse
from templates.engine import TemplateEngine
from templates.loader import TemplateLoader
from database.connection import DatabaseConnection


class FrontendViews:
    """Handles public-facing views for the CMS.

    This class provides views for displaying pages, posts, and other
    public content using the template engine.
    """

    def __init__(
        self,
        template_engine: Optional[TemplateEngine] = None,
        db_connection: Optional[DatabaseConnection] = None,
    ) -> None:
        """Initialize the frontend views.

        Args:
            template_engine: Template engine for rendering views
            db_connection: Database connection for querying content
        """
        self.template_engine = template_engine or TemplateEngine(
            TemplateLoader(["frontend/templates"])
        )
        self.db_connection = db_connection

    async def home_view(self, request: Request) -> Response:
        """Render the homepage.

        Args:
            request: HTTP request object

        Returns:
            HTTP response with rendered homepage
        """
        context = {
            "title": "Welcome",
            "site_name": "MyCMS",
            "request": request,
        }

        # Get recent posts if available
        if self.db_connection:
            try:
                # Query recent published posts
                recent_posts: list[Any] = []  # Query recent published posts
                context["recent_posts"] = recent_posts
            except Exception:
                pass

        try:
            content = self.template_engine.render_template("home.html", context)
            return HTMLResponse(content)
        except FileNotFoundError:
            # Fallback if template doesn't exist
            return HTMLResponse(self._render_default_home(context))

    async def page_detail_view(self, request: Request, slug: str) -> Response:
        """Render a page by slug.

        Args:
            request: HTTP request object
            slug: Page slug

        Returns:
            HTTP response with rendered page
        """
        if not self.db_connection:
            return Response("Database not configured", status_code=500)

        try:
            # Query page by slug
            # In a real implementation, you'd use the ORM properly
            page_data = {
                "title": "Sample Page",
                "slug": slug,
                "content": "This is a sample page content.",
            }

            context = {
                "page": page_data,
                "title": page_data["title"],
                "site_name": "MyCMS",
                "request": request,
            }

            try:
                content = self.template_engine.render_template("page.html", context)
                return HTMLResponse(content)
            except FileNotFoundError:
                return HTMLResponse(self._render_default_page(context))

        except Exception:
            return Response(f"Page not found: {slug}", status_code=404)

    async def post_detail_view(self, request: Request, slug: str) -> Response:
        """Render a blog post by slug.

        Args:
            request: HTTP request object
            slug: Post slug

        Returns:
            HTTP response with rendered post
        """
        if not self.db_connection:
            return Response("Database not configured", status_code=500)

        try:
            # Query post by slug
            post_data = {
                "title": "Sample Post",
                "slug": slug,
                "content": "This is a sample post content.",
                "excerpt": "A brief excerpt of the post.",
                "published_at": "2024-01-01",
            }

            context = {
                "post": post_data,
                "title": post_data["title"],
                "site_name": "MyCMS",
                "request": request,
            }

            try:
                content = self.template_engine.render_template("post.html", context)
                return HTMLResponse(content)
            except FileNotFoundError:
                return HTMLResponse(self._render_default_post(context))

        except Exception:
            return Response(f"Post not found: {slug}", status_code=404)

    async def post_list_view(self, request: Request) -> Response:
        """Render a list of blog posts.

        Args:
            request: HTTP request object

        Returns:
            HTTP response with rendered post list
        """
        if not self.db_connection:
            return Response("Database not configured", status_code=500)

        try:
            # Query published posts
            posts: list[Any] = []  # Query all published posts

            context = {
                "posts": posts,
                "title": "Blog Posts",
                "site_name": "MyCMS",
                "request": request,
            }

            content = self.template_engine.render(
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{{ title }} - {{ site_name }}</title>
                </head>
                <body>
                    <h1>{{ title }}</h1>
                    {% if posts %}
                        <ul>
                        {% for post in posts %}
                            <li>
                                <h2>{{ post.title }}</h2>
                                <p>{{ post.excerpt }}</p>
                                <a href="/posts/{{ post.slug }}">Read more</a>
                            </li>
                        {% endfor %}
                        </ul>
                    {% else %}
                        <p>No posts available yet.</p>
                    {% endif %}
                </body>
                </html>
                """,
                context,
            )
            return HTMLResponse(content)

        except Exception:
            return Response("Error loading posts", status_code=500)

    async def category_view(self, request: Request, slug: str) -> Response:
        """Render posts in a category.

        Args:
            request: HTTP request object
            slug: Category slug

        Returns:
            HTTP response with posts in category
        """
        if not self.db_connection:
            return Response("Database not configured", status_code=500)

        try:
            # Query category and its posts
            category_data = {"name": "Sample Category", "slug": slug}
            posts: list[Any] = []  # Query posts in category

            context = {
                "category": category_data,
                "posts": posts,
                "title": category_data["name"],
                "site_name": "MyCMS",
                "request": request,
            }

            content = self.template_engine.render(
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{{ title }} - {{ site_name }}</title>
                </head>
                <body>
                    <h1>Category: {{ category.name }}</h1>
                    {% if posts %}
                        <ul>
                        {% for post in posts %}
                            <li>
                                <h2>{{ post.title }}</h2>
                                <a href="/posts/{{ post.slug }}">Read more</a>
                            </li>
                        {% endfor %}
                        </ul>
                    {% else %}
                        <p>No posts in this category yet.</p>
                    {% endif %}
                </body>
                </html>
                """,
                context,
            )
            return HTMLResponse(content)

        except Exception:
            return Response(f"Category not found: {slug}", status_code=404)

    def _render_default_home(self, context: dict) -> str:
        """Render default homepage when template is not found.

        Args:
            context: Template context

        Returns:
            HTML string
        """
        site_name = context.get("site_name", "MyCMS")
        title = context.get("title", "Home")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title} - {site_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px;
                       margin: 0 auto; padding: 20px; }}
                h1 {{ color: #333; }}
                a {{ color: #0066cc; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>Welcome to {site_name}</h1>
            <p>This is a homegrown content management system.</p>
            <ul>
                <li><a href="/posts/">View Blog Posts</a></li>
            </ul>
        </body>
        </html>
        """

    def _render_default_page(self, context: dict) -> str:
        """Render default page when template is not found.

        Args:
            context: Template context

        Returns:
            HTML string
        """
        page = context.get("page", {})
        page_title = page.get("title", "Page")
        page_content = page.get("content", "")
        site_name = context.get("site_name", "MyCMS")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{page_title} - {site_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px;
                       margin: 0 auto; padding: 20px; }}
                h1 {{ color: #333; }}
                .content {{ line-height: 1.6; }}
            </style>
        </head>
        <body>
            <h1>{page_title}</h1>
            <div class="content">{page_content}</div>
            <p><a href="/">Back to Home</a></p>
        </body>
        </html>
        """

    def _render_default_post(self, context: dict) -> str:
        """Render default post when template is not found.

        Args:
            context: Template context

        Returns:
            HTML string
        """
        post = context.get("post", {})
        post_title = post.get("title", "Post")
        post_content = post.get("content", "")
        post_published = post.get("published_at", "Unknown")
        site_name = context.get("site_name", "MyCMS")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{post_title} - {site_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px;
                       margin: 0 auto; padding: 20px; }}
                h1 {{ color: #333; }}
                .meta {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
                .content {{ line-height: 1.6; }}
            </style>
        </head>
        <body>
            <h1>{post_title}</h1>
            <div class="meta">Published: {post_published}</div>
            <div class="content">{post_content}</div>
            <p><a href="/posts/">Back to Posts</a></p>
        </body>
        </html>
        """
