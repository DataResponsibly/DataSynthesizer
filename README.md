
# Usage of datafaker

> The demo.ipynb is a jupyter notebook for this file.

### Import two classes from datafaker

1. DatasetDestriber can infer the domain of each column in dataset.
2. SyntheticDataGenerator can generate synthetic data according to the dataset description.


```python
from datafaker import DatasetDestriber, SyntheticDataGenerator
```

### Data types
 The datafaker currently supports 4 basic data types.

| data type | example                   |
| --------- | ------------------------- |
| integer   | id, age, ...              |
| float     | score, rating, ...        |
| string    | first name, gender, ...   |
| datetime  | birthday, event time, ... |

The data types can be part of the input. If not, they will be inferred from the dataset.

### Data description format

The domain of data is described as follows.
- The "catagorical" indicates attributes with particular values, e.g., "gender", "nationality".
- Most domains are modeled by a histogram, except noncategorical "string".

| data type | categorical | min              | max              | values              | probabilities       | values count       | missing rate |
| --------- | ----------- | ---------------- | ---------------- | ------------------- | ------------------- | ------------------ | ------------ |
| int       | True/False  | min              | max              | x-axis in histogram | y-axis in histogram | #bins in histogram | missing rate |
| float     | True/False  | min              | max              | x-axis in histogram | y-axis in histogram | #bins in histogram | missing rate |
| string    | True        | min in length    | max in length    | x-axis in histogram | y-axis in histogram | #bins in histogram | missing rate |
| string    | False       | min in length    | max in length    | 0                   | 0                   | 0                  | missing rate |
| datetime  | True/False  | min in timestamp | max in timestamp | x-axis in histogram | y-axis in histogram | #bins in histogram | missing rate |

##### The directories for input and output files


```python
input_dataset_file = './raw_data/AdultIncomeData/adult.csv'
dataset_description_file = './output/description/AdultIncomeData_description.csv'
synthetic_data_file = './output/synthetic_data/AdultIncomeData_synthetic.csv'
```

##### Step 1: Initialize a DatasetDescriber


```python
describer = DatasetDestriber()
```

##### Step 2: Generate dataset description

- description1 is inferred by code.
- description2 also contains customization on datatypes and category indicators from the user.
  - "education-num" is of datat type "float".
  - "native-country" is not categrocial.
  - "age" is categorical.


```python
description1 = describer.get_dataset_description(file_name=input_dataset_file)
description2 = describer.get_dataset_description(file_name=input_dataset_file,
                                                 column_to_datatype_dict={'education-num': 'float'},
                                                 column_to_categorical_dict={'native-country':False,'age':True})
```

##### Step 3: save the dataset description


```python
describer.dataset_description.to_csv(dataset_description_file)
```

### Generate synthetic data

##### Step 1: Initialize a SyntheticDataGenerator.


```python
generator = SyntheticDataGenerator()
```

##### Step 2: Generate 10 rows in sysnthetic dataset

The values are sampled from the histograms in dataset description file.


```python
synthetic_dataset = generator.get_synthetic_data(dataset_description_file, N=10)
```

##### Step 3: Random missing

Random missing proportional to missing rates in dataset description.


```python
generator.random_missing_on_dataset_as_description()
```

##### Step 4: Save the synthetic dataset


```python
synthetic_dataset = generator.synthetic_dataset
synthetic_dataset.to_csv(synthetic_data_file)
```
