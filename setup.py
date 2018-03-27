import pip
from setuptools import setup,find_packages

reqs = ["pandas==0.22.0","numpy==1.14.2"]


#this is a bit of a hack, due to the inability to build numpy properly in a reasonable amount of time
for req in reqs:
    pip.main(["install", req])

setup(
    name='smurfs',
    version='0.1.5',
    packages=find_packages(exclude=["*test","dist","build","venv"]),
    url='https://github.com/muma7490/SMURFS',
    license='MIT',
    author='Marco Müllner',
    author_email='muellnermarco@gmail.com',
    description='Smart UseR Frequency analySer, a fast and easy to use frequency analyser.',
)