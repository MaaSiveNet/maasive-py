from setuptools import setup

setup(
    name='maasivepy',
    version='1.2.7',
    author='Josh Austin',
    author_email='josh@maasive.net',
    packages=['maasivepy'],
    entry_points={
        "console_scripts": [
            "maasivecommand=maasivepy.maasivecommand:main"
        ],
    }
)
