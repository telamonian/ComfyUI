# handling custom nodes and dependencies

## Node-like dependency conflict resolution in Python
- Short answer: don't
- Longer answer, node/js has support for multiple versions of dependencies at both the language and infrastructure/tooling level. Default cpython has no way to support these things
  - The cpython maintainers aren't interested in this pattern. Ultimately it comes down to the differing philosophies of the js/python communities:
    - see eg https://discuss.python.org/t/installing-multiple-versions-of-a-package/4862
  - The closest Python ever got to `node_modules` was [PEP 582](https://peps.python.org/pep-0582/), but it was rejected
- Python *can* be made to support multiple versions of a single package, but it requires changes to Python's internal `importlib` in addition to new packaging tooling  
  - For example, see this person's hack/implementation of multiple pkg versions via name mangling:
    - https://discuss.python.org/t/allowing-multiple-versions-of-same-python-package-in-pythonpath/2219
    - https://github.com/nix-community/nixpkgs-pytools/?tab=readme-ov-file#python-rewrite-imports
- None of the popular Python packaging tools (pip, pipx, uv, poetry, pdm) have any support whatsoever for this

## How custom nodes dependencies could be handled
- From what I can see, there are 3 related problems with the Python dependencies of custom nodes:
  - Installing requirements 1 package at a time causes many problems, especially with complex packages such as `opencv`
    - Solution: group the requirements of ComfyUI and all custom nodes in one location and resolve them all together
  - Custom nodes usually aren't actual python packages, there's no standardization in how they specify dependencies
    - See eg [ComfyUI_IPAdapter_plus](https://github.com/cubiq/ComfyUI_IPAdapter_plus), which doesn't even have a `requirements.txt`, instead choosing to list deps at a random place in the README
    - Solution: work with the ComfyUI maintainers to standardize a schema for custom nodes as python packages with well-defined comfyui-specific metadata
  - Even if the above issues are solved, there can still be actual dependency version conflicts
    - `pip` and most other package managers don't have any support for dealing with this at the package consumer level. Basically, they say to bug the package maintainers about it, and that otherwise [you're out of luck](https://pip.pypa.io/en/stable/topics/dependency-resolution/#all-requirements-are-appropriate-but-a-solution-does-not-exist)
    - "solution": `uv` supports a top-level [`overrides.txt`](https://github.com/astral-sh/uv?tab=readme-ov-file#dependency-overrides) that takes priority over any version constraints specificed by dependencies
      - This won't fix every conflict, but in the case of too-strict constraints/pins it can help

## Support for ComfyUI custom nodes as Python packages via the `entry_point` plugin mechanism:
- refs:
  - https://github.com/comfyanonymous/ComfyUI/issues/1613
  - https://github.com/comfyanonymous/ComfyUI/pull/298
- A sprawling effort by a very enthusiastic outside contributor. The issue/PR links back to many of the other threads on the ComfyUI github discussing this topic
- Basically, the PR author has come up with a reasonable way of handling custom nodes via Python’s builtin support for plugins as entry_points (via `importlib.metadata`, see [setuptools docs]( https://setuptools.pypa.io/en/latest/userguide/entry_point.html#entry-points-for-plugins))
- The problem is that the PR author has tried to contribute it as part of tens of thousands of lines worth of other, non-related code changes
- The ComfyUI maintainers seem to be receptive to the entry_points approach (eg [this comment](https://github.com/comfyanonymous/ComfyUI/pull/298#issuecomment-1917598207))
- Could be easily broken out and cleaned up into a new PR that would be much more likely to get pulled in

## Pros and cons of different Python packaging tools
- uv
  - pros
    - most important: the only mainstream python packaging tool that supports dependency overrides
    - drop-in replacement for pip, so it's "easy" to use
    - claimed to be much faster than base pip, and it seems to be
    - via `compile` cmd, can combine multiple requirements.txts (eg comfyui + custom nodes) into a single "lock" file with explicit versions
  - cons
    - not 100% compatible with pip
      - in particular, has poor support for the `--prerelease` flag and for `x.y+tag` tagged version specifiers
        - this makes support for the gpu-specific pytorch packages problematic, but workable
    - still pretty new, and thus buggy
      - for example, it claims that `tqdm==4.65.0` doesn't exist (which it does). I "fixed" this by adding tqdm to overrides.txt
- poetry
  - pros
    - has lockfiles
  - cons
    - real slow
    - requires a lot of explicit config for packages not on pypi (eg torch+gpu packages)
    - requires non-standard `pyproject.toml` file that isn't 100% compatible with `pip`, `uv`, etc
    - do we actually need a lock file? Given that users can install an arbitrary set of custom nodes, insisting on lock files is counterproductive
      - a lockfile may still make sense at top level for just core comfyui alone
