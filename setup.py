import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name="zephyrus-sc2-parser",
    version="0.1.13",
    author="ZephyrBlu/Luke Holroyd",
    author_email="hello@zephyrus.gg",
    description="Parser for SC2 replay files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ZephyrBlu/zephyrus-sc2-parser",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
