from pathlib import Path
import subprocess
import sys

rocmPytorchUrl = 'https://download.pytorch.org/whl/rocm6.0'
topName = 'requirements_top'

cmd_compile_top = [sys.executable, '-m', 'uv', 'pip', 'compile', '-q', f'{topName}.txt', '-o', f'{topName}.lock', '--override', 'overrides.txt']
cmd_install_top = [sys.executable, '-m', 'uv', 'pip', 'install', '--extra-index-url', rocmPytorchUrl, '-r', f'{topName}.lock', '--verbose']


def run(cmd: list[str], cwd: str):
    """uses check_call to run pip, as reccomended by the pip maintainers.
    see https://pip.pypa.io/en/stable/user_guide/#using-pip-from-your-program"""

    subprocess.check_call(cmd, cwd=cwd)

def makeTop(p: Path):
    """write a top-level requirements file that links to the requirements of
    comfyui and all installed custom nodes"""

    reqs = p.glob('custom_nodes/[!__pycache__]*/requirements.txt')

    with open(f'{topName}.txt', 'w') as f:
        f.write('# ensure usage of amd/rocm version of pytorch\n')
        f.write(f'--extra-index-url {rocmPytorchUrl}\n\n')
        f.write('# main comfy ui dependencies\n')
        f.write('-r requirements.txt\n\n')
        f.write('# custom node dependencies\n')
        for req in reqs:
            f.write(f'-r {req}\n')

        f.write('\n')

def compileTop(p: Path):
    """resolve the top-level requirements into a "lock" file using `uv pip compile`
    (see https://github.com/astral-sh/uv?tab=readme-ov-file#limitations)"""
    
    # first, clean up
    (p / f'{topName}.lock').unlink(missing_ok=True)
    run(cmd_compile_top, str(p))

def installTop(p: Path):
    """install the resolved top-level requirements using `uv pip install`"""

    run(cmd_install_top, str(p))

if __name__ == '__main__':
    here = Path('.')

    makeTop(here)
    compileTop(here)
    installTop(here)
