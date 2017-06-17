import json

import numpy as np
import pandas as pd
from dateutil.parser import parse

import DataSynthesizer.lib.utils as utils
from DataSynthesizer.lib.PrivBayes import greedy_bayes, construct_noisy_conditional_distributions


# TODO allow users to specify an attribute to be non-categorical.
# TODO allwo users to specify Null values.
class DataDescriber(object):
    """Analyze input dataset, then save the dataset description in a JSON file.

    Attributes:
        histogram_size: int, number of bins in histograms.
        threshold_of_categorical_variable: int, categorical variables have no more than "this number" distinct values.
        attribute_to_datatype: Dict, mappings of {attribute: datatype}, e.g., {"age": "int", "gender": "string"}
        dataset_description: Dict, a nested dictionary (equivalent to JSON) recording the mined dataset information.
        categorical_attributes: Set or List, e.g., {"gender", "nationality"}
        independent_attributes: Set or List, attributes that are excluded in BN construction.
        input_dataset: the dataset to be analyzed.
        bayesian_network: list of (child, (parent,)) in constructed BN.
    """

    def __init__(self, histogram_size=20, threshold_of_categorical_variable=10):
        self.histogram_size = histogram_size
        self.threshold_of_categorical_variables = threshold_of_categorical_variable
        self.dataset_description = {}
        self.attribute_to_datatype = {}
        self.categorical_attributes = set()
        self.independent_attributes = set()
        self.input_dataset = pd.DataFrame()
        self.bayesian_network = []
        self.encoded_dataset = pd.DataFrame()

        self.datatypes = {'int', 'float', 'datetime', 'string'}
        self.numerical_datatypes = {'int', 'float', 'datetime'}

    def describe_dataset_in_random_mode(self, dataset_file, categorical_attributes={}, seed=0):
        self.describe_dataset_in_independent_attribute_mode(dataset_file, epsilon=0.1,
                                                            categorical_attributes=categorical_attributes, seed=seed)

    def describe_dataset_in_independent_attribute_mode(self, dataset_file, epsilon=0.1,
                                                       attribute_to_datatype_dict={}, categorical_attributes={},
                                                       seed=0):
        utils.set_random_seed(seed)
        self.attribute_to_datatype = dict(attribute_to_datatype_dict)
        self.categorical_attributes = set(categorical_attributes)
        self.read_dataset_from_csv(dataset_file)
        self.get_dataset_meta_info()
        self.infer_attribute_datatypes()
        self.infer_domains()
        self.inject_laplace_noise_into_distribution_per_attribute(epsilon)

    def describe_dataset_in_correlated_attribute_mode(self, dataset_file, k=0, epsilon=0.1,
                                                      attribute_to_datatype_dict={}, categorical_attributes={}, seed=0):
        """Generate dataset description using correlated attribute mode.

        Users only need to call this function. It packages the rest functions.

        Args:
            dataset_file: string, directory and file name of the sensitive dataset as input in csv format.
            epsilon: float, a parameter in differential privacy.
            attribute_to_datatype_dict: Dict, mappings of {column_name: data_type}, e.g., {"gender": "string"}.
            categorical_attributes: Set or List, e.g., {"gender", "nationality"}
            seed: int or float, seeding the randomness.
        """

        self.describe_dataset_in_independent_attribute_mode(dataset_file, epsilon, attribute_to_datatype_dict,
                                                            categorical_attributes, seed)
        self.encoded_dataset = self.encode_dataset_into_interval_indices()
        self.bayesian_network = greedy_bayes(self.input_dataset[self.encoded_dataset.columns], k, epsilon)
        self.dataset_description['bayesian_network'] = self.bayesian_network
        self.dataset_description['conditional_probabilities'] = construct_noisy_conditional_distributions(
                                                                self.bayesian_network, self.encoded_dataset, epsilon)

    def read_dataset_from_csv(self, file_name=None):
        try:
            self.input_dataset = pd.read_csv(file_name)
        except (UnicodeDecodeError, NameError):
            self.input_dataset = pd.read_csv(file_name, encoding='latin1')

        # filter candidate key attributes and attributes with empty domain.
        for attribute in self.input_dataset:
            column_values = self.input_dataset[attribute].dropna()
            num_tuples = column_values.size
            num_unique_values = column_values.unique().size
            if (num_tuples == num_unique_values) or (num_tuples == 0):
                self.input_dataset.drop(attribute, axis=1, inplace=True)

    def get_dataset_meta_info(self):
        num_tuples, num_attributes = self.input_dataset.shape
        attribute_list = self.input_dataset.columns.tolist()
        meta_info = {"num_tuples": num_tuples, "num_attributes": num_attributes, "attribute_list": attribute_list}
        self.dataset_description['meta'] = meta_info

    def infer_attribute_datatypes(self):
        attributes_with_unspecified_datatype = set(self.input_dataset.columns) - set(self.attribute_to_datatype.keys())
        numeric_attributes = set(utils.get_numeric_column_list_from_dataframe(self.input_dataset))
        for attr in attributes_with_unspecified_datatype:
            current_column = self.input_dataset[attr].dropna()

            # current attribute is either int or float.
            if attr in numeric_attributes:
                if (current_column == current_column.astype(int)).all():
                    self.attribute_to_datatype[attr] = 'int'
                else:
                    self.attribute_to_datatype[attr] = 'float'

            # current attribute is either string or datetime.
            else:
                # Sample 20 values to test whether the elements of current attribute are of type datetime.
                tests = current_column.sample(20, replace=True).map(utils.is_datetime)
                if all(tests):
                    self.attribute_to_datatype[attr] = 'datetime'
                else:
                    self.attribute_to_datatype[attr] = 'string'

    def is_categorical(self, attribute):
        """Detect whether a column is categorical.
        
        A column is categorical if one of following conditions.
            (1) it is specified by user to be categorical
            (2) its domain is less than threshold_of_categorical_variables. 

        Args:
            attribute: string, attribute name.
        """
        if attribute in self.categorical_attributes:
            return True
        else:
            if self.input_dataset[attribute].dropna().unique().size <= self.threshold_of_categorical_variables:
                return True
            else:
                return False

    def infer_domain_of_numeric_attribute(self, attribute):
        datatype = self.attribute_to_datatype[attribute]
        column_values = self.input_dataset[attribute]
        column_dropna = column_values.dropna()

        # use timestamp to represent datetime
        if datatype == 'datetime':
            column_dropna = column_dropna.map(lambda x: parse(x).timestamp())

        is_categorical_attr = self.is_categorical(attribute)
        if is_categorical_attr:
            distribution = column_dropna.value_counts()
        else:
            distribution = column_dropna.value_counts(bins=self.histogram_size)

        distribution.sort_index(inplace=True)
        distribution_probabilities = utils.normalize_given_distribution(distribution)

        if is_categorical_attr:
            distribution_bins = np.array(distribution.index).tolist()
        else:
            distribution_bins = np.array(distribution.index.left).tolist()

        attribute_info = {'datatype': datatype,
                          'is_categorical': is_categorical_attr,
                          'min': float(column_dropna.min()),
                          'max': float(column_dropna.max()),
                          'distribution_bins': distribution_bins,
                          'distribution_probabilities': distribution_probabilities.tolist(),
                          'missing_rate': column_values.isnull().sum() / column_values.index.size}

        if datatype == 'int':
            attribute_info['min'] = int(column_dropna.min())
            attribute_info['max'] = int(column_dropna.max())

        return attribute_info

    def infer_domain_of_string_attribute(self, attribute):
        datatype = self.attribute_to_datatype[attribute]
        column_values = self.input_dataset[attribute]
        column_dropna = column_values.dropna()
        column_value_lengths = column_dropna.map(len)

        is_categorical_attribute = self.is_categorical(attribute)
        if is_categorical_attribute:
            distribution = column_dropna.value_counts()
        else:
            distribution = column_value_lengths.value_counts(bins=self.histogram_size)

        distribution.sort_index(inplace=True)
        distribution_probabilities = utils.normalize_given_distribution(distribution)

        attribute_info = {'datatype': datatype,
                          'is_categorical': is_categorical_attribute,
                          'min_length': int(column_value_lengths.min()),
                          'max_length': int(column_value_lengths.max()),
                          'distribution_bins': np.array(distribution.index).tolist(),
                          'distribution_probabilities': distribution_probabilities.tolist(),
                          'missing_rate': column_values.isnull().sum() / column_values.index.size}

        return attribute_info

    def infer_domains(self):
        """Infer the attribute domains.
        
        The domain of an attribute includes
            (1) is_categorical or not 
            (2) datatype 
            (3) [min, max] 
            (4) 1-D distribution
            (5) missing rate

        Args:
            attribute: str.
        """
        self.dataset_description['attribute_description'] = {}
        for attribute in self.input_dataset:
            datatype = self.attribute_to_datatype[attribute]
            if datatype in self.numerical_datatypes:
                attribute_info = self.infer_domain_of_numeric_attribute(attribute)
            else:
                attribute_info = self.infer_domain_of_string_attribute(attribute)
            self.dataset_description['attribute_description'][attribute] = attribute_info

    def inject_laplace_noise_into_distribution_per_attribute(self, epsilon=0.1):
        for attr in self.dataset_description['attribute_description'].keys():
            distribution = self.dataset_description['attribute_description'][attr]['distribution_probabilities']
            noisy_scale = 1 / (epsilon * self.input_dataset.shape[0])
            laplace_noises = np.random.laplace(0, scale=noisy_scale, size=len(distribution))
            noisy_distribution = np.asarray(distribution) + laplace_noises
            noisy_distribution = utils.normalize_given_distribution(noisy_distribution).tolist()
            self.dataset_description['attribute_description'][attr]['distribution_probabilities'] = noisy_distribution

    def encode_dataset_into_interval_indices(self):
        """Before constructing noisy distributions, encode dataset into binning indices."""
        encoded_dataset = self.input_dataset.copy()
        for attribute in self.input_dataset:
            attribute_info = self.dataset_description['attribute_description'][attribute]

            datatype = attribute_info['datatype']
            is_categorical_attribute = attribute_info['is_categorical']
            bins = attribute_info['distribution_bins']

            if datatype == 'string' and not is_categorical_attribute:
                encoded_dataset.drop(attribute, axis=1, inplace=True)
                # non-categorical string attributes are ignored in BN construction.
                continue
            elif datatype == 'datetime':
                encoded_dataset[attribute] = encoded_dataset[attribute].map(lambda x: parse(x).timestamp())

            if is_categorical_attribute:
                encoded_dataset[attribute] = encoded_dataset[~encoded_dataset[attribute].isnull()][
                    attribute].map(lambda x: bins.index(x))
            else:
                # the intervals are half-open, i.e., [1, 2)
                encoded_dataset[attribute] = encoded_dataset[~encoded_dataset[attribute].isnull()][
                    attribute].map(lambda x: bins.index([i for i in bins if i < x][-1]))

            # missing values are replaced with len(bins).
            encoded_dataset[attribute].fillna(value=len(bins), inplace=True)

        return encoded_dataset

    def save_dataset_description_to_file(self, file_name):
        with open(file_name, 'w') as outfile:
            json.dump(self.dataset_description, outfile, indent=4)

    def display_dataset_description(self):
        print(json.dumps(self.dataset_description, indent=4))


if __name__ == '__main__':
    # AdultIncome - reduced
    input_dataset_file = '../out/mock_input/adult_reduced.csv'
    dataset_description_file = '../out/AdultIncome/description_test.txt'
    synthetic_dataset_file = '../out/AdultIncome/output_test.csv'

    describer = DataDescriber()
    describer.describe_dataset_in_correlated_attribute_mode(input_dataset_file, k=2, epsilon=0.1)
    describer.save_dataset_description_to_file(dataset_description_file)
