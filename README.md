# DataSynthesizer

### Usage

DataSynthesizer can generate a synthetic dataset from a sensitive one for release to public. It is developed in Python 3 and requires some third-party modules, such as numpy, pandas, and python-dateutil.

Its usage is presented in the following Jupyter Notebooks,

- DataSynthesizer Usage (random mode).ipynb
- DataSynthesizer Usage (independent attribute mode).ipynb
- DataSynthesizer Usage (correlated attribute mode).ipynb

### Assumptions for Input Dataset

1. The input dataset is a table in first normal form (1NF).
2. When implementing differential privacy,  DataSynthesizer injects noises into the statistics within **active domain** that are the values presented in the table.

### Install DataSynthesizer

Step 1 Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) for Python 3.

Step 2 Download DataSynthesizer.

```bash
git clone https://github.com/DataResponsibly/DataSynthesizer
```

Step 3 Install DataSynthesizer.

```bash
cd DataSynthesizer  # go to the DataSynthesizer repository that is just downloaded
conda env create -f environment.yml
```

### Run DataSynthesizer

DataSynthesizer can be executed by both Jupyter Notebooks and a web-based UI.

Step 1 Activate this environment for DataSynthesizer.

```bash
conda activate DataSynthesizer
```

Step 2

For Jupyter Notebooks, run `juypyter notebook` in terminal.

For web-based UI

```bash
cd DataSynthesizer/webUI/
PYTHONPATH=../DataSynthesizer python manage.py runserver
```

Then the web-based UI is hosted at http://127.0.0.1:8000/synthesizer/

### License

Copyright <2018> <dataresponsibly.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
