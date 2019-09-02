import inspect


def mix(mixin_class):
    """Helper function to add mixins for class inside which it is called.
    :param mixin_class: mixin class to add to _mixins property of current class.
    """
    frm = inspect.stack()[1][0]
    if '_mixins' not in frm.f_locals:
        frm.f_locals['_mixins'] = []
    frm.f_locals['_mixins'].append(mixin_class)


def mix_meta_factory(base_meta):
    class MixMeta(base_meta):
        """
        Metaclass which adds public attributes of classes listed in _mixins
        directly to the current created class.
        """
        def __new__(cls, name, bases, attrs):
            if '_mixins' in attrs:
                for mixin in attrs['_mixins']:
                    mixed_attrs = {k: v for k, v in mixin.__dict__.items() if not k.startswith('_') and k not in attrs}
                    attrs.update(mixed_attrs)
                del attrs['_mixins']
            return base_meta.__new__(cls, name, bases, attrs)
    return MixMeta
