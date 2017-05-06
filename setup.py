from setuptools import setup

def read_file(filename):
    with open(filename, 'r') as stream:
        req = stream.read()
    return req

setup(
    name='webapp',
    version='0.1.0',
    install_requires=read_file('requirements.txt'),
)
