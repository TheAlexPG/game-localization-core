"""Setup configuration for game-translator package"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="game-translator",
    version="1.0.0",
    author="Your Name",
    description="AI-powered game localization tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/game-translator",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Games/Entertainment",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0",
        "rich>=10.0",
        "openpyxl>=3.0",
        "openai>=1.0",
        "requests>=2.25",
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.900",
        ],
        "web": [
            "fastapi>=0.68",
            "uvicorn>=0.15",
        ],
    },
    entry_points={
        "console_scripts": [
            "game-translator=game_translator_cli.main:cli",
        ],
    },
)