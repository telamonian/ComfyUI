# Design Doc

## Motivation

(this is a draft of the blog abstract)

Normally, Python installs dependencies in an order-dependent, FIFO manner. This means that the more recently you installed a package, the more likely said package's dependencies are to be correct and up-to-date. This is good enough in many general purpose Python environments. However, in a ComfyUI environment, the dependencies of core `comfyui` and every single installed custom node extension must be ensured at run time in order for the ComfyUI app to function correctly. Ideally, we want a  cleaner, more predictable approach to Python dependencies that produces a deterministic result. To this end, cm-cli has implemented a set of comfy-specific dependency management tools on top of `uv` and other established projects. These tools allow cm-cli to install, record, and restore the Python environment needed for any possible comfy workflow.

## Features

- Produces deterministic Python installations
  - Aims to be as "correct" (in terms of version constraints) as possible, but prioritizes UX
  - Follows a few predictable rules
- Can record and restore any Python environment
  - Record is based on `uv pip compile`
  - Restore is based on `uv pip sync`
  - The records will be stored as part of the cm-cli lockfile
- Also includes dedicated code for handling the various special cases amongst the standard comfy dependencies
  - eg ensuring the correct torch+gpu package, ensuring that exactly one headless install of opencv is present, etc
  - This section of the code can become a sort of repository of community knowledge (via PR) about any special cases that require special handling

## Implementation

- Unfortunately, following in pip's footsteps, uv has no programmatic api
  - This means that all interaction cm-cli <-> uv will have to be through subprocess commands and the output/stdout of uv

- Workflow for the install of the Python env for a workspace:
  1. Get a list of all extensions in the workspace
  2. Based on extensions, gather all Python dependencies
    - Currently that will mean getting the path to/contents of the `requirements.txt` of core and all extensions
    - In the future, if/when core and extensions are packaged as Python modules, this part may become much simpler
  3. Feed all Python deps to uv compile
    - `pip uv compile -r req1 req2 ...`
  4. Based on output, decide what overrides are needed, if any
  5. Run uv compile again with overrides
    - `pip uv compile --overide overides.txt -r req1 req2 ...`
  6. Peform any other special handling needed on the compile results
  7. Sync the results with the env
    - `pip sync compiled.txt`
  8. Save a record of the compile result to the lockfile

## Integration with Existing Comfy-CLI Assets

- The record produced by `uv pip compile` will be stored in it's own section in the lockfile.

- One possible schema:

```yaml
python: [list of requirement specifiers]
  - [req spec defined here: https://pip.pypa.io/en/stable/reference/requirement-specifiers/]
```

- The above is basically the same as the lines you'd find in a normal `requirements.txt`, which matches the output of `uv pip compile`

- There's a *lot* of work to be done in terms of integrating this and all of the other lockfile functionality with the relevant moving parts of cm-cli

## Risks

- Astral drops ongoing support for uv
  - Seems unlikely given that rye is being depracted in favor of uv
  - uv is basically just a very fast bundle of core pip and pip-tools, and aims to be a drop-in replacement. In case uv ever dissappears, our tools can be trivially refactored to use core pip and pip-tools instead.

- Lockfile becomes an unmaneageable mess
  - One way to mitigate this would be to decide on a formal schema early in development 
  - Ideally this would include a json-schema specification. This can serve both as a reference and a PR target
  