from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="arbvantage-provider",
    version="0.1.0",
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
    install_requires=[
        "grpcio>=1.44.0",
        "backoff>=2.1.2",
        "protobuf>=3.20.0",
        "grpcio-tools>=1.44.0",
    ],
) 