import os
from pathlib import Path
import subprocess
import sys
from textwrap import dedent
from typing import Any

PathLike = os.PathLike[str] | str

def run(cmd: list[str], cwd: str = ".") -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )

def check_call(cmd: list[str], cwd: str = "."):
    """uses check_call to run pip, as reccomended by the pip maintainers.
    see https://pip.pypa.io/en/stable/user_guide/#using-pip-from-your-program"""

    subprocess.check_call(cmd, cwd=cwd)

class Appler:
    rocmPytorchUrl = "https://download.pytorch.org/whl/rocm6.0"
    nvidiaPytorchUrl = "https://download.pytorch.org/whl/cu121"

    overrideGpu = dedent("""
        # ensure usage of {gpu} version of pytorch
        --extra-index-url {gpuUrl}
        torch
        torchsde
        torchvision
    """).strip()

    reqNames = [
        "requirements.txt",
        "pyproject.toml",
        "setup.cfg",
        "setup.py",
    ]

    @staticmethod
    def findReqFiles(p: PathLike) -> list[Path]:
        p = Path(p).absolute()
        reqFiles: list[Path] = []
        for reqName in Appler.reqNames:
            reqFiles.extend(p.glob(reqName))
        return reqFiles
    
    # cmdCompileTop = [sys.executable, "-m", "uv", "pip", "compile", "-q", f"{topName}.txt", "-o", f"{topName}.lock", "--override", "overrides.txt"]
    # cmdInstallTop = [sys.executable, "-m", "uv", "pip", "install", "--extra-index-url", rocmPytorchUrl, "-r", f"{topName}.lock", "--no-deps"]

    @staticmethod
    def compile(reqFiles: list[PathLike], override: PathLike | None = None, out: PathLike | None = None) -> subprocess.CompletedProcess[Any]:
        cmd = [
            sys.executable,
            "-m",
            "uv",
            "pip",
            "compile",
        ]
        
        for reqFile in reqFiles:
            cmd.append(str(reqFile))

        if override is not None:
            cmd.extend([
                "--override",
                str(override),
            ])
        
        if out is not None:
            cmd.extend([
                "-o",
                str(out),
            ])

        return run(cmd)

    def __init__(
        self,
        cwd: PathLike = ".",
        extDirs: list[PathLike] = [],
        gpu: str | None = None,
        outName: str = "requirements.compiled",
    ):
        self.cwd = Path(cwd)
        self.extDirs = [Path(extDir) for extDir in extDirs] if extDirs is not None else None
        self.gpu = gpu

        self.gpuUrl = Appler.nvidiaPytorchUrl if self.gpu == "nvidia" else Appler.rocmPytorchUrl if self.gpu == "amd" else None
        self.out = self.cwd / outName
        self.override = self.cwd / "override.txt"

        self.coreReqFiles = Appler.findReqFiles(self.cwd)
        self.extReqFiles = [reqFile for extDir in self.extDirs for reqFile in Appler.findReqFiles(extDir)]

    def makeOverride(self):
        #clean up
        self.override.unlink(missing_ok=True)

        with open(self.override, "w") as f:
            if self.gpu is not None:
                f.write(Appler.overrideGpu.format(gpu=self.gpu, gpuUrl=self.gpuUrl))
                f.write("\n\n")
            f.write("# ensure that core comfyui deps take precedence over any 3rd party extension deps\n")

        coreOverride = Appler.compile(self.coreReqFiles, override=self.override)

        with open(self.override, "a") as f:
            for line in coreOverride.stdout:
                f.write(line)

    def compileCorePlusExt(self):
        #clean up
        self.out.unlink(missing_ok=True)

        Appler.compile(
            reqFiles=(self.coreReqFiles + self.extReqFiles),
            override=self.override,
            out=self.out,
        )

    def handleOpencv(self):
        """as per the opencv docs, you should only have exactly one opencv package.
        headless is more suitable for comfy than the gui version, so remove gui if
        headless is present. TODO: add support for contrib pkgs. see: https://github.com/opencv/opencv-python"""
        
        with open(self.out, "r") as f:
            lines = f.readlines()
        
        guiFound, headlessFound = False, False
        for line in lines:
            if "opencv-python==" in line:
                guiFound = True
            elif "opencv-python-headless==" in line:
                headlessFound = True

        if headlessFound and guiFound:
            with open(self.out, "w") as f:
                for line in lines:
                    if "opencv-python==" not in line:
                        f.write(line)

def installComfyDeps(cwd: PathLike, gpu: str):
    p = Path(cwd)
    extDirs = [d for d in p.glob("custom_nodes/[!__pycache__]*") if d.is_dir()]
    
    appler = Appler(cwd=cwd, extDirs=extDirs, gpu=gpu)

    appler.makeOverride()
    appler.compileCorePlusExt()
    appler.handleOpencv()

# def installTop(p: Path):
#     """install the resolved top-level requirements using `uv pip install`"""

#     run(cmdInstallTop, str(p))

# if __name__ == "__main__":
#     here = Path(".")

#     makeTop(here)
#     compileTop(here)
#     installTop(here)

if __name__ == "__main__":
    installComfyDeps(cwd=".", gpu="amd")
