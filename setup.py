"""
Provides a python package to get data of academic papers
posted at arXiv.org in a specific date range and category.

Collected data:

        Title,
        ID,
        Authors,
        Abstract,
        Subcategories,
        DOI,
        Created (date),
        Updated (date)
"""

import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    sys.exit(
        """Error: Setuptools is required for installation.
 -> http://pypi.python.org/pypi/setuptools"""
    )

setup(
    name="arxivscraper",
    version="0.1.3",
    description="Get arXiv.org metadate within a date range and category",
    author="Mahdi Sadjadi, Joe Lyman",
    author_email="sadjadi.seyedmahdi@gmail.com",
    url="https://github.com/Lyalpha/arxivscraper",
    py_modules=[""],
    packages=find_packages(),
    keywords=["arxiv", "scraper", "api", "citation"],
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Topic :: Text Processing :: Markup :: LaTeX",
    ],
)
