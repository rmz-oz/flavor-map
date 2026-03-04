"""Custom template tags and filters for FlavorMap."""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def star_icons(rating, total=5):
    """
    Usage: {{ review.rating|star_icons }}
    Renders filled and empty star icons.
    """
    rating = int(rating or 0)
    full  = '⭐' * rating
    empty = '☆' * (total - rating)
    return mark_safe(f'<span class="stars">{full}{empty}</span>')


@register.filter
def bs_stars(avg):
    """
    Render Bootstrap-icon stars for an average float rating.
    Usage: {{ restaurant.average_rating|bs_stars }}
    """
    avg   = float(avg or 0)
    full  = int(avg)
    half  = 1 if (avg - full) >= 0.5 else 0
    empty = 5 - full - half
    html  = ''
    html += '<i class="bi bi-star-fill text-warning"></i>' * full
    html += '<i class="bi bi-star-half text-warning"></i>' * half
    html += '<i class="bi bi-star text-secondary"></i>'    * empty
    return mark_safe(html)


@register.filter
def price_euros(price_str):
    """
    Render price range with colored euro signs.
    '€€' → one orange, one orange, one grey
    """
    mapping = {'€': 1, '€€': 2, '€€€': 3}
    count   = mapping.get(price_str, 0)
    active  = f'<span style="color:var(--fm-orange)">€</span>' * count
    inactive = '<span class="text-secondary opacity-50">€</span>' * (3 - count)
    return mark_safe(active + inactive)


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Return the current query string with overridden parameters.
    Usage: {% query_transform page=2 sort='rating' %}
    """
    request  = context.get('request')
    if not request:
        return ''
    params   = request.GET.copy()
    for key, val in kwargs.items():
        params[key] = val
    return params.urlencode()


@register.inclusion_tag('restaurants/partials/stars.html')
def render_stars(rating, size='normal'):
    """
    Inclusion tag — renders the stars partial.
    Usage: {% render_stars restaurant.average_rating %}
    """
    rating = float(rating or 0)
    full   = int(rating)
    half   = 1 if (rating - full) >= 0.5 else 0
    empty  = 5 - full - half
    return {
        'full':  range(full),
        'half':  range(half),
        'empty': range(empty),
        'avg':   rating,
        'size':  size,
    }
