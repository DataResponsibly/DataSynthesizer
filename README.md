[![PyPi Shield](https://img.shields.io/pypi/v/DataSynthesizer.svg)](https://pypi.python.org/pypi/DataSynthesizer) [![Travis CI Shield](https://travis-ci.com/DataResponsibly/DataSynthesizer.svg?branch=master)](https://travis-ci.com/DataResponsibly/DataSynthesizer)

# DataSynthesizer

DataSynthesizer generates synthetic data that simulates a given dataset.

> It aims to facilitate the collaborations between data scientists and owners of sensitive data. It applies Differential Privacy techniques to achieve strong privacy guarantee.
>
> For more details, please refer to [DataSynthesizer: Privacy-Preserving Synthetic Datasets](docs/cr-datasynthesizer-privacy.pdf)

### Install DataSynthesizer

```bash
pip install DataSynthesizer
```

### Usage

##### Assumptions for the Input Dataset

1. The input dataset is a table in first normal form ([1NF](https://en.wikipedia.org/wiki/First_normal_form)).
2. When implementing differential privacy, DataSynthesizer injects noises into the statistics within **active domain** that are the values presented in the table.

##### Use [Jupyter Notebook](https://jupyter.org/install)

After installing DataSynthesizer and Jupyter Notebook, open and try the demos in `./notebooks/`

- [DataSynthesizer__random_mode.ipynb](notebooks/DataSynthesizer__random_mode.ipynb)
- [DataSynthesizer__independent_attribute_mode.ipynb](notebooks/DataSynthesizer__independent_attribute_mode.ipynb)
- [DataSynthesizer__correlated_attribute_mode.ipynb](notebooks/DataSynthesizer__correlated_attribute_mode.ipynb)

##### Use Web UI

DataSynthesizer can be executed with a Web-based UI .

```bash
# install Django
pip install django

# (optional) if DataSynthesizer is not installed
pip install DataSynthesizer

# go to the directory for webUI
cd DataSynthesizer/webUI/

# (optional) Django's way of propagating changes
python manage.py migrate

# run the server
python manage.py runserver
```

Then open a browser and visit http://127.0.0.1:8000/synthesizer/
