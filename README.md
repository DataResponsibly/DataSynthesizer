
# Usage of DataSynthesizer

> The demo.ipynb is a Jupyter Notebook of ReadMe.
>
> DataSynthesizer is developed in Python 3.5.2 and with some third-party modules, including
>
> - Numpy, Scipy, Pandas, dateutil (available in Anaconda 4.2.0)
> - faker https://github.com/joke2k/faker

Given a private dataset, DataSynthesizer can generate a synthetic dataset for release to public. It infers the data types and domains for the attributes in dataset. Histograms are used to model the distribution of each attribute. Synthetic dataset is sampled from the histograms or sampled uniformly from the inferred domains.

## Data types
 The DataSynthesizer currently supports 4 basic data types.

| data type | example                   |
| --------- | ------------------------- |
| integer   | id, age, ...              |
| float     | score, rating, ...        |
| string    | first name, gender, ...   |
| datetime  | birthday, event time, ... |

## Data description format

The domain of an attribute is as follows.
- The "catagorical" indicates attributes with particular values, e.g., "gender", "nationality".
- Domains are modeled by histograms, except noncategorical "string".

| data type | categorical | min              | max              | values              | probabilities       | values count       | missing rate |
| --------- | ----------- | ---------------- | ---------------- | ------------------- | ------------------- | ------------------ | ------------ |
| int       | True/False  | min              | max              | x-axis in histogram | y-axis in histogram | #bins in histogram | missing rate |
| float     | True/False  | min              | max              | x-axis in histogram | y-axis in histogram | #bins in histogram | missing rate |
| string    | True        | min in length    | max in length    | x-axis in histogram | y-axis in histogram | #bins in histogram | missing rate |
| string    | False       | min in length    | max in length    | 0                   | 0                   | 0                  | missing rate |
| datetime  | True/False  | min in timestamp | max in timestamp | x-axis in histogram | y-axis in histogram | #bins in histogram | missing rate |

##### Step 0: Import DataDestriber and DataGenerator from DataSynthesizer


```python
from DataSynthesizer import DataDestriber, DataGenerator
```


```python
# Directories of input and output files
input_dataset_file = './raw_data/AdultIncomeData/adult.csv'
dataset_description_file = './output/description/AdultIncomeData_description.csv'
synthetic_dataset_file = './output/synthetic_data/AdultIncomeData_synthetic.csv'
```

##### Step 1: Initialize a DatasetDescriber


```python
describer = DataDestriber()
```

##### Step 2: Generate dataset description

The dataset description is inferred by code, while users can also customize the data types and categorical indicators, e.g.,
- "education-num" is of type "float".
- "native-country" is not categrocial.
- "age" is categorical.


```python
describer.describe_dataset(file_name=input_dataset_file,
                           column_to_datatype_dict={'education-num': 'float'},
                           column_to_categorical_dict={'native-country':False,'age':True})
```

##### Step 3: Get the dataset description

The dataset description is


```python
describer.dataset_description
```

##### Step 4: save the dataset description


```python
describer.dataset_description.to_csv(dataset_description_file)
```

### Generate synthetic data

##### Step 5: Initialize a DataGenerator.


```python
generator = DataGenerator()
```

##### Step 6: Generate sysnthetic dataset

By default, the data is sampled from the histograms in dataset description. But users can make some columns sample uniformly in doamin of [min, max].

> generator.generate_uniform_random_dataset(dataset_description_file, N=10) # will generate a totoally random dataset.

Here the example is to generate 10 rows in synthetic datset, where "age" and "education" are sampled uniformly.


```python
generator.generate_synthetic_dataset(dataset_description_file, N=10, uniform_columns={'age', 'education'})
```

##### Step 7: Random missing

Remove values of a given column randomly, e.g., removing 60% of age values.


```python
generator.random_missing_on_column('age', 0.6)
```

##### Step 8: Save the synthetic dataset


```python
generator.synthetic_dataset.to_csv(synthetic_dataset_file, index=False)
```
