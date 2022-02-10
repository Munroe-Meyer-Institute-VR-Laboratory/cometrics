from setuptools import setup
from ui_params import cometrics_version

with open('README.md') as f:
    readme = f.read()

setup(name='cometrics',
      version=cometrics_version,
      description='Clinical tool for coregistration of frequency and duration based behavior, physiological signals, '
                  'and video data. Session tracking features streamline multi-session clinical data recording.',
      long_description=readme,
      long_description_content_type="text/markdown",
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.8',
          'Topic :: ABA :: Data Collection :: Video :: Display'
      ],
      keywords='empatica aba behavioral-science video unmc mmi',
      url='https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics',
      author='Walker Arce (wsarce)',
      author_email='walkerarce@unmc.edu',
      license='MIT',
      packages=['cometrics'],
      install_requires=[
          'setuptools',
          'opencv-python',
          'pynput',
          'tkvideoutils',
          'pillow',
          'numpy',
          'WMI',
          'PyYAML',
          'matplotlib',
          'pyEmpatica',
          'openpyxl',
      ],
      include_package_data=True,
      zip_safe=False
      )
