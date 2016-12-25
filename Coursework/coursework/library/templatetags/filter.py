from django import template

register = template.Library()

@register.filter(name='underscore')
def private(dic, key):
    return dic[key]