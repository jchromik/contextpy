# ContextPy3

This is ContextPy3, which provides context-oriented programming
for both Python2 and Python3. ContextPy3 is based on ContextPy (version 1.1)
by Christian Schubert and Michael Perscheid. As ContextPy, ContextPy3 uses a
layer-in-class approach.

## Basic Interface

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

## Working with Multiple Layers

Let's assume we have the following layers and partial method definitions:

```python
my_layer = Layer("My Layer")
another_layer = Layer("Another Layer")

@base
def my_function():
    print("This is base.")

@around(my_layer)
def my_function():
    print("This is my layer.")
    proceed()

@around(another_layer)
def my_function():
    print("This is another layer.")
    proceed()
```

### Activating Multiple Layers

We can either activate multiple layers globally, locally, or mix both methods.

#### Globally

```python
global_activate_layer(my_layer)
global_activate_layer(another_layer)
my_function()
global_deactivate_layer(my_layer)
global_deactivate_layer(another_layer)
```

#### Locally

```python
with active_layer(my_layer):
    with active_layer(another_layer):
        my_function()
```

And, there is a short-hand for this:

```python
with active_layers(my_layer, another_layer):
    my_function()
```

#### Mixing Global and Local Activation

```python
global_activate_layer(my_layer)
with active_layer(another_layer)
    my_function() # my_layer and another_layer are active
global_deactivate_layer(my_layer)
```

### Scoped Deactivation

We can also deactivate layers in a specific scope:

```python
with active_layers(my_layer, another_layer):
    with inactive_layer(my_layer):
        my_function() # here only another_layer is active
```