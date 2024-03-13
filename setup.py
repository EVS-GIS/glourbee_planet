from setuptools import setup
from glourbee import __version__

setup(
    name='glourbee',
    version=__version__,
    py_modules=['glourbee.*'],
    install_requires=[
        'click',
        'numpy',
        'geopandas',
        'earthengine-api',
        'pandas',
        'geemap',
        'geetools',
        # 'ipython',
        # 'ipykernel',
        # 'ipyleaflet==0.16',
    ],
)