import os
import subprocess
import sys
import site
import platform
import configparser
from pathlib import Path
from shutil import which
from typing import List

VENV = ".venv"

# ANSI escape codes for colored output
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"


def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")


def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")


def print_info(msg):
    print(f"👉 {msg}")


def print_header(msg):
    print(f"\n🔎 {msg}\n{'=' * 30}")


class ProjectSetup:
    def __init__(self):
        self._use_poetry: bool = False
        self._package_name: str = ""

    def _detect_platform(self):
        sysname = os.uname().sysname
        arch = os.uname().machine
        print("🧠 Detecting OS and architecture...")

        os_type = "unknown"
        if sysname == "Darwin":
            os_type = "mac"
        elif sysname == "Linux":
            os_type = "debian" if os.path.exists("/etc/debian_version") else "linux"
        else:
            print_error(f"Unsupported OS: {sysname}")
            sys.exit(1)

        print(f"📟 OS: {os_type} | Architecture: {arch}")

        project_tool = self._detect_project_tool()
        if project_tool == "poetry":
            self._use_poetry = True
            print_info("Detected Poetry project from pyproject.toml.")
        elif project_tool == "hatch":
            self._use_poetry = False
            print_info("Detected Hatch project from pyproject.toml.")
        elif project_tool == "flit":
            self._use_poetry = False
            print_info("Detected Flit project from pyproject.toml.")
        else:
            pip_or_poetry = input("📦 Do you want to use pip or poetry? (default: pip): ") or "pip"
            self._use_poetry = pip_or_poetry.lower() == "poetry"

        return os_type

    def _detect_project_tool(self):
        if not os.path.exists("pyproject.toml"):
            return None
        try:
            with open("pyproject.toml", "r", encoding="utf-8") as f:
                contents = f.read()
                if "[tool.poetry]" in contents:
                    return "poetry"
                elif "[tool.hatch]" in contents:
                    return "hatch"
                elif "[tool.flit]" in contents:
                    return "flit"
        except Exception:
            return None
        return None

    def _convert_requirements_to_poetry(self) -> str:
        deps = []
        if os.path.exists("requirements.txt"):
            with open("requirements.txt", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        deps.append(line)
        return "\n".join([f"{dep}" for dep in deps])

    def _create_pyproject_toml(self):
        if os.path.exists("pyproject.toml"):
            print_success("pyproject.toml already exists.")
            return

        print_info("pyproject.toml not found. Let's create one.")
        self._package_name = self._get_default_package_name()
        package_name_input = input(f"Package name (default: {self._package_name}): ")
        if package_name_input:
            self._package_name = package_name_input.replace(" ", "-").lower().replace("-", "_")

        package_version = input("Package version (default: 0.1.0): ") or "0.1.0"
        package_description = input("Package description: ")
        author_name = self._get_git_config("user.name") or "unnamed developer"
        author_email = self._get_git_config("user.email") or "developer@example.com"

        author_name = input(f"Author name (default: {author_name}): ") or author_name
        author_email = input(f"Author email (default: {author_email}): ") or author_email

        src_package_path = Path(f"src/{self._package_name}")
        src_package_path.mkdir(parents=True, exist_ok=True)
        init_file = src_package_path / "__init__.py"
        init_file.touch(exist_ok=True)

        if self._use_poetry:
            deps_block = self._convert_requirements_to_poetry()
            content = f"""
                [tool.poetry]
                name = "{self._package_name}"
                version = "{package_version}"
                description = "{package_description}"
                authors = ["{author_name} <{author_email}>"]

                [tool.poetry.dependencies]
                python = "^3.8"
{self._indent_dependencies(deps_block)}

                [tool.poetry.dev-dependencies]
                pytest = "^7.0"

                [build-system]
                requires = ["poetry-core>=1.0.0"]
                build-backend = "poetry.core.masonry.api"
            """
        else:
            build_system = input("Build system (default: hatchling): ") or "hatchling"
            content = f"""
                [project]
                name = "{self._package_name}"
                version = "{package_version}"
                description = "{package_description}"
                authors = [{{name="{author_name}", email="{author_email}"}}]
                requires-python = ">=3.8"

                [tool.pytest.ini_options]
                pythonpath = ["src"]
                testpaths = ["tests", "src"]
                markers = [
                    "integration: marks tests as integration (deselect with '-m \\"not integration\\"')"
                ]
                addopts = "-m 'not integration'"

                [build-system]
                requires = ["{build_system}"]
                build-backend = "{build_system}.build"

                [tool.hatch.build.targets.wheel]
                packages = ["src/{self._package_name}"]
            """
            os.makedirs("tests", exist_ok=True)

        with open("pyproject.toml", "w", encoding="utf-8") as file:
            file.write(self._strip_content(content))
        print_success("pyproject.toml created.")

    def _indent_dependencies(self, deps: str) -> str:
        return "\n".join([" " * 4 + dep for dep in deps.splitlines() if dep.strip()])

    def _get_default_package_name(self):
        return Path(os.getcwd()).name.lower().replace(" ", "_").replace("-", "_")

    def _get_git_config(self, key: str) -> str:
        try:
            result = subprocess.run(["git", "config", "--get", key], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            return None
        return None

    def _strip_content(self, content: str) -> str:
        return "\n".join(line.strip().replace("\t", "") for line in content.split("\n") if line.strip())

    def _setup_requirements(self):
        self._write_if_missing("requirements.txt", "# project requirements")
        self._write_if_missing("requirements.dev.txt", self._strip_content(self._dev_requirements_content()))

    def _write_if_missing(self, filename: str, content: str):
        if not os.path.exists(filename):
            print_info(f"{filename} not found. Let's create one.")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            print_success(f"{filename} created.")
        else:
            print_success(f"{filename} already exists.")

    def _dev_requirements_content(self) -> str:
        return """
            pytest
            mypy
            types-python-dateutil
            build
            toml
            twine
            wheel
            pkginfo
            hatchling
            moto
        """

    def setup(self):
        self._detect_platform()
        self._setup_requirements()
        (self._setup_poetry if self._use_poetry else self._setup_pip)()
        self.print_env_info()
        print("\n🎉 Setup complete!")
        if not self._use_poetry:
            print(f"➡️  Run 'source {VENV}/bin/activate' to activate the virtual environment.")

    def _setup_poetry(self):
        self._create_pyproject_toml()
        print("📚  Using Poetry for environment setup...")
        try:
            if which("poetry") is None:
                print("⬇️ Installing Poetry...")
                subprocess.run("curl -sSL https://install.python-poetry.org | python3 -", shell=True, check=True)
                os.environ["PATH"] = f"{os.path.expanduser('~')}/.local/bin:" + os.environ["PATH"]

            result = subprocess.run(["poetry", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                print_error("Poetry installation failed.")
                sys.exit(1)
            print_success(result.stdout.strip())

            print("🔧 Creating virtual environment with Poetry...")
            subprocess.run(["poetry", "install"], check=True)
        except subprocess.CalledProcessError as e:
            print_error(f"Poetry setup failed: {e}")
            sys.exit(1)

    def _setup_pip(self):
        self._create_pyproject_toml()
        print(f"🐍 Setting up Python virtual environment at {VENV}...")
        try:
            subprocess.run(["python3", "-m", "venv", VENV], check=True)
            subprocess.run([f"{VENV}/bin/pip", "install", "--upgrade", "pip"], check=True)

            for req_file in self.get_list_of_requirements_files():
                print(f"🔗 Installing packages from {req_file}...")
                subprocess.run([f"{VENV}/bin/pip", "install", "-r", req_file, "--upgrade"], check=True)

            print("🔗 Installing local package in editable mode...")
            subprocess.run([f"{VENV}/bin/pip", "install", "-e", "."], check=True)
        except subprocess.CalledProcessError as e:
            print_error(f"pip setup failed: {e}")
            sys.exit(1)

    def get_list_of_requirements_files(self) -> List[str]:
        return [f for f in os.listdir(Path(__file__).parent) if f.startswith("requirements") and f.endswith(".txt")]

    def print_env_info(self):
        print_header("Python Environment Info")
        print(f"📦 Python Version     : {platform.python_version()}")
        print(f"🐍 Python Executable  : {sys.executable}")
        print(f"📂 sys.prefix         : {sys.prefix}")
        print(f"📂 Base Prefix        : {getattr(sys, 'base_prefix', sys.prefix)}")
        site_packages = site.getsitepackages()[0] if hasattr(site, 'getsitepackages') else 'N/A'
        print(f"🧠 site-packages path : {site_packages}")
        in_venv = self.is_virtual_environment()
        print(f"✅ In Virtual Env     : {'Yes' if in_venv else 'No'}")
        if in_venv:
            print(f"📁 Virtual Env Name   : {Path(sys.prefix).name}")

    def is_virtual_environment(self):
        return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def main():
    ps = ProjectSetup()
    ps.setup()


if __name__ == "__main__":
    main()
