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
    - In the future, if/when core and extensions are packaged as Python modules, this may become much simpler
  3. Feed all Python deps to uv compile
    - 

## Integration with Existing Comfy-CLI Assets
