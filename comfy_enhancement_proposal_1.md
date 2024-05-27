# CEP 1
# Comfy Enhancement Proposal 1 - A Modest Proposal to Pythonize ComfyUI Packaging

## Authors
Max Klein, PhD telamonian@hotmail.com

## Problem

The current state of the ComfyUI ecosystem, in particular with respect to the UX of installation and workspace management, is currently a bit of a mess. ComfyUI core and the various custom nodes are Python modules, but are not packaged as such. This causes friction, as users are unable to take advantage of the standard Python packaging tools. Instead, a user must handle the task of installing comfy core and extensions manually. To install an extension, a user must place the extension's files in the appropriate directory themselves, and then must separately install the Python dependencies of the extension. Worse, because there is no real standard for how the files of an extension should be laid out, the user is lucky if the extension author has decided to include a `requirements.txt` or other formal dependency specification. There are existing cases of (very popular) custom nodes that have instead chosen to describe their dependencies in plaintext buried in the midst of their READMEs.

There is an appetite now amongst the ComfyUI community to improve this mess by coming together and agreeing on a common standard for ComfyUI extension packaging.

## Proposed Enhancement

The proposed enhancement is twofold:

  1. New custom node extensions should be laid out as Python packages, following the current best practices of the Python community. At the top level there should be a `pyproject.toml` file that includes all of the metadata that is normally required for a Python project, in particular a formal listing of dependencies, ideally with at least some version constraints. The actual contents of the Python module (ie `__init__.py` and any other Python assets) should be collected in a single subdirectory.

  2. New custom node extensions should advertise their functionality, and core ComfyUI should consume said functionality, via Python's builtin `entry_points` mechanism. This will allow extensions to be installed using the same automated tooling as any other Python package (ie `pip install <node_path_or_url>`). This will also have the happy consequence (in conjunction with the `pyproject.toml` described above) of automatically handling any needed Python dependencies.

## What we are not Proposing

It does not necessarily follow from packaging custom node extensions as Python modules that said modules will be uploaded to PyPI (ie the primary open source Python repository) or be made available for download via the default `pip` commands. Given the unique needs of the ComfyUI ecosystem (in particular, the need to deal with many gigabytes worth of model files) there is some natural motivation for a comfy-flavored solution for distribution and related tooling. There are already some teams/projects pursuing the idea of a custom Comfy repo, such as Comfy Registry.

One of the goals of this proposal is to minimize the quantity of wheels that such Comfy native tooling will have to reinvent. The idea is that we will let the existing Python ecosystem handle the installation of the Comfy Python packages, while any Comfy specific tooling can be built on top. This will promote a healthy separation of concerns that will allow Comfy specific tooling to better focus on Comfy specific issues.

## Detailed Explanation

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

Implementing the proposed entry points pattern will not require any changes to `NODE_CLASS_MAPPINGS` or any of an extension's existing Python code. Instead, an entry point section will be added to the extension's metadata in the `pyproject.toml` file:

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

### The `pyproject.toml` file



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
