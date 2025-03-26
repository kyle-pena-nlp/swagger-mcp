import tomli
from setuptools import setup, find_packages

def read_requirements(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Get version from pyproject.toml
with open("pyproject.toml", "rb") as f:
    pyproject = tomli.load(f)
version = pyproject["project"]["version"]

# Get requirements
install_requires = read_requirements("requirements.txt")

setup(
    name="swagger-mcp",
    version=version,
    author="Kyle Pena",
    author_email="kyle.pena@kuzco.xyz",
    description="MCP server for Swagger/OpenAPI integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/context-labs/swagger-mcp",
    packages=find_packages(exclude=["tests*", "sample_rest_api*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=install_requires,
    data_files=[(".", ["requirements.txt"])],
    entry_points={
        "console_scripts": [
            "swagger-mcp=swagger_mcp.openapi_mcp_server:main",
        ],
    },
)
