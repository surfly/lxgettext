from setuptools import setup, find_packages

VERSION = "0.2.0"

setup(
    name="lxgettext",
    version=VERSION,
    description="Extract strings wrapped in gettext('...')",
    keywords="gettext i18n l10n xgettext",
    author="Yauhen Shulitski",
    author_email="yauhen@surfly.com",
    url="https://github.com/surfly/lxgettext",
    license="BSD",
    test_suite="tests",
    install_requires=["polib==1.0.8"],
    entry_points={
        "console_scripts": [
            "lxgettext = lxgettext.lxgettext:main",
            "lpo2json = lxgettext.lpo2json:main"
        ]
    },
    packages=find_packages(exclude=["tests"])
)
