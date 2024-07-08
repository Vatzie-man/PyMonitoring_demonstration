from django import template

register = template.Library()


@register.filter
def length_to_number(value):
    return f"{int(value)}%"


@register.filter
def percentage_bar(value):
    bar = (int(value) * (1 / 3))
    return int(bar) * "|"


@register.filter
def compressors(comps, n):
    comps = comps.split("|")
    return f"{comps[n]}"


@register.filter
def split_on_pipe_and_padding(s, n):
    s = s.split('|')
    return s[n]
