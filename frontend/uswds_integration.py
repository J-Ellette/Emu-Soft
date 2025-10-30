"""USWDS (United States Web Design System) integration for frontend, admin, and settings.

This module provides utilities for integrating USWDS components and styles
across the CMS user-facing pages, admin panel, and settings interfaces.

Reference: https://github.com/uswds/uswds
"""

from typing import Dict, List, Optional


class USWDSConfig:
    """Configuration for USWDS integration."""

    # USWDS version to use
    VERSION = "3.7.1"

    # CDN URLs for USWDS assets
    CSS_CDN = f"https://cdn.jsdelivr.net/npm/@uswds/uswds@{VERSION}/dist/css/uswds.min.css"
    JS_CDN = f"https://cdn.jsdelivr.net/npm/@uswds/uswds@{VERSION}/dist/js/uswds.min.js"

    # Theme colors (can be customized)
    THEME_COLORS = {
        "primary": "#005ea2",  # USWDS blue-60v
        "secondary": "#54278f",  # USWDS violet-70v
        "accent-warm": "#c05600",  # USWDS orange-50v
        "accent-cool": "#00bde3",  # USWDS cyan-30v
    }


class USWDSComponentRenderer:
    """Render USWDS components with proper markup and classes."""

    @staticmethod
    def render_banner() -> str:
        """Render the official government banner.

        Returns:
            HTML string for the government banner
        """
        return """
<section class="usa-banner" aria-label="Official website of the United States government">
  <div class="usa-accordion">
    <header class="usa-banner__header">
      <div class="usa-banner__inner">
        <div class="grid-col-auto">
          <img aria-hidden="true" class="usa-banner__header-flag" src="https://cdn.jsdelivr.net/npm/@uswds/uswds/dist/img/us_flag_small.png" alt="" />
        </div>
        <div class="grid-col-fill tablet:grid-col-auto" aria-hidden="true">
          <p class="usa-banner__header-text">
            An official website of the United States government
          </p>
          <p class="usa-banner__header-action">Here's how you know</p>
        </div>
        <button
          type="button"
          class="usa-accordion__button usa-banner__button"
          aria-expanded="false"
          aria-controls="gov-banner-default"
        >
          <span class="usa-banner__button-text">Here's how you know</span>
        </button>
      </div>
    </header>
    <div class="usa-banner__content usa-accordion__content" id="gov-banner-default" hidden="">
      <div class="grid-row grid-gap-lg">
        <div class="usa-banner__guidance tablet:grid-col-6">
          <img
            class="usa-banner__icon usa-media-block__img"
            src="https://cdn.jsdelivr.net/npm/@uswds/uswds/dist/img/icon-dot-gov.svg"
            role="img"
            alt=""
            aria-hidden="true"
          />
          <div class="usa-media-block__body">
            <p>
              <strong>Official websites use .gov</strong><br />A
              <strong>.gov</strong> website belongs to an official government
              organization in the United States.
            </p>
          </div>
        </div>
        <div class="usa-banner__guidance tablet:grid-col-6">
          <img
            class="usa-banner__icon usa-media-block__img"
            src="https://cdn.jsdelivr.net/npm/@uswds/uswds/dist/img/icon-https.svg"
            role="img"
            alt=""
            aria-hidden="true"
          />
          <div class="usa-media-block__body">
            <p>
              <strong>Secure .gov websites use HTTPS</strong><br />A
              <strong>lock</strong> (
              <span class="icon-lock"
                ><svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="52"
                  height="64"
                  viewBox="0 0 52 64"
                  class="usa-banner__lock-image"
                  role="img"
                  aria-labelledby="banner-lock-description"
                  focusable="false"
                >
                  <title id="banner-lock-description">Lock</title>
                  <desc>Locked padlock icon</desc>
                  <path
                    fill="#000000"
                    fill-rule="evenodd"
                    d="M26 0c10.493 0 19 8.507 19 19v9h3a4 4 0 0 1 4 4v28a4 4 0 0 1-4 4H4a4 4 0 0 1-4-4V32a4 4 0 0 1 4-4h3v-9C7 8.507 15.507 0 26 0zm0 8c-5.979 0-10.843 4.77-10.996 10.712L15 19v9h22v-9c0-6.075-4.925-11-11-11z"
                  />
                </svg> </span
              >) or <strong>https://</strong> means you've safely connected to
              the .gov website. Share sensitive information only on official,
              secure websites.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
        """.strip()

    @staticmethod
    def render_header(
        site_name: str,
        nav_items: Optional[List[Dict[str, str]]] = None,
        show_banner: bool = True,
    ) -> str:
        """Render USWDS header with navigation.

        Args:
            site_name: Name of the site
            nav_items: List of navigation items with 'text' and 'url' keys
            show_banner: Whether to show the government banner

        Returns:
            HTML string for the header
        """
        nav_items = nav_items or []
        banner_html = USWDSComponentRenderer.render_banner() if show_banner else ""

        nav_html = ""
        if nav_items:
            nav_html = '<nav class="usa-nav"><ul class="usa-nav__primary usa-accordion">'
            for item in nav_items:
                nav_html += f'<li class="usa-nav__primary-item"><a class="usa-nav__link" href="{item.get("url", "#")}"><span>{item.get("text", "")}</span></a></li>'
            nav_html += "</ul></nav>"

        return f"""
{banner_html}
<header class="usa-header usa-header--basic">
  <div class="usa-nav-container">
    <div class="usa-navbar">
      <div class="usa-logo">
        <em class="usa-logo__text">
          <a href="/" title="Home">{site_name}</a>
        </em>
      </div>
      <button type="button" class="usa-menu-btn">Menu</button>
    </div>
    {nav_html}
  </div>
</header>
        """.strip()

    @staticmethod
    def render_footer(site_name: str, year: Optional[int] = None) -> str:
        """Render USWDS footer.

        Args:
            site_name: Name of the site
            year: Copyright year (defaults to current year)

        Returns:
            HTML string for the footer
        """
        from datetime import datetime

        year = year or datetime.now().year

        return f"""
<footer class="usa-footer">
  <div class="usa-footer__secondary-section">
    <div class="grid-container">
      <div class="grid-row grid-gap">
        <div class="usa-footer__contact-links mobile-lg:grid-col-12">
          <div class="usa-footer__primary-content">
            <p>&copy; {year} {site_name}. All rights reserved.</p>
            <p>Powered by <a href="https://github.com/J-Ellette/CMS-Home-Grown">MyCMS</a> - A Homegrown Content Management System</p>
            <p>Design system: <a href="https://designsystem.digital.gov/">U.S. Web Design System</a></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</footer>
        """.strip()

    @staticmethod
    def render_alert(
        message: str, alert_type: str = "info", heading: Optional[str] = None
    ) -> str:
        """Render USWDS alert component.

        Args:
            message: Alert message
            alert_type: Type of alert (info, warning, error, success)
            heading: Optional alert heading

        Returns:
            HTML string for the alert
        """
        heading_html = f"<h4 class='usa-alert__heading'>{heading}</h4>" if heading else ""
        return f"""
<div class="usa-alert usa-alert--{alert_type}">
  <div class="usa-alert__body">
    {heading_html}
    <p class="usa-alert__text">{message}</p>
  </div>
</div>
        """.strip()

    @staticmethod
    def render_button(
        text: str,
        button_type: str = "default",
        size: Optional[str] = None,
        is_outline: bool = False,
    ) -> str:
        """Render USWDS button component.

        Args:
            text: Button text
            button_type: Type of button (default, secondary, accent-cool, accent-warm, base)
            size: Optional size (big)
            is_outline: Whether to render as outline button

        Returns:
            HTML string for the button
        """
        classes = ["usa-button"]
        if button_type != "default":
            classes.append(f"usa-button--{button_type}")
        if size:
            classes.append(f"usa-button--{size}")
        if is_outline:
            classes.append("usa-button--outline")

        return f'<button class="{" ".join(classes)}">{text}</button>'

    @staticmethod
    def render_card(
        heading: str,
        content: str,
        media_url: Optional[str] = None,
        footer: Optional[str] = None,
    ) -> str:
        """Render USWDS card component.

        Args:
            heading: Card heading
            content: Card content
            media_url: Optional media image URL
            footer: Optional footer content

        Returns:
            HTML string for the card
        """
        media_html = (
            f'<div class="usa-card__media"><img class="usa-card__img" src="{media_url}" alt="" /></div>'
            if media_url
            else ""
        )
        footer_html = f'<div class="usa-card__footer">{footer}</div>' if footer else ""

        return f"""
<div class="usa-card">
  {media_html}
  <div class="usa-card__container">
    <div class="usa-card__header">
      <h3 class="usa-card__heading">{heading}</h3>
    </div>
    <div class="usa-card__body">
      <p>{content}</p>
    </div>
    {footer_html}
  </div>
</div>
        """.strip()


