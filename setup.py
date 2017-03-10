from setuptools import setup, find_packages

setup(
    name='logbookclient',
    version='0.0.1',
    description='This is a python client for the PCDS logbook. It also contains the QT based grabber.',
    url='https://pswww.slac.stanford.edu/svn/psdmrepo/LogBookClient',
    author='Igor Gaponenko/Mikhail Dubrovin',
    author_email='gapon@slac.stanford.edu',
    license='EPICS license',
    classifiers=[
        'Development Status :: 4 - Beta'
        'Intended Audience :: SLAC PCDS ',
        'Topic :: Utilities',
        'License :: EPICS License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3'
    ],
    install_requires=[ 
        'requests',
        'simplejson',
        'MySQL-python',
        'six', 
    ],
    scripts=['LogBookClient/LogBookGrabber_qt'],
    packages=find_packages()
)
