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

##### Use Jupyter Notebook

After installing DataSynthesizer and [Jupyter Notebook](https://jupyter.org/install), open and try the demos in `./notebooks/`

- [DataSynthesizer__random_mode.ipynb](notebooks/DataSynthesizer__random_mode.ipynb)
- [DataSynthesizer__independent_attribute_mode.ipynb](notebooks/DataSynthesizer__independent_attribute_mode.ipynb)
- [DataSynthesizer__correlated_attribute_mode.ipynb](notebooks/DataSynthesizer__correlated_attribute_mode.ipynb)

##### Use Web UI

The [dataResponsiblyUI](https://github.com/DataResponsibly/dataResponsiblyUI) is a Django project that includes DataSynthesizer. Please follow the steps in [Run the Web UIs locally](https://github.com/DataResponsibly/dataResponsiblyUI#run-the-web-uis-locally) and run DataSynthesizer by visiting http://127.0.0.1:8000/synthesizer in a browser.

