from setuptools import setup, find_packages

setup(
    name="llmtool",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "llmtool=llmtool.__main__:main",
        ]
    },
    install_requires=[],
)