class USWDSFormRenderer:
    """Render USWDS form components."""

    @staticmethod
    def render_text_input(
        name: str,
        label: str,
        value: str = "",
        required: bool = False,
        hint: Optional[str] = None,
        error: Optional[str] = None,
    ) -> str:
        """Render USWDS text input.

        Args:
            name: Input name attribute
            label: Input label
            value: Input value
            required: Whether input is required
            hint: Optional hint text
            error: Optional error message

        Returns:
            HTML string for the text input
        """
        required_attr = "required" if required else ""
        hint_html = f'<span class="usa-hint">{hint}</span>' if hint else ""
        error_html = (
            f'<span class="usa-error-message">{error}</span>' if error else ""
        )
        error_class = " usa-input--error" if error else ""

        return f"""
<div class="usa-form-group{' usa-form-group--error' if error else ''}">
  <label class="usa-label" for="{name}">{label}</label>
  {hint_html}
  {error_html}
  <input class="usa-input{error_class}" id="{name}" name="{name}" type="text" value="{value}" {required_attr} />
</div>
        """.strip()

    @staticmethod
    def render_textarea(
        name: str,
        label: str,
        value: str = "",
        required: bool = False,
        hint: Optional[str] = None,
    ) -> str:
        """Render USWDS textarea.

        Args:
            name: Textarea name attribute
            label: Textarea label
            value: Textarea value
            required: Whether textarea is required
            hint: Optional hint text

        Returns:
            HTML string for the textarea
        """
        required_attr = "required" if required else ""
        hint_html = f'<span class="usa-hint">{hint}</span>' if hint else ""

        return f"""
<div class="usa-form-group">
  <label class="usa-label" for="{name}">{label}</label>
  {hint_html}
  <textarea class="usa-textarea" id="{name}" name="{name}" {required_attr}>{value}</textarea>
</div>
        """.strip()

    @staticmethod
    def render_select(
        name: str, label: str, options: List[Dict[str, str]], selected: str = ""
    ) -> str:
        """Render USWDS select dropdown.

        Args:
            name: Select name attribute
            label: Select label
            options: List of options with 'value' and 'text' keys
            selected: Selected option value

        Returns:
            HTML string for the select
        """
        options_html = ""
        for option in options:
            value = option.get("value", "")
            text = option.get("text", "")
            selected_attr = "selected" if value == selected else ""
            options_html += f'<option value="{value}" {selected_attr}>{text}</option>'

        return f"""
<div class="usa-form-group">
  <label class="usa-label" for="{name}">{label}</label>
  <select class="usa-select" id="{name}" name="{name}">
    {options_html}
  </select>
</div>
        """.strip()


__all__ = [
    "USWDSConfig",
    "USWDSComponentRenderer",
    "USWDSFormRenderer",
]
