from setuptools import setup, find_packages

setup(
    name="questrade-custom-api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "typing; python_version < '3.5'"
    ],
    author="Questrade API Wrapper Developer",
    author_email="example@example.com",
    description="A custom wrapper for the Questrade API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="questrade, api, trading, finance",
    url="https://github.com/yourusername/QuestradeCustomAPIWrapper",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.6",
) 