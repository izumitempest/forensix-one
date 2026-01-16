from django import template
from django.utils.safestring import mark_safe
import markdown

register = template.Library()


@register.filter(name="render_markdown")
def render_markdown(value):
    if not value:
        return ""
    # Use standard markdown with table support and other common extensions
    html = markdown.markdown(value, extensions=["tables", "fenced_code", "nl2br"])
    return mark_safe(html)
