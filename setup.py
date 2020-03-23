import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements = fh.read().splitlines()

setuptools.setup(
    name="smurfs",
    version="1.1.7",
    author="Marco Müllner",
    author_email="muellnermarco@gmail.com",
    description="Smart UseR Frequency analySer, a fast and easy to use frequency analyser.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/muma7490/SMURFS",
    install_requires=requirements,
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts':['smurfs = smurfs.__main__:main']
    }
)
