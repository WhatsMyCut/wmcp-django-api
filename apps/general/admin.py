from apps.appointments.forms import ImportForm


class ReadOnlyAfterCreatedMixin:
    read_only_after_created_fields = ()  # add your field names here

    def get_readonly_fields(self, request, obj=None):
        if not self.read_only_after_created_fields:
            raise Exception('You did not add any field name into `read_only_after_created_fields`.')
        if obj:  # editing an existing object
            return list(self.readonly_fields) + list(self.read_only_after_created_fields)
        return self.readonly_fields


class ShowCreatedModifiedMixin:
    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return list(fields) + ['created_at', 'modified_at']


class MatchingRulesMixin:
    matching_rules_title = None
    matching_rules_text = None
    change_list_template = 'general/admin/change_list_with_rules.html'
    add_form_template = 'general/admin/change_form_with_rules.html'
    import_admin_template = 'general/admin/import_with_rules.html'

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, extra_context=self._update_context(extra_context))

    def add_view(self, request, form_url='', extra_context=None):
        return super().changeform_view(request, None, form_url, extra_context=self._update_context(extra_context))

    def run_import(self, request, extra_context=None):
        return super().run_import(request, import_form=ImportForm, extra_context=self._update_context(extra_context))

    def _update_context(self, extra_context):
        context = {'rules': self.matching_rules_text,
                   'rules_title': self.matching_rules_title}
        context.update(extra_context or {})
        return context
