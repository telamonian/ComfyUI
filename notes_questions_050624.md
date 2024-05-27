# Questions, week of 5/6/24

1. How can we “take a snapshot of the pip dependencies” before installing new custom nodes?
  - If we want to install a custom node, how can we do that safely such that we can roll back to the previous pip state if there are dependency conflicts during installation?

- 3 options
  - a) Don't. Delegate responsibility for python dependencies to python ecosystem by installing comfy and custom nodes one-by-one with `pip install`
    - pros:
      - less work
      - same approach taken by 95% of python projects
    - cons:
      - resulting install is not predictable, is dependent on the exact order in which nodes are installed
        - when you `pip install a b`, modern pip (>20.3) fully resolves the mutual dependencies of `a` and `b` and errors out on any conflicts
        - however when you do `pip install a && pip install b`, pip won't consider the dependency constraints of `a` when resolving the deps of `b`. Instead, it simply replaces any conflicting packages with the version preferred by `b`
      - no great way to snapshot and/or rollback
        - can still do some basic stuff with `pip freeze`

  - b) Enforce "core" dependencies/versions via nested environments
    - in top level venv-core, install core comfyui requirements
    - in each nested venv-node-x, install all requirements for some set of custom nodes
    - pros:
      - when in nested venv, pip refuses to install/uninstall anything in the top level venv
      - saves the disk space that otherwise would be required to install all comfy core deps in each and every venv representing a set of custom nodes
      - if we do the UX right, any added complexity will be completely transparent to the user
    - cons:
      - really complicated
      - due to ^^^^^^^^^^^, hard to set up well in the first place, likely prone to bugs
        - for example, in the case of an outright conflict between packages in top level/nested venv, pip will install a "shadow" package in the nested venv
    - refs:
      - https://stackoverflow.com/questions/61019081/is-it-possible-to-create-nested-virtual-environments-for-python
      
  - c) Gather and resolve all core and node dependencies into a single explicit requirements.txt file
    - proposed workflow:
      - using a tool like `uv pip compile`, resolve core deps into an explicit requirements file (ie every dep and subdep is listed along with exact version resolved)
      - repeat one-by-one with each custom node
      - combine all of the explicit req files, resolving any conflicts as so:
        - first, apply any special handling rules (eg for `torch+gpu`, `opencv-python`, etc)
        - if any of the nodes deps conflict with core deps, always prefer the core version
        - if any node deps conflict with each other, always prefer the newest version resolved
      - install resulting fully resolved requirement file
    - pros:
      - flexible enough to handle any special cases
      - ensures that dep versions specified by core comfy are always used, as per the comfyui maintainer's preference
      - given that a version conflict can be solved by a simple override, this should provide an easy and consistent UX
      - guaranteed to be at least not worse than the current approach in `comfy-cli` of relying on install-order-dependent clobbering of conflicts
    - cons:
      - is not formally "correct"
      - will probably (?) eventually result in a situation where it silently installs a non-functional conflicting mess
    - overall I think this is the most promising approach, but serious thought needs to be put into UX
      - warn noisily when a conflict is autoresolved
      - keep track in a record file somewhere of conflict resolution actions taken

- options b. and c. are not mutually exclusive
- for the purpose of snapshotting, however, option c by itself should be the simplest

2. What are entry points (EP) and how do they help here?

- roughly speaking, there are 3 kinds of EP in python
  - console script EP, that installs a script on $PATH that calls a specific python function
  - GUI script EP, same thing as console script EP but it launches in a separate window
  - plugin EP, a simple hook that advertises a plugin function that can be easily discovered/called in a "parent" package that consumes it

- example of entry point plugin hooks in a custom node's `pyproject.toml`:
```toml
[project.entry-points."comfyui.node_class_mappings"]
node_class_mappings = "comfyui_ipadapter_plus:NODE_CLASS_MAPPINGS"

[project.entry-points."comfyui.node_display_name_mappings"]
node_display_name_mappings = "comfyui_ipadapter_plus:NODE_DISPLAY_NAME_MAPPINGS"
```

- as an alternative to explicit specification of entry points, they could be automatically handled in custom nodes by a lightly customized `build-backend`, eg:
```toml
[build-system]
requires = ["comfyui_packaging"]
build-backend = "comfyui_packaging.build_api"
```
  - see [`jupyter-packaging`](https://github.com/jupyter/jupyter-packaging) for an existing example of something similar

- NB: in order to function as plugins, projects with plugin entry points must be installed as actual python packages

- example of entry point plugin consumption code in core comfyui's `node.py`:
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

- on the other hand, consuming entry point plugins does *not* require core comfyui to be installed as a python package

- refs:
  - https://setuptools.pypa.io/en/stable/userguide/entry_point.html
 
3. Can `uv` handle pyproject.toml dependencies

- short answer: yes, absolutely
- longer answser: the `uv pip compile` command appears to treat requirements listed in a `pyproject.toml` nearly the same as it does those in `requirement.txt` files. No `-r` flag is needed, instead you can just pass in the path to a dir containing a `pyproject.toml` file.


# code

- The venv path hacking magic that allows for correctly nested venvs. Run this with the top level venv activated:

```bash
base_site_packages="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
derived_site_packages="$(./path-to-sub-venv/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
echo "$base_site_packages" > "$derived_site_packages"/_base_packages.pth
```
