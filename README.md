# DataSynthesizer

### Usage

DataSynthesizer can generate a synthetic dataset from a sensitive one for release to public. It is developed in Python 3.6 and requires some third-party modules, including numpy, scipy, pandas, and dateutil.

Its usage is presented in the following Jupyter Notebooks,

- DataSynthesizer Usage (random mode).ipynb
- DataSynthesizer Usage (independent attribute mode).ipynb
- DataSynthesizer Usage (correlated attribute mode).ipynb

### Web-UI

There is also a web-UI for DataSynthesizer developed by Django. You can first open a terminal and  `cd`  to `[repo directory]/webUI/` , then try `python manage.py runserver`  to run a local server. The web-UI will be hosted at `http://127.0.0.1:8000/synthesizer/` .