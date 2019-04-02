# DataSynthesizer

### Usage

DataSynthesizer can generate a synthetic dataset from a sensitive one for release to public. It is developed in Python 3.6 and requires some third-party modules, including numpy, scipy, pandas, and dateutil.

Its usage is presented in the following Jupyter Notebooks,

- DataSynthesizer Usage (random mode).ipynb
- DataSynthesizer Usage (independent attribute mode).ipynb
- DataSynthesizer Usage (correlated attribute mode).ipynb

### Assumptions for Input Dataset

1. The input dataset is a table in first normal form (1NF).
2. The active domain is the domain for each attribute of the table. When implementing differential privacy,  DataSynthesizer injects noises into the statistics within active domain.

### Web-based UI

There is a web-based UI in `webUI/`  directory, which is a self-contained Django project. Here is a simple way to run it on your machine.

##### Step 1 Install Python 3 and necessary packages

- [Miniconda](http://conda.pydata.org/miniconda.html) is recommended as the Python distribution. It also contains a user-friendly package manager "conda".  Note that DataSynthesizer is Python 3 based.
- After installing it on your machine, run `conda install numpy pandas scikit-learn matplotlib seaborn jupyter django`  in terminal to install the packages.

##### Step 2 Run web-based UI

- Clone or download this repo to your local machine.
- Open a terminal and  `cd [repo directory]/webUI/` 
- Run `PYTHONPATH=../DataSynthesizer python manage.py runserver` . The web-based UI will be hosted at `http://127.0.0.1:8000/synthesizer/` .

### License

Copyright <2018> <dataresponsibly.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
