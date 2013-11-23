import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md')) as fp:
    README = fp.read()

with open(os.path.join(here, 'CHANGES.md')) as fp:
    CHANGES = fp.read()

requires = [
    'fanstatic',
    'js.jquery',
    'css.pure',
    'passlib',
    'pyramid==1.5a2',
    'pyramid_mako',
    'pyramid_tm',
    'sqlalchemy>=0.9.0b1',
    'wtforms',
    'zope.sqlalchemy',
]

test_requires = [
    'nose',
    'psycopg2',
    'mysql-connector-python'
],

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
    tests_require=test_requires,
    entry_points={
        'fanstatic.libraries': [
            'yoshimi_admin = yoshimi.admin.fanstatic:library',
        ],
    },
)
