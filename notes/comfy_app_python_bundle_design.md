# comfyui standalone python bundle design
- `pyinstaller`, `cx_freeze`, etc, won't work as is, probably not worth the effort

  - problems:
    - populates `sys.executable` in a highly non-standard way
      - under almost all circumstances, `sys.executable` is the proximal python interpreter in the process. Instead, `pyinstaller` makes `sys.executable` point to it's bundled executable
      - this breaks anything that calls `subprocess.run([sys.executable, ...])`, eg `comfy-cli`, `uv`, many other things
    - supplies a custom executable, not a python interpreter
      - probably the reason why `sys.executable` is not populated correctly
      - in general makes it at least very awkward for the bundled executable to call any other python script as a subprocess
    - in general, due to restructuring it breaks a lot of custom path handling
      - in particular, this makes `uv` almost impossible to run
        - the `uv` python package is just a thin wrapper that finds and runs the `uv` rust binary as a subprocess. `pyinstaller` completely breaks `uv`'s logic for finding the rust binary
      - the subprocess call that `comfy-cli` makes to `cm-cli` also completely breaks

  - some of the above problems can fixed easily (if a bit messily), some are very hard
    - easy-ish: fixing `sys.executable` issue
      - can make python subprocesses run-able by adding entry shims as top level executables in the `pyinstaller` bundle
        - eg add script at top level that just imports `__main__` from `uv` and runs it
      - in our code, we could add guards around relevant `subprocess` calls that check if in frozen bundle, and if so point to the shim script instead of `sys.executable`
    - very hard: fixing rust binary finding code in `uv`
      - might be do-able, probably will involve serious hackery and/or upstream changes

- a much simpler, easier design: ship a standalone (but otherwise vanilla) python interpreter with a pre-populated cache-dir

  - getting a standalone python interpreter
    - on windows, there are the official `embeddable` distros
      - see: https://www.python.org/downloads/windows/
    - on all platforms, there's the [python-build-standalone](https://github.com/indygreg/python-build-standalone) project
      - this needs some testing

  - setting up `pip` in a standalone python interpreter is a solved problem
    - see: https://stackoverflow.com/a/48906746

  - all other "bundled" python dependencies can be handled by pre-populating a cache-dir
    - normally cache-dir contains the install artifacts downloaded by `pip` (or `uv`, or whatever)
    - if we pre-populate the artifacts in our installer, we save the user from having to download them during the installer run
    - this should produce an installation UX nearly equivalent to that of copy/pasting a `pyinstaller` bundle
      - the difference is the runtime of `uv pip install ...`, but that typically is less than a second

  - typical execution flow:
    - start installer
    - installer sets up standalone python
    - standalone python is used to create and activate a venv
    - `pip` is set up inside of the venv
    - run `pip install uv --cache-dir=<foo>`
    - run `uv pip install comfy-cli --cache-dir=<foo>`
    - use `comfy-cli` to install comfy core, manager, and all deps
      - ensure that all calls to `uv` are passed the appropriate `--cache-dir=<foo>` arg
        - we'll need some new code for this (maybe just a `--cache-dir` option for `comfy-cli`)
