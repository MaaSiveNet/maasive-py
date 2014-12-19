from setuptools import setup

setup(
    name='maasivepy',
    version='1.2.7',
    author='Josh Austin',
    author_email='josh@maasive.net',
    license='MIT',
    packages=['maasivepy'],
    install_requires=['requests>=1.2.3'],
    entry_points={
        "console_scripts": [
            "maasivecommand=maasivepy.maasivecommand:main"
        ],
    }
)
