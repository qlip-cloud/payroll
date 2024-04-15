from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in qp_payroll/__init__.py
from qp_payroll import __version__ as version

setup(
	name='qp_payroll',
	version=version,
	description='Designer integration with Qlip',
	author='Frappé',
	author_email='adolfo.hernandez@mentum.group',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
