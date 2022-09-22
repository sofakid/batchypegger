from setuptools import setup, find_packages
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read()
setup(
    name = 'batchypegger',
    version = '0.5.1',
    author = 'Lucas',
    author_email = 'lucas@example.com',
    license = 'MIT',
    description = 'apply ffmpeg in a batchy way',
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = 'https://github.com/sofakid/batchypegger',
    py_modules = ['batchypegger'],
    packages = find_packages(),
    install_requires = [requirements],
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
    ],
    entry_points = '''
        [console_scripts]
        batchypegger=batchypegger:main
    '''
)