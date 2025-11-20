from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="purl",
    version="0.1.0",
    author="Hasitha Mapalagama",
    description="A command-line tool for HTTP request testing with YAML configuration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ImHmg/purl",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "faker>=18.0.0",
        "termcolor>=2.3.0",
        "requests>=2.31.0",
        "requests_toolbelt>=0.9.1",
        "jsonpath-ng>=1.6.0",
        "lxml>=4.9.0",
    ],
    entry_points={
        "console_scripts": [
            "purl=purl.cli:main",
        ],
    },
)
