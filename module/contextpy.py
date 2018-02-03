# License (MIT License)
#
# Copyright (c) 2007-2008 Christian Schubert and Michael Perscheid
# michael.perscheid@hpi.uni-potsdam.de, http://www.hpi.uni-potsdam.de/swa/
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys
import threading

__all__ = ['Layer']
__all__ += ['activelayer', 'activelayers', 'inactivelayer', 'inactivelayers']
__all__ += ['proceed']
__all__ += ['before', 'after', 'around', 'base']
__all__ += ['global_activate_layer', 'global_deactivate_layer']

__version__ = "1.1"

# tuple with layers that are always active
_BASELAYERS = (None,)

class TLS(threading.local):
    def __init__(self):
        super().__init__()
        self.context = None
        self.activelayers = ()

_TLS = TLS() # pylint: disable=invalid-name

class Layer(object):
    def __init__(self, name=None):
        self._name = name or hex(id(self))

    def __str__(self):
        return "<layer %s>" % (self._name)

    def __repr__(self):
        args = []
        if self._name != hex(id(self)):
            args.append('name="%s"' % self._name)
        return "layer(%s)" % (", ".join(args))

class _LayerManager(object):
    def __init__(self, layers):
        self._layers = layers
        self._old_layers = ()

    def _get_active_layers(self):
        return self._old_layers

    def __enter__(self):
        self._old_layers = _TLS.activelayers
        _TLS.activelayers = tuple(self._get_active_layers())

    def __exit__(self, exc_type, exc_value, exc_tb):
        _TLS.activelayers = self._old_layers

class _LayerActivationManager(_LayerManager):
    def _get_active_layers(self):
        return [layer for layer in self._old_layers if layer not in self._layers] + self._layers

class _LayerDeactivationManager(_LayerManager):
    def _get_active_layers(self):
        return [layer for layer in self._old_layers if layer not in self._layers]

def activelayer(layer):
    return _LayerActivationManager([layer])

def inactivelayer(layer):
    return _LayerDeactivationManager([layer])

def activelayers(*layers):
    return _LayerActivationManager(list(layers))

def inactivelayers(*layers):
    return _LayerDeactivationManager(list(layers))

class _advice(object):
    def __init__(self, func, successor):
        if func:
            self._func = func
        else:
            self._func = None
        self._successor = successor

    def _invoke(self, context, args, kwargs):
        if (context[0] is None) and (context[1] is None):
            # Normal Python function no binding needed
            return self._func(*args, **kwargs)
        # Kind of instance method, class or static mehtod (binding needed)
        return self._func.__get__(context[0], context[1])(*args, **kwargs)

    def __call__(self, context, args, kwargs):
        raise NotImplementedError

    @classmethod
    def createchain(cls, methods):
        if not methods:
            return _stop(None, None)
        method, when = methods[0]
        return when(method, cls.createchain(methods[1:]))

class _before(_advice):
    def __call__(self, context, args, kwargs):
        self._invoke(context, args, kwargs)
        return self._successor(context, args, kwargs)

class _around(_advice):
    def __call__(self, context, args, kwargs):
        backup = _TLS.context
        _TLS.context = context
        context[2] = self._successor
        result = self._invoke(context, args, kwargs)
        _TLS.context = backup
        return result

class _after(_advice):
    def __call__(self, context, args, kwargs):
        result = self._successor(context, args, kwargs)
        kwargs_with_result = dict(__result__=result, **kwargs)
        return self._invoke(context, args, kwargs_with_result)

class _stop(_advice):
    def __call__(self, context, args, kwargs):
        raise Exception(
            "called proceed() in innermost function, this probably means that"
            "you don't have a base method (`around` advice in None layer) or"
            "the base method itself calls proceed()")

def proceed(*args, **kwargs):
    context = _TLS.context
    return context[2](context, args, kwargs)

def _true(*_):
    return True

class _layeredmethodinvocationproxy(object):
    __slots__ = ("_inst", "_cls", "_descriptor")

    def __init__(self, descriptor, inst, cls):
        self._inst = inst
        self._cls = cls
        self._descriptor = descriptor

    def __call__(self, *args, **kwargs):
        layers = _BASELAYERS + _TLS.activelayers
        advice = (
            self._descriptor.cache().get(layers)
            or self._descriptor.cache_methods(layers))

        context = [self._inst, self._cls, None]
        result = advice(context, args, kwargs)
        return result

    def get_methods(self):
        return self._descriptor.methods

    def set_methods(self, methods):
        self._descriptor.methods = methods

    def get_name(self):
        return self._descriptor.methods[-1][1].__name__

    def register_method(self, method, when=_around, layer_=None, guard=_true):
        self._descriptor.register_method(method, when, layer_, guard)

    def unregister_method(self, method, layer_=None):
        self._descriptor.unregister_method(method, layer_)

    methods = property(get_methods, set_methods)
    __name__ = property(get_name)

