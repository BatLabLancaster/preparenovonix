import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

desc = "Clean and add extra information to data " + \
    "produced by the battery cyclers from Novonix."

setuptools.setup(
    name='preparenovonix',
    version='1.0.0',
    py_modules=['preparenovonix'],
    description=desc,
    long_description=long_description,
    url="https://github.com/BatLabLancaster/preparenovonix",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
