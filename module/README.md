# ContextPy3

This is ContextPy3, which provides context-oriented programming
for both Python2 and Python3. ContextPy3 is based on ContextPy (version 1.1)
by Christian Schubert and Michael Perscheid. As ContextPy, ContextPy3 uses a
layer-in-class approach.

## Interface

### Creating Layers

```python
my_layer = Layer("My Layer")
```

### Layering Methods

```python
# This is the base function, called when no layers are active.
@base
def my_function():
    print("Hello World")

# This is a partial function for my_layer, called when my_layer is active.
@around(my_layer)
def my_function():
    print("I am a layered function.")
    # Calling proceed() brings us one step down in the layer stack.
    # Here we are calling the @base version of my_function.
    proceed()
```

### Activating Layers

Now you know how to define layers and adapt methods. But how to actually
activate layers? There are two layer stacks: A system-global stack affecting all
threads, and a thread-local stack.

#### System-global layer activation

```python
global_activate_layer(my_layer)
my_function()
global_deactivate_layer(my_layer)
```

#### Thread-local layer activation

```python
with active_layer(my_layer):
  my_function()
```