from pathlib import Path
import subprocess
import sys

cmd_install_torch = [sys.executable, '-m', 'pip', 'install', '-r', 'requirements_torch_amd.txt']
cmd_compile_top = [sys.executable, '-m', 'uv', 'pip', 'compile', '-q', 'requirements_top.txt', '-o', 'requirements_top.lock', '--override', 'overrides.txt']
cmd_install_top = [sys.executable, '-m', 'uv', 'pip', 'install', '-r', 'requirements_top.lock', '--verbose']

topName = 'requirements_top'

def run(cmd: list[str], cwd: str):
    """uses check_call to run pip, as reccomended by the pip maintainers.
    see https://pip.pypa.io/en/stable/user_guide/#using-pip-from-your-program"""

    subprocess.check_call(cmd, cwd=cwd)

def installTorch(p: Path):
    """special handling for installing gpu-specific torch. uv doesn't
    handle --pre correctly, so we just use base pip for this step"""

    run(cmd_install_torch, str(p))

def makeTop(p: Path):
    """write a top-level requirements file that links to the requirements of
    comfyui and all installed custom nodes"""

    reqs = p.glob('custom_nodes/[!__pycache__]*/requirements.txt')

    with open(f'{topName}.txt', 'w') as f:
        f.write('# main comfy ui dependencies\n')
        f.write('-r requirements.txt\n\n')
        f.write('# custom node dependencies\n')
        for req in reqs:
            f.write(f'-r {req}\n')

        f.write('\n')

def compileTop(p: Path):
    """resolve the top-level requirements into a "lock" file using `uv pip compile`
    (see https://github.com/astral-sh/uv?tab=readme-ov-file#limitations)"""

    run(cmd_compile_top, str(p))

def installTop(p: Path):
    """install the resolved top-level requirements using `uv pip install`"""

    run(cmd_install_top, str(p))

if __name__ == '__main__':
    here = Path('.')

    installTorch(here)
    makeTop(here)
    compileTop(here)
    installTop(here)
