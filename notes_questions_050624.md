# Questions, week of 5/6/24

1. How can we “take a snapshot of the pip dependencies” before installing new custom nodes?
  - If we want to install a custom node, how can we do that safely such that we can roll back to the previous pip state if there are dependency conflicts during installation?

- 3 options
  - a) Don't. Delegate responsibility for python dependencies to python ecosystem by installing comfy and custom nodes one-by-one
    - pros:
      - less work
      - same approach taken by 95% of python projects
    - cons:
      - resulting install is not predictable, is dependent on the exact order in which nodes are installed
        - when you `pip install a b`, modern pip (>20.3) fully resolves the mutual dependencies of `a` and `b` and errors out on any conflicts
        - however when you do `pip install a && pip install b`, pip won't consider the dependency contraints of `a` when resolving the deps of `b`. Instead, it simply replaces any conflicting packages with the version preferred by `b`
      - no great way to snapshot and/or rollback
        - can still do some basic stuff with `pip freeze`

  - b) Enforce "core" dependencies/versions via nested environments
    - in top level venv-core, install core comfyui requriements
    - in each nested venv-node-x, install all requirements for some set of custom nodes
    - pros:
      - when in nested venv, pip refuses to install/uninstall anything in the top level venv
      - saves the disk space that otherwise would be required to install all comfy core deps in each and every venv representing a set of custom nodes
    - cons:
      - really complicated
      - due to ^^^^^, hard to set up well in the first place, likely prone to bugs
        - for example, in the case of an outright conflict between packages in top level/nested venv, pip will install a "shadow" package in the nested venv
    - refs:
      - https://stackoverflow.com/questions/61019081/is-it-possible-to-create-nested-virtual-environments-for-python
      
  - c) Gather and resolve all core and node dependencies into a single explicit requirements.txt file
    - 
    
- options b. and c. are not mutually exclusive
- for the purpose of snapshotting, however, option c by itself should be the simplest

2. What are entry points (EP) and how do they help here?

- roughly speaking, there are 3 kinds of EP in python
  - script EP, that installs a specific executable .py file to $PATH
  - command EP, that installs a script on $PATH that calls a specific python function
  - plugin EP, a simple hook that advertises a plugin function that can be easily discovered/called in a "parent" package that consumes it
 
3. Can `uv` handle pyproject.toml dependencies

- short answer: yes, absolutely
- longer answser: the `uv pip compile` command appears to treat requirements listed in a `pyproject.toml` nearly the same as it does those in `requirement.txt` files. No `-r` flag is needed, instead you can just pass in the path to a dir containing a `pyproject.toml` file.


base_site_packages="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
derived_site_packages="$(./venv/venv-node/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
echo "$base_site_packages" > "$derived_site_packages"/_base_packages.pth