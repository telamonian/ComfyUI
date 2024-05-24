# Design Doc

## Motivation

(this is a draft of the blog abstract)

Normally, Python installs dependencies in an order-dependent, FIFO manner. This means that the more recently you installed a package, the more likely said package's dependencies are to be correct and up-to-date. This is good enough in many general purpose Python environments. However, in a ComfyUI environment, the dependencies of core `comfyui` and every single installed custom node extension must be ensured at run time in order for the ComfyUI app to function correctly. Ideally, we want a  cleaner, more predictable approach to Python dependencies that produces a deterministic result. To this end, cm-cli has implemented a set of comfy-specific dependency management tools on top of `uv` and other established projects. These tools allow cm-cli to install, record, and restore the Python environment needed for any possible comfy workflow.

## Features

## Implementation

## Integration with Existing Comfy-CLI Assets
