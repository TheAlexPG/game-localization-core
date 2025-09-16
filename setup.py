#!/usr/bin/env python3
"""Setup configuration for Game Translator package"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "AI-powered game localization tool with translation validation and quality control"

# Core requirements
install_requires = [
    "click>=8.0.0",
    "rich>=10.0.0",
    "requests>=2.25.0",
    "python-dotenv>=0.19.0",
    "openai>=1.0.0",  # Primary translation provider (OpenAI, OpenRouter, DeepSeek)
    "openpyxl>=3.0.0",  # Excel file support for validation patterns and translations
]

# Optional requirements
extras_require = {
    "dev": [
        "pytest>=6.0.0",
        "black>=22.0.0",
        "flake8>=4.0.0",
        "mypy>=0.950",
        "pytest-cov>=3.0.0",
    ],
    "docs": [
        "sphinx>=4.0.0",
        "sphinx-rtd-theme>=1.0.0",
        "myst-parser>=0.17.0",
    ],
}

setup(
    name="game-translator",
    version="1.0.0",
    author="Oleksandr Basiuk",
    author_email="oleksandr.basiuk@example.com",  # Replace with actual email
    description="AI-powered game localization tool with translation validation and quality control",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oleksandr-basiuk/game-translator",  # Replace with actual repo
    project_urls={
        "Bug Reports": "https://github.com/oleksandr-basiuk/game-translator/issues",
        "Source": "https://github.com/oleksandr-basiuk/game-translator",
        "Documentation": "https://github.com/oleksandr-basiuk/game-translator/blob/main/docs/",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    include_package_data=True,
    package_data={
        "game_translator": ["py.typed"],
        "examples": ["*.csv", "*.json", "*.xlsx"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Other Audience",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Internationalization",
        "Topic :: Software Development :: Localization",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Natural Language :: English",
        "Natural Language :: Ukrainian",
        "Natural Language :: Spanish",
        "Natural Language :: French",
        "Natural Language :: German",
        "Natural Language :: Russian",
        "Environment :: Console",
        "Environment :: Web Environment",
    ],
    keywords=[
        "game", "localization", "translation", "ai", "openai", "gpt",
        "validation", "quality", "i18n", "l10n", "gamedev", "unity",
        "unreal", "godot", "cli", "automation"
    ],
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "game-translator=game_translator_cli.main:cli",
            "gt=game_translator_cli.main:cli",  # Short alias
        ],
    },
    zip_safe=False,
    platforms=["any"],
    license="MIT",
)