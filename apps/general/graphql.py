import datetime
from collections import OrderedDict, Iterable
from decimal import Decimal

import graphene
import graphene_django.views
from graphene.types import String, Int, Float, Boolean
from graphene.types import Union
from graphene.types.datetime import DateTime, Time, Scalar
from graphene.types.enum import EnumTypeMeta, eq_enum, PyEnum, Enum
from graphene.types.inputobjecttype import InputObjectTypeMeta
from graphene.types.mutation import MutationMeta
from graphene.types.objecttype import ObjectTypeMeta
from graphene.types.options import Options
from graphene.types.union import UnionMeta
from graphene.utils.is_base_type import is_base_type
from graphene.utils.str_converters import to_camel_case
from graphene.utils.trim_docstring import trim_docstring
from graphql.error import GraphQLError
from graphql.error import format_error as format_graphql_error
from graphql.language.ast import StringValue

from apps.general.exceptions import AppException, InternalErrorException, ErrorDto
from apps.general.metautils import mix_meta_factory


class MixableEnum(graphene.Enum, metaclass=mix_meta_factory(EnumTypeMeta)):
    pass


class MixableMutation(graphene.Mutation, metaclass=mix_meta_factory(MutationMeta)):
    @staticmethod
    def mutate(root, args, context, info):
        return NotImplemented


class MixableInputObjectType(graphene.InputObjectType, metaclass=mix_meta_factory(InputObjectTypeMeta)):
    pass


class MixableObjectType(graphene.ObjectType, metaclass=mix_meta_factory(ObjectTypeMeta)):
    pass


class DeferredAttr:
    def __init__(self, getter):
        self.getter = getter

    def __call__(self, *args, **kwargs):
        return self.getter()


class DeferredUnionMeta(UnionMeta):
    """Metaclass for creation of union types with a deferred types initialization.
    """
    def __new__(cls, name, bases, attrs):
        # Also ensure initialization is only performed for subclasses of
        # DeferredUnion
        if not is_base_type(bases, DeferredUnionMeta):
            return type.__new__(cls, name, bases, attrs)

        meta = attrs.pop('Meta', None)
        if meta is None:
            raise AssertionError('Meta is required for union type.')

        if hasattr(meta, 'types') and isinstance(meta.types, DeferredAttr):
            class DeferredOptions(Options):
                _types = meta.types

                @property
                def types(self):
                    return self._types()
            delattr(meta, 'types')
            options = DeferredOptions(meta, name=name, description=trim_docstring(attrs.get('__doc__')))
        else:
            options = Options(
                meta,
                name=name,
                description=trim_docstring(attrs.get('__doc__')),
                types=(),
            )

            assert (
                isinstance(options.types, (list, tuple)) and
                len(options.types) > 0
            ), 'Must provide types for Union {}.'.format(options.name)

        return type.__new__(cls, name, bases, dict(attrs, _meta=options))


class DeferredUnion(Union, metaclass=DeferredUnionMeta):
    pass


class DeferredEnumMeta(EnumTypeMeta):
    """Metaclass for creation of enum types with a deferred values initialization.
    """
    def __new__(cls, name, bases, attrs):
        # Also ensure initialization is only performed for subclasses of Model
        # (excluding Model class itself).
        if not is_base_type(bases, DeferredEnumMeta):
            return type.__new__(cls, name, bases, attrs)

        meta = attrs.pop('Meta', None)
        if meta is None:
            raise AssertionError('Meta is required for deferred enum type.')

        if not hasattr(meta, 'values') or not isinstance(meta.values, DeferredAttr):
            raise AssertionError('Incorrect `Meta.values` in deferred enum type.')

        class DeferredOptions(Options):
            _values = meta.values

            @property
            def enum(self):
                attrs.update(self._values())
                return PyEnum(cls.__name__, attrs)

        delattr(meta, 'values')
        attrs['__eq__'] = eq_enum
        options = DeferredOptions(
            meta,
            name=name,
            description=trim_docstring(attrs.get('__doc__'))
        )

        new_attrs = OrderedDict(attrs, _meta=options, **options.enum.__members__)
        return type.__new__(cls, name, bases, new_attrs)


