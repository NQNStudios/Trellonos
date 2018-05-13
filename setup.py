from setuptools import setup

setup(
    name='Trellonos',
    version='0.1dev',
    packages=['trellonos','scripts',],
    install_requires=['reportlab','markdown','trello','PyGithub','PyYAML','python-dateutil',],
)
