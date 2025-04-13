from setuptools import setup, find_packages
import os
import subprocess
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
import pkg_resources
import re

def generate_proto():
    """Generate proto files."""
    try:
        # Check if grpcio-tools is installed
        pkg_resources.require('grpcio-tools')
    except pkg_resources.DistributionNotFound:
        # Install grpcio-tools if not found
        subprocess.check_call(['pip', 'install', 'grpcio-tools>=1.44.0'])
    
    proto_file = "arbvantage_provider/protos/hub.proto"
    if os.path.exists(proto_file):
        print("Generating proto files...")
        subprocess.check_call([
            "python", "-m", "grpc_tools.protoc",
            "-I.", 
            f"--python_out=.",
            f"--grpc_python_out=.",
            proto_file
        ])

class CustomBuildPy(build_py):
    """Custom build command to generate proto files."""
    def run(self):
        generate_proto()
        build_py.run(self)

class CustomDevelop(develop):
    """Custom develop command to generate proto files."""
    def run(self):
        generate_proto()
        develop.run(self)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read version from __init__.py
with open('arbvantage_provider/__init__.py', 'r') as f:
    version = re.search(r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read()).group(1)

setup(
    name="arbvantage-provider",
    version=version,
    author="Valera Satsura",
    author_email="satsura@gmail.com",
    description="A framework for creating Arbvantage providers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arbvantage/arbvantage-provider",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    setup_requires=[
        "grpcio",
        "grpcio-tools",
    ],
    install_requires=[
        "grpcio",
        "grpcio-tools",
        "backoff",
        "protobuf",
        "pydantic",
        "requests",
        "pytz",
    ],
    cmdclass={
        'build_py': CustomBuildPy,
        'develop': CustomDevelop,
    },
) 