# CEP 1
# Comfy enhancement proposal 1 - Simplifying and improving ComfyUI installations

## Authors
- Max Klein, PhD - telamonian@hotmail.com
- Robin Huang

## Problem

Currently installing ComfyUI core and a set of custom node extensions is a difficult, inconsistent process. There are many efforts under way right now in the Comfy ecosystem to create tools to ease this installation process. However, these tools are currently the position of having to reinvent the wheels of software packaging and management. They have to provide their own custom implementations of various difficult features, such as caching and cache management.

Instead, we should take advantage of the fact that ComfyUI core and all of the extensions are Python packages. If we could build on top of the extensive zoo of existing, well-featured Python installer tools, it will greatly simplify the creation of new Comfy installer tools. We can encourage a strong separation of concerns by allowing Python tools to handle installation of Python packages, freeing the developers of Comfy-specific installer tools to focus on Comfy-specific problems.

However, custom node extensions currently are not structured as proper Python packages, nor do they generally include the appropriate metadata in an appropriate format. This causes friction and errors when trying to use Python tools with the existing Comfy assets. By coming together as a community and deciding upon a standard for how to package custom node extensions, we can lay the groundwork for a fertile ecosystem of Comfy installer tools.

This proposal lays out a framework by which *new* Comfy extensions should be laid out, and what metadata they should contain. By following the standards laid out here, we will ensure that every new extension is also a proper Python package. Hand-in-hand with that, we also propose a new mechanism by which core ComfyUI will load extensions. This mechanism will be based on Python's builtin `entry_point`. The current pattern requires extensions to be manually placed within a subdirectory of ComfyUI core. Instead, `entry_point` based extensions can be installed as standard Python packages while still allowing ComfyUI core to load their assets. This new mechanism will initially coexist alongside the old extension loading mechanism, ensuring that both old-style and new-style will continue to work. Over time, a pathway by which to migrate old-style extensions to the new-style pattern will be created, and eventually the old-style will be deprecated alongside a major version of ComfyUI core.

## Proposed Enhancement

The proposed enhancement is threefold:
 
  1. At the top level of every new custom node extension there should be a `pyproject.toml` file. This should include all of the metadata that is normally required for a Python project, in particular a formal listing of dependencies, ideally with at least some version constraints.

  2. New custom node extensions should be laid out as Python packages, following the current best practices of the Python community. Beside the top level `pyproject.toml`, the actual contents of the Python module (ie `__init__.py` and any other Python assets) should be collected in a single subdirectory.

  3. New custom node extensions should advertise their functionality, and core ComfyUI should consume said functionality, via Python's builtin `entry_point` mechanism. This will allow extensions to be installed using the same automated tooling as any other Python package (ie `pip install <node_path_or_url>`). This will also have the happy consequence (in conjunction with the `pyproject.toml` described above) of automatically handling any needed Python dependencies.

## What we are not Proposing