class DeferredEnum(Enum, metaclass=DeferredEnumMeta):
    pass


def log_error(msg, exc_info=None):
    from apps.general.loggers import django_logger

    django_logger.error(msg, exc_info=exc_info)


def format_error(error):
    if hasattr(error, 'original_error'):
        err = error.original_error
        formatted_error = {}
        if isinstance(err, AppException):
            if isinstance(err, InternalErrorException):
                log_error(err.detail, exc_info=(err.__class__, err, err.stack))
            formatted_error['message'] = err.detail
            formatted_error['code'] = err.code
        else:
            log_error('Exception during GraphQL method execution.', exc_info=(err.__class__, err, err.stack))
            formatted_error['message'] = 'Internal error.'
            formatted_error['code'] = InternalErrorException.code

        if hasattr(err, 'errors') and err.errors is not None:
            formatted_error['errors'] = [{'key': to_camel_case(x.key), 'message': x.message} for x in err.errors]
        if error.locations is not None:
            formatted_error['locations'] = [
                {'line': loc.line, 'column': loc.column}
                for loc in error.locations
            ]
        return formatted_error
    if isinstance(error, GraphQLError):
        return format_graphql_error(error)
    return {'message': str(error)}


class GraphQLView(graphene_django.views.GraphQLView):
    @staticmethod
    def format_error(error):
        return format_error(error)

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() in ('get', 'post'):
            data = self.parse_body(request)
            # Disable batch mode if received an unsuitable request.
            if isinstance(data, dict) or not isinstance(data, Iterable):
                self.batch = False
        return super().dispatch(request, *args, **kwargs)

    def parse_body(self, request):
        # To not parse twice.
        if not hasattr(request, '_parsed_data'):
            data = super().parse_body(request)
            setattr(request, '_parsed_data', data)
        return getattr(request, '_parsed_data')


def construct_dynamic_graphene_object(obj_name, fields_dict, force_camel_case=True):
    """ Creates an instance of graphene.ObjectType with dynamically-specified fields
        I.e.,

        construct_dynamic_graphene_object('SomeDynamicType', {'field1': graphene.String(), 'field2': graphene.Int()}) is like

        class SomeDynamicType(graphene.ObjectType):
            field1 = graphene.String()
            field2 = graphene.Int()
    """
    new_dict = {}
    for key, value in fields_dict.items():
        key_ = key if not force_camel_case else key.lower().capitalize()
        new_dict[key_] = value
    return type(obj_name, (graphene.ObjectType,), new_dict)


def python_type_to_graphql_type(python_type):
    # Only basic types are supported at the moment. Feel free to add support for them.
    types_mapping = {
        String: (str, Decimal),
        Int: int,
        Float: float,
        Boolean: bool,
        DateTime: datetime.datetime,
        Time: datetime.time,
    }
    for type_key, type_values in types_mapping.items():
        if python_type == type_values or (isinstance(type_values, (list, tuple)) and python_type in type_values):
            return type_key
    raise InternalErrorException(
        detail='Dynamic settings error.',
        errors=[ErrorDto(key=str(python_type), message='Unsupported type.')]
    )


class Date(Scalar):
    """ A date type, yyyy-mm-dd """

    _format = '%Y-%m-%d'

    @staticmethod
    def serialize(date):
        assert isinstance(date, datetime.date), (
            'Received not compatible date "{}"'.format(repr(date))
        )
        return date.strftime(Date._format)

    @classmethod
    def parse_literal(cls, node):
        if isinstance(node, StringValue):
            return cls.parse_value(node.value)

    @staticmethod
    def parse_value(value):
        return datetime.datetime.strptime(value, Date._format).date()