class _layeredmethoddescriptor(object):
    def __init__(self, methods):
        self._methods = methods
        self._cache = {}

    def _clear_cache(self):
        for key in self._cache:
            self._cache.pop(key, None)

    def cache(self):
        return self._cache

    def cache_methods(self, layers):
        layers = list(reversed(layers))

        # For each active layer, get all methods and the when advice class related to this layer
        methods = sum([
            list(reversed(
                [(lmwgm[1], lmwgm[2])
                 for lmwgm in self._methods
                 if lmwgm[0] is currentlayer and lmwgm[3](activelayers)]
            )) for currentlayer in layers], [])

        self._cache[activelayers] = result = _advice.createchain(methods)
        return result

    def set_methods(self, methods):
        self._methods[:] = methods
        self._clear_cache()

    def get_methods(self):
        return list(self._methods)

    def register_method(self, method, when=_around, layer_=None, guard=_true, method_name=""):
        if method_name == "":
            method_name = method.__name__
        if hasattr(when, "when"):
            when = when.when

        assert isinstance(layer_, (Layer, type(None)))
        assert issubclass(when, _advice)

        self.methods = self.methods + [
            (layer_, method, when, guard, method_name)]

    def unregister_method(self, method, layer_=None):
        self.methods = [lmwgm
                        for lmwgm in self.methods
                        if lmwgm[1] is not method or lmwgm[0] is not layer_]

    methods = property(get_methods, set_methods)

    def __get__(self, inst, cls=None):
        return _layeredmethodinvocationproxy(self, inst, cls)

    # Used only for functions (no binding or invocation proxy needed)
    def __call__(self, *args, **kwargs):
        layers = _BASELAYERS + _TLS.activelayers
        advice = self._cache.get(layers) or self.cache_methods(layers)

        # 2x None to identify: do not bound this function
        context = [None, None, None]
        result = advice(context, args, kwargs)
        return result

def createlayeredmethod(base_method, partial_method):
    if base_method:
        return _layeredmethoddescriptor([(None, base_method, _around, _true)] + partial_method)
    return _layeredmethoddescriptor(partial_method)

# Needed for a hack to get the name of the class/static method object
class _dummyClass:
    pass

def get_method_name(method):
    if isinstance(method, (classmethod, staticmethod)):
        # Bound the method to a dummy class to retrieve the original name
        return method.__get__(None, _dummyClass).__name__
    return method.__name__

def __common(layer_, guard, when):
    assert isinstance(layer_, (Layer, type(None))), \
        "layer_ argument must be a layer instance or None"
    assert callable(guard), "guard must be callable"
    assert issubclass(when, _advice)

    frame = sys._getframe(2).f_locals # pylint: disable=protected-access

    def decorator(method):
        method_name = get_method_name(method)
        current_method = frame.get(method_name)
        if issubclass(type(current_method), _layeredmethoddescriptor):
            #Append the new method
            current_method.register_method(method, when, layer_, guard, method_name)
        else:
            current_method = createlayeredmethod(current_method,
                                                 [(layer_, method, when, guard, method_name)])
        return current_method

    return decorator

def before(layer_=None, guard=_true):
    return __common(layer_, guard, _before)
def around(layer_=None, guard=_true):
    return __common(layer_, guard, _around)
def after(layer_=None, guard=_true):
    return __common(layer_, guard, _after)

def base(method):
    # look for the current entry in the __dict__ (class or module)
    frame = sys._getframe(1).f_locals # pylint: disable=protected-access
    method_name = get_method_name(method)
    current_method = frame.get(method_name)
    if issubclass(type(current_method), _layeredmethoddescriptor):
        # add the first entry of the layered method with the base entry
        current_method.methods = [(None, method, _around, _true)] + current_method.methods
        return current_method
    return method

before.when = _before
around.when = _around
after.when = _after

def global_activate_layer(layer):
    global _BASELAYERS
    if layer in _BASELAYERS:
        raise ValueError("layer is already active")
    _BASELAYERS += (layer,)
    return _BASELAYERS

def global_deactivate_layer(layer):
    global _BASELAYERS
    old_layers = list(_BASELAYERS)
    if layer not in old_layers:
        raise ValueError("layer is not active")
    i = old_layers.index(layer)
    _BASELAYERS = tuple(old_layers[:i] + old_layers[i+1:])
    return _BASELAYERS
