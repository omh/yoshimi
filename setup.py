import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--cov', 'yoshimi']
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md')) as fp:
    README = fp.read()

with open(os.path.join(here, 'CHANGES.md')) as fp:
    CHANGES = fp.read()

requires = [
    'fanstatic>=1.0a4',
    'js.jquery',
    'css.pure',
    'passlib',
    'pyramid>=1.5a3',
    'pyramid_jinja2',
    'pyramid_tm',
    'sqlalchemy>=0.9.0',
    'wtforms',
    'zope.sqlalchemy',
]

tests_requires = [
    'mock',
    'pytest',
    'pytest-cov',
    'flake8',
    'psycopg2',
    'mysql-connector-python'
]

docs_extras = [
    'Sphinx',
]

dependency_links = [
    # for which==1.1.3py3 - needed by fanstatic
    "https://bitbucket.org/fanstatic/fanstatic/src/default/3rdparty/which/",
]

setup(
    name='yoshimi',
    version='0.1',
    description='yoshimi',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'Programming Language :: Python',
        "Framework :: Pyramid",
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    author='Ole Morten Halvorsen',
    author_email='olemortenh@gmail.com',
    url='http://github.com/omh/yoshimi',
    keywords='web wsgi pyramid cms',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_require=tests_requires,
    cmdclass={'test': PyTest},
    extras_require={
        'testing': tests_requires,
        'docs': docs_extras,
    },
    dependency_links=dependency_links,
    entry_points={
        'fanstatic.libraries': [
            'yoshimi_admin = yoshimi.admin.fanstatic:library',
        ],
    },
)
