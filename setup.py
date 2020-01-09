import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

def get_requirements(remove_links=True):
    """
    lists the requirements to install.
    """
    requirements = []
    try:
        with open('requirements.txt') as f:
            requirements = f.read().splitlines()
    except Exception as ex:
        with open('DecoraterBotUtils.egg-info\requires.txt') as f:
            requirements = f.read().splitlines()
    if remove_links:
        for requirement in requirements:
        # git repository url.
            if requirement.startswith("git+"):
                requirements.remove(requirement)
            # subversion repository url.
            if requirement.startswith("svn+"):
                requirements.remove(requirement)
            # mercurial repository url.
            if requirement.startswith("hg+"):
                requirements.remove(requirement)
    return requirements


def get_links():
    """
    gets URL Dependency links.
    """
    links_list = get_requirements(remove_links=False)
    for link in links_list:
        keep_link = False
        already_removed = False
        # git repository url.
        if not link.startswith("git+"):
            if not link.startswith("svn+"):
                if not link.startswith("hg+"):
                    links_list.remove(link)
                    already_removed = True
                else:
                    keep_link = True
                if not keep_link and not already_removed:
                    links_list.remove(link)
                    already_removed = True
            else:
                keep_link = True
            if not keep_link and not already_removed:
                links_list.remove(link)
    return links_list


setuptools.setup(
    name="smurfs",
    version="1.0.12",
    author="Marco Müllner",
    author_email="muellnermarco@gmail.com",
    description="Smart UseR Frequency analySer, a fast and easy to use frequency analyser.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/muma7490/SMURFS",
    install_requires=get_requirements(),
    dependency_links=get_links(),
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts':['smurfs = smurfs.__main__:main']
    }
)
