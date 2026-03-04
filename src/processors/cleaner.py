from bs4 import BeautifulSoup, Tag


def _remove_all(soup: BeautifulSoup, selector: str) -> None:
    for el in soup.select(selector):
        el.decompose()


def clean_article_soup(soup: BeautifulSoup) -> None:
    """
    Remove boilerplate elements that are not part of the main content:
    - script, style
    - nav, footer, header
    - sidebars, related posts, comments, share buttons, keyword blocks, etc.
    """
    for tag in soup(["script", "style"]):
        tag.decompose()

    for tag_name in ("nav", "footer", "header"):
        for tag in soup.find_all(tag_name):
            tag.decompose()

    selectors = [
        ".sidebar",
        "[class*='sidebar']",
        "[id*='sidebar']",
        "[class*='related-post']",
        "[class*='related_posts']",
        "[id*='related-post']",
        "[id*='related_posts']",
        "[class*='comment']",
        "[id*='comment']",
        "[class*='share']",
        "[id*='share']",
        ".format-post_keyword",
        ".format-post_related",
        ".format-post_share",
        ".post-tags",
        ".post-navigation",
        ".breadcrumbs",
        ".lwptoc",
    ]

    for selector in selectors:
        _remove_all(soup, selector)


__all__ = ["clean_article_soup"]

