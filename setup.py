from setuptools import setup, find_packages

setup(name='DataSynthesizer',
      version='0.0.1',
      description='Generate new data.',
      url='https://github.com/DataResponsibly/DataSynthesizer',
      author='DataResponsibly',
      author_email='',
      license='MIT',
      packages=find_packages(exclude=['tests']),
      python_requires='>=3.6'
     )