import graphene

from apps.dynamic_settings.utils import DynamicSettingsUtils
from apps.general.graphql import construct_dynamic_graphene_object, python_type_to_graphql_type


def _merge_settings():
    # syntax z = {**x, **y} is supported only from versions Python 3.5 and higher
    d = DynamicSettingsUtils.get_public_dynamic_settings().copy()
    d.update(DynamicSettingsUtils.get_public_settings())
    return d


DynamicSettingsType = construct_dynamic_graphene_object(
    'DynamicSettingsType', {key: python_type_to_graphql_type(DynamicSettingsUtils.get_settings_type(key))()
                            for key in _merge_settings().keys()}
)


class Query(graphene.AbstractType):
    site_settings = graphene.Field(DynamicSettingsType)

    def resolve_site_settings(self, args, context, info):
        keys_dict = {}
        for c_key, c_value in DynamicSettingsUtils.get_public_dynamic_settings().items():
            keys_dict[c_key.lower().capitalize()] = c_value
        for c_key, c_value in DynamicSettingsUtils.get_public_settings().items():
            keys_dict[c_key.lower().capitalize()] = c_value
        return DynamicSettingsType(**keys_dict)
