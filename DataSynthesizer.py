import numpy as np
import pandas as pd
from dateutil.parser import parse
from scipy.stats import gaussian_kde
from faker import Faker
from datetime import datetime

# TODO add differential privace for description
# TODO Two-column correlation

class DataDestriber(object):
    """Generate a description of the input dataset

    Attributes:
        histogram_size: Number of bins by default in histograms.
        categorical_threshold: Categorical values are repeated at least "categorical_threshold" times in average.
        column_to_datatype: Mappings of {column_name: data_type}, e.g., {"age": "int", "gender": "string"}
        column_to_categorical: Mappings of {column_name: categorical}, e.g., {"age": False, "gender": True}
        dataset_description: A dataframe of statistics of the dataset.
        input_dataset: the dataset to be described.
    """

    def __init__(self, histogram_size=20, categorical_threshold=10):
        self.histogram_size = histogram_size
        self.categorical_threshold = categorical_threshold

    def describe_dataset(self, file_name=None, column_to_datatype_dict={}, column_to_categorical_dict={}):
        """A comprehensive function to generate dataset description.

        Users only need to call this function. It packages the rest functions.

        Args:
            file_name: The directory and file name of the input dataset in csv format.
            column_to_datatype_dict: A dict of {column_name: datatype} for a subset of columns, e.g., {"age": "int"}
            column_to_categorical_dict: A dict of {column_name: categroical} for a subset of columns, e.g., {"gender": True}
        """
        self.dataset_description = pd.DataFrame(columns=['data type', 'categorical', 'min', 'max', 'values',
                                                         'value counts', 'histogram size', 'missing rate'])
        self.dataset_description.index.rename('column', inplace=True)

        self.column_to_datatype = dict(column_to_datatype_dict)
        self.column_to_categorical = dict(column_to_categorical_dict)
        self.read_csv(file_name)
        self.infer_column_data_types()
        self.infer_domains()

    def read_csv(self, file_name=None):
        try:
            self.input_dataset = pd.read_csv(file_name)
        except (UnicodeDecodeError, NameError):
            self.input_dataset = pd.read_csv(file_name, encoding='latin1')

    def infer_column_data_types(self):
        columns_of_unspecified_datatype = set(self.input_dataset.columns) - set(self.column_to_datatype.keys())
        statistics = self.input_dataset.dropna().describe()
        for col in columns_of_unspecified_datatype:
            current_column = self.input_dataset[col].dropna()

            # this column is numerical
            if col in statistics:
                if (current_column == current_column.astype(int)).all():
                    self.column_to_datatype[col] = 'int'
                else:
                    self.column_to_datatype[col] = 'float'

            # this column is of string or datetime.
            else:
                if self.is_date(current_column.iloc[0]):
                    self.column_to_datatype[col] = 'datetime'
                else:
                    self.column_to_datatype[col] = 'string'

    def is_date(self, date_string):
        try:
            parse(date_string)
            return True
        except ValueError:
            return False

    def is_categorical(self, data_type, unique_values_size, column_size):
        """Detect whether a column is categorical.

        A column is categorical if there are only a few disctince values (less than histogram size). If the column is of type "string", it is also categorical when the values are repeated at least "categorical_threshold" times in average. So that attributes such as languages and countries are indicated as categorical when "categorical_threshold" is set properly.

        Args:
            data_type: The data type of the column.
            unique_values_size: Number of distinct values.
            column_size: Lenghth of the column.
        """
        if unique_values_size < self.histogram_size:
            return True
        elif data_type == 'string' and unique_values_size*self.categorical_threshold < column_size:
            return True
        else:
            return False

    def infer_domains(self):

        for col in self.input_dataset:
            data_type = self.column_to_datatype[col]
            current_column = self.input_dataset[col].dropna()

            if col in self.column_to_categorical:
                categorical_boolean = self.column_to_categorical[col]
            else:
                categorical_boolean = self.is_categorical(data_type, current_column.unique().size, current_column.size)

            if categorical_boolean:
                distribution = current_column.value_counts()
                if data_type == 'string':
                    current_column = current_column.map(len)
                self.dataset_description.loc[col] = [data_type,
                                                     categorical_boolean,
                                                     current_column.min(),
                                                     current_column.max(),
                                                     list(distribution.index),
                                                     list(distribution.values),
                                                     len(distribution),
                                                     self.input_dataset[col].isnull().sum() / self.input_dataset[col].size]

            else:

                # use timestamp to represent datetime
                if data_type == 'datetime':
                    current_column = current_column.map(lambda x: parse(x).timestamp())
                elif data_type == 'string':
                    current_column = current_column.map(len)

                distribution = current_column.value_counts(bins=self.histogram_size)
                self.dataset_description.loc[col] = [data_type,
                                                     categorical_boolean,
                                                     current_column.min(),
                                                     current_column.max(),
                                                     list(distribution.index),
                                                     list(distribution.values),
                                                     len(distribution),
                                                     self.input_dataset[col].isnull().sum() / self.input_dataset[col].size]

