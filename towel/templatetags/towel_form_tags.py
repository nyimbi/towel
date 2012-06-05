from django import forms, template
from django.template.loader import render_to_string


register = template.Library()


def _type_class(item):
    if isinstance(item.field.widget, forms.CheckboxInput):
        return 'checkbox'
    elif isinstance(item.field.widget, forms.DateInput):
        return 'date'
    elif isinstance(item.field.widget, (forms.RadioSelect,
            forms.CheckboxSelectMultiple)):
        return 'list'
    return ''


@register.simple_tag
def form_items(form):
    """
    Render all form items::

        {% form_items form %}
    """
    return u''.join(render_to_string('_form_item.html', {
        'item': field,
        'is_checkbox': isinstance(field.field.widget, forms.CheckboxInput),
        'type_class': _type_class(field),
        }) for field in form)


@register.inclusion_tag('_form_item.html')
def form_item(item, additional_classes=None):
    """
    Helper for easy displaying of form items::

        {% for field in form %}
            {% form_item field %}
        {% endfor %}
    """

    return {
        'item': item,
        'additional_classes': additional_classes,
        'is_checkbox': isinstance(item.field.widget, forms.CheckboxInput),
        'type_class': _type_class(item),
        }


@register.inclusion_tag('_form_item_plain.html')
def form_item_plain(item, additional_classes=None):
    """
    Helper for easy displaying of form items without any additional
    tags (table cells or paragraphs) or labels::

        {% form_item_plain field %}
    """

    return {
        'item': item,
        'additional_classes': additional_classes,
        'is_checkbox': isinstance(item.field.widget, forms.CheckboxInput),
        'type_class': _type_class(item),
        }


@register.tag
def form_errors(parser, token):
    """
    Show all form and formset errors::

        {% form_errors form formset1 formset2 %}

    Silently ignores non-existant variables.
    """

    tokens = token.split_contents()

    return FormErrorsNode(*tokens[1:])


class FormErrorsNode(template.Node):
    def __init__(self, *items):
        self.items = [template.Variable(item) for item in items]

    def render(self, context):
        items = []
        for item in self.items:
            try:
                var = item.resolve(context)
                if isinstance(var, dict):
                    items.extend(var.values())
                elif isinstance(var, (list, tuple)):
                    items.extend(var)
                else:
                    items.append(var)
            except template.VariableDoesNotExist:
                # We do not care too much
                pass

        errors = False

        form_list = []
        formset_list = []

        for i in items:
            if isinstance(i, forms.BaseForm):
                form_list.append(i)
            else:
                formset_list.append(i)

            if (getattr(i, 'errors', None) or
                    getattr(i, 'non_field_errors', lambda: None)()):
                errors = True

        if not errors:
            return u''

        return render_to_string('_form_errors.html', {
            'forms': form_list,
            'formsets': formset_list,
            'errors': True,
            })


@register.simple_tag
def form_warnings(form):
    """
    Shows the validation warnings in a nicely formatted way, including the
    checkbox to ignore the warnings
    """

    if getattr(form, 'warnings', None):
        return render_to_string('_form_warnings.html', {
            'form': form,
            })

    return u''


@register.tag
def dynamic_formset(parser, token):
    """
    Implements formsets where subforms can be added using the
    ``towel_add_subform`` javascript method::

        {% dynamic_formset formset "activities" %}
            ... form code
        {% enddynamic_formset %}
    """

    tokens = token.split_contents()
    nodelist = parser.parse(('enddynamic_formset',))
    parser.delete_first_token()

    return DynamicFormsetNode(tokens[1], tokens[2], nodelist)


class DynamicFormsetNode(template.Node):
    def __init__(self, formset, slug, nodelist):
        self.formset = template.Variable(formset)
        self.slug = template.Variable(slug)
        self.nodelist = nodelist

    def render(self, context):
        formset = self.formset.resolve(context)
        slug = self.slug.resolve(context)

        result = []

        context.update({
            'empty': True,
            'form_id': '%s-empty' % slug,
            'form': formset.empty_form,
            })
        result.append(self.nodelist.render(context))
        context.pop()

        for idx, form in enumerate(formset.forms):
            context.update({
                'empty': False,
                'form_id': '%s-%s' % (slug, idx),
                'form': form,
                })
            result.append(self.nodelist.render(context))
            context.pop()

        return u''.join(result)
