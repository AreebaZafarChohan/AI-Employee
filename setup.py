"""Setup script for AI Employee Bronze Tier."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ai-employee",
    version="0.1.0",
    author="AI Employee Team",
    author_email="team@ai-employee.local",
    description="Personal AI Employee Bronze Tier - Local-first Obsidian vault workflow system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ai-employee/ai-employee",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ai-employee=cli.main:main",
        ],
    },
)
