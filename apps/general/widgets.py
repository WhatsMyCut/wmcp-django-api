from django.forms import widgets


class NullableCheckboxInput(widgets.CheckboxInput):
    def value_from_datadict(self, data, files, name):
        if name not in data:
            return None
        else:
            return super().value_from_datadict(data, files, name)

    def value_omitted_from_data(self, data, files, name):
        return None
