import pip
from smurfs._version import __version__
pipVer = pip.__version__.split(".")

#main is not directly accessible anymore on pip > 10
if int(pipVer[0]) < 10:
    from pip import main
else:
    from pip._internal import main

from setuptools import setup,find_packages

reqs = ["pandas==0.22.0"
        ,"numpy==1.14.2"
        ,"astropy==3.0.1"
        ,"scipy==1.0.1"
        ,"plotnine==0.2.1"
        ,"pandas==0.22.0"
        ,"stem==1.6.0"
        ,"matplotlib==2.2.2"]


#this is a bit of a hack, due to the inability to build numpy properly in a reasonable amount of time
for req in reqs:
        main(["install", req])

setup(
    name='smurfs',
    version=__version__,
    packages=find_packages(exclude=["*test","dist","build","venv"]),
    url='https://github.com/muma7490/SMURFS',
    license='MIT',
    author='Marco Müllner',
    author_email='muellnermarco@gmail.com',
    description='Smart UseR Frequency analySer, a fast and easy to use frequency analyser.',
)