It does not necessarily follow from packaging custom node extensions as Python modules that said modules will be uploaded to PyPI (ie the primary open source Python repository) or be made available for download via the default `pip` commands. Given the unique needs of the ComfyUI ecosystem (in particular, the need to deal with many gigabytes worth of model files) there is some natural motivation for a comfy-flavored solution for distribution and related tooling. The proposal authors are working on one such tool, [Comfy Registry](https://www.comfyregistry.org/), a custom repo for ComfyUI extensions and assets.

One of the goals of this proposal is to minimize the quantity of wheels that such Comfy native tooling will have to reinvent. The idea is that we will let the existing Python ecosystem handle the installation of the Comfy Python packages, while any Comfy specific tooling can be built on top. This will promote a healthy separation of concerns that will allow Comfy specific tooling to better focus on Comfy specific issues.

## Detailed Explanation

### The `pyproject.toml` file

Similar to any generic Python project, a ComfyUI extension's `pyproject.toml` file will include a `[project]` section:

```toml
[project]
name = "myext" # Unique identifier for your node. Cannot be changed later.
description = "my very good ComfyUI extension"
version = "1.0.0" # SemVer compatible
requires-python = ">= 3.9"
dependencies  = []
license = {file = "LICENSE"}

[project.urls]
Repository = "https://github.com/foo/myext.git"
```

In addition, `pyproject.toml` can hold arbitrary metadata under the `[tool]` table (see [here](https://peps.python.org/pep-0518/#tool-table) for details). This provides us an opportunity to start encouraging (or perhaps requiring) ComfyUI extension devs to start recording more comfy specific metadata in a more formalized way. In particular, this is an opportunity to start including formal metadata describing exactly the set of models required for the functionality of a custom node. [Comfy Registry](https://www.comfyregistry.org/) (with which the proposal authors are involved) has put forward a possible format for a `[tool.comfy]` table of metadata in `pyproject.toml`:

```toml
[tool.comfy]
publisherid = "" # Must match the id registered on Comfy Registry Website
displayname = "" # Display Name of the custom node
icon = "images/icon.png"
comfy-version = ">= 1.2" # Add when comfy is versioned
os = ["all"] # windows, mac, linux
models = [
  {name = "foo", path = "checkpoints", url = "https://aloofback.co/foo", priority = "required"},
  {name = "bar", path = "checkpoints", url = "https://aloofback.co/bar", priority = "default"},
  {name = "baz", path = "checkpoints", url = "https://aloofback.co/baz", priority = "supplementary"},
]
```

### Extension File Layout

Currently, ComfyUI extensions are laid out with an `__init__.py` file at top level:

```
extension_root_directory
├── __init__.py
├── ...
├── module.py
└── subpkg/
    ├── __init__.py
    ├── ...
    └── module1.py
```

Instead, we propose a layout more in line with the standard Python package layout in which a project metadata file (ie `pyproject.toml`) is at top level and the actual Python code is stored one or more levels below. There are 2 commonly used layouts. The [flat-layout](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html#flat-layout), in which the extension's module directory is at top level next to the pyproject file:

```
extension_root_directory
├── pyproject.toml
├── ...
└── myext/
    ├── __init__.py
    ├── ...
    ├── module.py
    └── subpkg/
        ├── __init__.py
        ├── ...
        └── module1.py
```

There is also the [src-layout](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html#src-layout), in which the extension's module directory is one extra level down underneath a `src` directory. Although slightly more convoluted, this layout has the advantage of allowing the structure of the source directory and any test directories to be symmetrical:

```
extension_root_directory
├── pyproject.toml
├── ...
├── src/
|   └── myext/
|       ├── __init__.py
|       ├── ...
|       ├── module.py
|       └── subpkg/
|           ├── __init__.py
|           ├── ...
|           └── module1.py
└── test/
    └── myext/
        └── ...
```

Any new ComfyUI extension should use one of the above two layouts.

### Entry Points

Broadly speaking, an entry point in Python is a builtin mechanism to allow an installed Python package to expose specific functionality to other programs. For example, a 3rd party extension can advertise a plugin function that can then be consumed by some core program. See the [setuptool docs](https://setuptools.pypa.io/en/latest/userguide/entry_point.html#advertising-behavior) for more details.

#### Extension Side Advertisement Mechanism

The current pattern for the code of a ComfyUI extension is that it should include a top-level `__init__.py` that includes a `NODE_CLASS_MAPPINGS` dict of {node_name: node_class} pairs. There can also be an optional `NODE_DISPLAY_NAME_MAPPINGS` dict of {node_name: display_name} pairs.

Implementing the proposed entry points pattern will not require any changes to `NODE_CLASS_MAPPINGS` or any of an extension's existing Python code. Instead, one or more entry point sections will be added to the extension's `pyproject.toml` file:

```toml
[project.entry-points."comfyui.node_class_mappings"]
node_class_mappings = "myext:NODE_CLASS_MAPPINGS"

[project.entry-points."comfyui.node_display_name_mappings"]
node_display_name_mappings = "myext:NODE_DISPLAY_NAME_MAPPINGS"
```

#### Core Side Consumption Mechanism

The code for consuming entry points is very simple. Below is an example of a full functional implementation of entry point loading taken from an in-progress PR for ComfyUI core:

```python
def load_custom_nodes_entry_points():
    base_node_names = set(NODE_CLASS_MAPPINGS.keys())

    for ep in entry_points(group="comfyui.node_class_mappings"):
        class_mapping = ep.load()
        for name in class_mapping:
            if name not in base_node_names:
                NODE_CLASS_MAPPINGS[name] = class_mapping[name]

    for ep in entry_points(group="comfyui.node_display_name_mappings"):
        display_name_mapping = ep.load()
        NODE_DISPLAY_NAME_MAPPINGS.update(display_name_mapping)
```

The above code was designed and tested to have complete parity with the existing extension loader code in ComfyUI core. One issue with the current behavior is that extension nodes whose names conflict with core nodes are silently dropped, while on the other hand extension nodes are free to clobber each other. It may make sense to revisit this node name conflict behavior as part of implementing this proposal.

## Pros and Cons

### Migration Pathway

This new extension pattern is compatible with, and can coexist beside, the old way of structuring and installing Comfy extensions. If/when this proposal is accepted, the old way will be formally deprecated and, eventually, removed in conjunction with a future major version release of core ComfyUI. At that point old extensions will continue to work with the old versions of ComfyUI, but  will have to be updated to the new pattern in order to work with the latest ComfyUI. This will naturally cause some amount of consternation and inconvenience amongst the community of extension maintainers.

The authors have previous experience working on the extension system of JupyterLab, another large OSS project. Taking lessons learned, it is crucial that we ensure as smooth a migration process as possible for 3rd party extension authors, in order to maintain their cooperation and enthusiasm for the ComfyUI project as a whole. To that end, there are 3 things (at least) that we need to do:

1. Provide extensive documentation on the changes and a simple tutorial showing how the migration is performed.
2. Make examples of some popular extensions.
    - At the start of the migration process the core Comfy team should get the buy-in and approval of the maintainers of 5 or 6 of the most visible/popular 3rd party projects. The core team should help contribute PRs to ensure that these projects can be used by the rest of the community as examples of the "right way" to perform the migration.
3. Communicate about the migration as much as possible, and as frequently as reasonable.
    - At the onset of the migration the core team should perform as much outreach as they can in order to ensure that all of the relevant parties are at least aware of what is happening. Blog posts are helpful, and short presentations should be made at any relevant conferences.

## Interested Contributors

- One of the authors (Max Klein, @telamonian on github) has already contributed a PR with a basic prototype of the `entry_point` mechanism to ComfyUI core, and is interested in further developing any related code.
- Robin Huang and the rest of the Comfy Registry team would like to support the creation of a formal `pyproject.toml` standard.
