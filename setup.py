from setuptools import find_packages, setup


def read(path):
    with open(path, 'r') as f:
        return f.read()


long_description = read('README.md')

setup(
    name='ffq',
    version='0.0.1',
    url='https://github.com/sbooeshaghi/ffq',
    author='Sina Booeshaghi',
    author_email='alisina@caltech.edu',
    maintainer='Pachter Lab',
    maintainer_email='lpachter@caltech.edu',
    description='',  # noqa
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='',
    python_requires='>=3.6',
    license='MIT',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=read('requirements.txt').strip().split('\n'),
    entry_points={
        'console_scripts': ['ffq=ffq.main:main'],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Utilities',
    ],
)