class DataGenerator(object):
    """Generate synthetic data given a dataset description file.

    Attributes:
        fake: A fake value generator imported from a module named fake, supporting fake names, addresses, birthdays, etc.

    """

    def __init__(self):
        self.fake = Faker()

    def set_random_seed(self, seed=0):
        np.random.seed(seed)

    def generate_synthetic_dataset(self, file_name=None, N=20, epsilon=0.1, uniform_columns={}, seed=0):
        """A comprehensive function to generate synthetic dataset

        Args:
            file_name: The directory and file name of the dataset description file.
            N: Number of rows to generate.
            uniform_columns: Set of columns that should be sampled uniformly from the domain.
            seed: Seed for the sampling process, so that the sampling is predictable.
        """
        self.set_random_seed(seed)
        self.read_data_description(file_name)
        self.differential_privacy(epsilon)
        self.sample_synthetic_dataset(N, uniform_columns)

    def generate_uniform_random_dataset(self, file_name=None, N=20):
        """ Generate a totally random dataset, where values in each column are sampled uniformly from the domain of [min, max]. """
        self.read_data_description(file_name)
        self.sample_synthetic_dataset(N, uniform_columns=self.dataset_description.index.values)

    def read_data_description(self, file_name=None):
        self.dataset_description = pd.read_csv(file_name, index_col='column')

    def differential_privacy(self, epsilon=0.1):
        """ Apply differential privacy to values counts and missing counts in histograms. """
        for col, description in self.dataset_description.iterrows():

            value_counts = np.array(eval(description['value counts']))
            missing_counts = value_counts.sum() / (1 - description['missing rate']) * description['missing rate']

            value_counts = value_counts + np.random.laplace(0, 1/epsilon, value_counts.size)
            value_counts[value_counts < 1] = 1

            missing_counts += np.random.laplace(0, 1/epsilon)
            if missing_counts < 0:
                missing_counts = 0
            elif missing_counts > value_counts.sum():
                missing_counts = value_counts.sum()

            self.dataset_description.loc[col, 'value counts'] = str(value_counts.tolist())
            self.dataset_description.loc[col, 'missing rate'] = missing_counts / value_counts.sum()


    def sample_synthetic_dataset(self, N=20, uniform_columns={}):
        self.synthetic_dataset = pd.DataFrame(columns=self.dataset_description.index.values)
        for col, column_description in self.dataset_description.iterrows():
            data_type = column_description['data type']

            if col in uniform_columns:
                mode = 'uniform'
            else:
                mode = 'histogram'

            if column_description['categorical']:
                self.generate_categorical_column(col, column_description, N, mode)
            elif data_type == 'int':
                self.generate_int_column(col, column_description, N, mode)
            elif data_type == 'float':
                self.generate_float_column(col, column_description, N, mode)
            elif data_type == 'datetime':
                self.generate_datetime_column(col, column_description, N, mode)
            elif data_type == 'string':
                self.generate_string_column(col, column_description, N, mode)

    def sample_from_histogram(self, column_description, N=20):
        values = eval(column_description['values'])
        probabilities = np.array(eval(column_description['value counts']))
        probabilities = probabilities / probabilities.sum()
        return np.random.choice(values, size=N, p=probabilities)

    def sample_from_kde(self, column_description, N=20):
        """Kernel-density estimate using Gaussian kernels to sample continuously from the histograms"""
        kde = gaussian_kde(self.sample_from_histogram(column_description, N=1000000))
        candidate_samples = np.array([])
        while True:
            # Select samples that are between min and max values of current column
            new_samples = kde.resample(N)[0].flatten()
            new_samples = new_samples[np.where((column_description['min'] < new_samples)&
                                               (new_samples < column_description['max']))]
            candidate_samples = np.append(candidate_samples, new_samples)
            if candidate_samples.size >= N:
                return candidate_samples[:N]

    def generate_categorical_column(self, col=None, column_description=None, N=20, mode='histogram'):
        if mode == 'uniform':
            self.synthetic_dataset[col] = np.random.choice(eval(column_description['values']), size=N)
        elif mode == 'histogram':
            self.synthetic_dataset[col] = self.sample_from_histogram(column_description, N)
        else:
            raise RuntimeError('The parameter "mode" should be either "histogram" or "uniform".')

    def generate_int_column(self, col=None, column_description=None, N=20, mode='histogram'):
        if mode == 'uniform':
            self.synthetic_dataset[col] = np.random.randint(column_description['min'], column_description['max']+1, N)
        elif mode == 'histogram':
            self.synthetic_dataset[col] = self.sample_from_kde(column_description, N).astype(int)
        else:
            raise RuntimeError('The parameter "mode" should be either "histogram" or "uniform".')

    def generate_float_column(self, col=None, column_description=None, N=20, mode='histogram'):
        if mode == 'uniform':
            self.synthetic_dataset[col] = np.random.uniform(column_description['min'], column_description['max'], N)
        elif mode == 'histogram':
            self.synthetic_dataset[col] = self.sample_from_kde(column_description, N)
        else:
            raise RuntimeError('The parameter "mode" should be either "histogram" or "uniform".')

    def generate_datetime_column(self, col=None, column_description=None, N=20, mode='histogram'):
        if mode == 'uniform':
            datetime_column = np.random.uniform(column_description['min'], column_description['max'], N)
        elif mode == 'histogram':
            datetime_column = self.sample_from_kde(column_description, N)
        else:
            raise RuntimeError('The parameter "mode" should be either "histogram" or "uniform".')

        self.synthetic_dataset[col] = datetime_column.map(lambda x: datetime.utcfromtimestamp(x)
                                                              .strftime("%Y-%m-%d %H:%M:%S.%f+00:00 (UTC)"))


    def generate_string_column(self, col=None, column_description=None, N=20, mode='uniform'):
        min_chars, max_chars = column_description['min'], column_description['max']
        self.synthetic_dataset[col] = self.synthetic_dataset[col].map(lambda x: self.fake.pystr(min_chars, max_chars))

    def random_missing_on_dataset_as_description(self):
        for col, column_description in self.dataset_description.iterrows():
            missing = column_description['missing rate']
            self.random_missing_on_column(col, missing)

    def random_missing_on_columns(self, columns=[], missing_rates=[]):
        for col, missing in zip(columns, missing_rates):
            self.random_missing_on_column(col, missing)

    def random_missing_on_column(self, col=None, missing=0):
        """Missing some values randomly.

        Given the column name and missing rate, first compute the number of missing values #miss = size(column)*missing, then randomly select #miss indices in the column and set the values of these indices to NAN.

        Args:
            col: column name.
            missing: missing rate.
        """
        current_column = self.synthetic_dataset[col]
        missing_idx = np.random.choice(current_column.index, size=int(missing*current_column.size), replace=False)
        self.synthetic_dataset.loc[missing_idx, col] = np.nan