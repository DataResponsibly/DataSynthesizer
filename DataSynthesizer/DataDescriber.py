import json
from typing import Dict, List, Union

from numpy import array_equal
from pandas import DataFrame, read_csv

from DataSynthesizer.datatypes.AbstractAttribute import AbstractAttribute
from DataSynthesizer.datatypes.DateTimeAttribute import is_datetime, DateTimeAttribute
from DataSynthesizer.datatypes.FloatAttribute import FloatAttribute
from DataSynthesizer.datatypes.IntegerAttribute import IntegerAttribute
from DataSynthesizer.datatypes.SocialSecurityNumberAttribute import is_ssn, SocialSecurityNumberAttribute
from DataSynthesizer.datatypes.StringAttribute import StringAttribute
from DataSynthesizer.datatypes.utils.DataType import DataType
from DataSynthesizer.lib import utils
from DataSynthesizer.lib.PrivBayes import greedy_bayes, construct_noisy_conditional_distributions


class DataDescriber:
    """Model input dataset, then save a description of the dataset into a JSON file.

    Attributes
    ----------
    histogram_bins : int or str
        Number of bins in histograms.
        If it is a string such as 'auto' or 'fd', calculate the optimal bin width by `numpy.histogram_bin_edges`.
    category_threshold : int
        Categorical variables have no more than "this number" of distinct values.
    null_values: str or list
        Additional strings to recognize as missing values.
        By default missing values already include {‘’, ‘NULL’, ‘N/A’, ‘NA’, ‘NaN’, ‘nan’}.
    attr_to_datatype : dict
        Dictionary of {attribute: datatype}, e.g., {"age": "Integer", "gender": "String"}.
    attr_to_is_categorical : dict
        Dictionary of {attribute: boolean}, e.g., {"gender":True, "age":False}.
    attr_to_is_candidate_key: dict
        Dictionary of {attribute: boolean}, e.g., {"id":True, "name":False}.
    data_description: dict
        Nested dictionary (equivalent to JSON) recording the mined dataset information.
    df_input : DataFrame
        The input dataset to be analyzed.
    attr_to_column : Dict
        Dictionary of {attribute: AbstractAttribute}
    bayesian_network : list
        List of [child, [parent,]] to represent a Bayesian Network.
    df_encoded : DataFrame
        Input dataset encoded into integers, taken as input by PrivBayes algorithm in correlated attribute mode.
    """

    def __init__(self, histogram_bins: Union[int, str] = 20, category_threshold=20, null_values=None):
        self.histogram_bins: Union[int, str] = histogram_bins
        self.category_threshold: int = category_threshold
        self.null_values = null_values

        self.attr_to_datatype: Dict[str, DataType] = None
        self.attr_to_is_categorical: Dict[str, bool] = None
        self.attr_to_is_candidate_key: Dict[str, bool] = None

        self.data_description: Dict = {}
        self.df_input: DataFrame = None
        self.attr_to_column: Dict[str, AbstractAttribute] = None
        self.bayesian_network: List = None
        self.df_encoded: DataFrame = None

    def describe_dataset_in_random_mode(self,
                                        dataset_file: str,
                                        attribute_to_datatype: Dict[str, DataType] = None,
                                        attribute_to_is_categorical: Dict[str, bool] = None,
                                        attribute_to_is_candidate_key: Dict[str, bool] = None,
                                        categorical_attribute_domain_file: str = None,
                                        numerical_attribute_ranges: Dict[str, List] = None,
                                        seed=0):
        attribute_to_datatype = attribute_to_datatype or {}
        attribute_to_is_categorical = attribute_to_is_categorical or {}
        attribute_to_is_candidate_key = attribute_to_is_candidate_key or {}
        numerical_attribute_ranges = numerical_attribute_ranges or {}

        if categorical_attribute_domain_file:
            categorical_attribute_to_domain = utils.read_json_file(categorical_attribute_domain_file)
        else:
            categorical_attribute_to_domain = {}

        utils.set_random_seed(seed)
        self.attr_to_datatype = {attr: DataType(datatype) for attr, datatype in attribute_to_datatype.items()}
        self.attr_to_is_categorical = attribute_to_is_categorical
        self.attr_to_is_candidate_key = attribute_to_is_candidate_key
        self.read_dataset_from_csv(dataset_file)
        self.infer_attribute_data_types()
        self.analyze_dataset_meta()
        self.represent_input_dataset_by_columns()

        for column in self.attr_to_column.values():
            attr_name = column.name
            if attr_name in categorical_attribute_to_domain:
                column.infer_domain(categorical_domain=categorical_attribute_to_domain[attr_name])
            elif attr_name in numerical_attribute_ranges:
                column.infer_domain(numerical_range=numerical_attribute_ranges[attr_name])
            else:
                column.infer_domain()

        # record attribute information in json format
        self.data_description['attribute_description'] = {}
        for attr, column in self.attr_to_column.items():
            self.data_description['attribute_description'][attr] = column.to_json()

    def describe_dataset_in_independent_attribute_mode(self,
                                                       dataset_file,
                                                       epsilon=0.1,
                                                       attribute_to_datatype: Dict[str, DataType] = None,
                                                       attribute_to_is_categorical: Dict[str, bool] = None,
                                                       attribute_to_is_candidate_key: Dict[str, bool] = None,
                                                       categorical_attribute_domain_file: str = None,
                                                       numerical_attribute_ranges: Dict[str, List] = None,
                                                       seed=0):
        self.describe_dataset_in_random_mode(dataset_file,
                                             attribute_to_datatype,
                                             attribute_to_is_categorical,
                                             attribute_to_is_candidate_key,
                                             categorical_attribute_domain_file,
                                             numerical_attribute_ranges,
                                             seed=seed)

        for column in self.attr_to_column.values():
            column.infer_distribution()

        self.inject_laplace_noise_into_distribution_per_attribute(epsilon)
        # record attribute information in json format
        self.data_description['attribute_description'] = {}
        for attr, column in self.attr_to_column.items():
            self.data_description['attribute_description'][attr] = column.to_json()

    def describe_dataset_in_correlated_attribute_mode(self,
                                                      dataset_file,
                                                      k=0,
                                                      epsilon=0.1,
                                                      attribute_to_datatype: Dict[str, DataType] = None,
                                                      attribute_to_is_categorical: Dict[str, bool] = None,
                                                      attribute_to_is_candidate_key: Dict[str, bool] = None,
                                                      categorical_attribute_domain_file: str = None,
                                                      numerical_attribute_ranges: Dict[str, List] = None,
                                                      seed=0):
        """Generate dataset description using correlated attribute mode.

        Parameters
        ----------
        dataset_file : str
            File name (with directory) of the sensitive dataset as input in csv format.
        k : int
            Maximum number of parents in Bayesian network.
        epsilon : float
            A parameter in Differential Privacy. Increase epsilon value to reduce the injected noises. Set epsilon=0 to turn
            off Differential Privacy.
        attribute_to_datatype : dict
            Dictionary of {attribute: datatype}, e.g., {"age": "Integer", "gender": "String"}.
        attribute_to_is_categorical : dict
            Dictionary of {attribute: boolean}, e.g., {"gender":True, "age":False}.
        attribute_to_is_candidate_key: dict
            Dictionary of {attribute: boolean}, e.g., {"id":True, "name":False}.
        categorical_attribute_domain_file: str
            File name of a JSON file of some categorical attribute domains.
        numerical_attribute_ranges: dict
            Dictionary of {attribute: [min, max]}, e.g., {"age": [25, 65]}
        seed : int or float
            Seed the random number generator.
        """
        self.describe_dataset_in_independent_attribute_mode(dataset_file,
                                                            epsilon,
                                                            attribute_to_datatype,
                                                            attribute_to_is_categorical,
                                                            attribute_to_is_candidate_key,
                                                            categorical_attribute_domain_file,
                                                            numerical_attribute_ranges,
                                                            seed)
        self.df_encoded = self.encode_dataset_into_binning_indices()
        if self.df_encoded.shape[1] < 2:
            raise Exception("Correlated Attribute Mode requires at least 2 attributes(i.e., columns) in dataset.")

        self.bayesian_network = greedy_bayes(self.df_encoded, k, epsilon / 2)
        self.data_description['bayesian_network'] = self.bayesian_network
        self.data_description['conditional_probabilities'] = construct_noisy_conditional_distributions(
            self.bayesian_network, self.df_encoded, epsilon / 2)

    def read_dataset_from_csv(self, file_name=None):
        try:
            self.df_input = read_csv(file_name, skipinitialspace=True, na_values=self.null_values)
        except (UnicodeDecodeError, NameError):
            self.df_input = read_csv(file_name, skipinitialspace=True, na_values=self.null_values,
                                     encoding='latin1')

        # Remove columns with empty active domain, i.e., all values are missing.
        attributes_before = set(self.df_input.columns)
        self.df_input.dropna(axis=1, how='all')
        attributes_after = set(self.df_input.columns)
        if len(attributes_before) > len(attributes_after):
            print(f'Empty columns are removed, including {attributes_before - attributes_after}.')

    def infer_attribute_data_types(self):
        attributes_with_unknown_datatype = set(self.df_input.columns) - set(self.attr_to_datatype)
        inferred_numerical_attributes = utils.infer_numerical_attributes_in_dataframe(self.df_input)

        for attr in attributes_with_unknown_datatype:
            column_dropna = self.df_input[attr].dropna()

            # current attribute is either Integer or Float.
            if attr in inferred_numerical_attributes:
                # TODO Comparing all values may be too slow for large datasets.
                if array_equal(column_dropna, column_dropna.astype(int, copy=False)):
                    self.attr_to_datatype[attr] = DataType.INTEGER
                else:
                    self.attr_to_datatype[attr] = DataType.FLOAT

            # current attribute is either String, DateTime, or SocialSecurityNumber.
            else:
                # Sample 20 values to test its data_type.
                samples = column_dropna.sample(20, replace=True)
                if all(samples.map(is_datetime)):
                    self.attr_to_datatype[attr] = DataType.DATETIME
                else:
                    if all(samples.map(is_ssn)):
                        self.attr_to_datatype[attr] = DataType.SOCIAL_SECURITY_NUMBER
                    else:
                        self.attr_to_datatype[attr] = DataType.STRING

    def analyze_dataset_meta(self):
        all_attributes = set(self.df_input.columns)

        # find all candidate keys.
        for attr in all_attributes - set(self.attr_to_is_candidate_key):
            self.attr_to_is_candidate_key[attr] = self.df_input[attr].is_unique

        candidate_keys = {attr for attr, is_key in self.attr_to_is_candidate_key.items() if is_key}

        # find all categorical attributes.
        for attr in all_attributes - set(self.attr_to_is_categorical):
            self.attr_to_is_categorical[attr] = self.is_categorical(attr)

        non_categorical_string_attributes = set()
        for attr, is_categorical in self.attr_to_is_categorical.items():
            if not is_categorical and self.attr_to_datatype[attr] is DataType.STRING:
                non_categorical_string_attributes.add(attr)

        attributes_in_BN = list(all_attributes - candidate_keys - non_categorical_string_attributes)
        non_categorical_string_attributes = list(non_categorical_string_attributes)

        self.data_description['meta'] = {"num_tuples": self.df_input.shape[0],
                                         "num_attributes": self.df_input.shape[1],
                                         "num_attributes_in_BN": len(attributes_in_BN),
                                         "all_attributes": self.df_input.columns.tolist(),
                                         "candidate_keys": list(candidate_keys),
                                         "non_categorical_string_attributes": non_categorical_string_attributes,
                                         "attributes_in_BN": attributes_in_BN}

    def is_categorical(self, attribute_name):
        """ Detect whether an attribute is categorical.

        Parameters
        ----------
        attribute_name : str
        """
        if attribute_name in self.attr_to_is_categorical:
            return self.attr_to_is_categorical[attribute_name]
        else:
            return self.df_input[attribute_name].dropna().unique().size <= self.category_threshold

    def represent_input_dataset_by_columns(self):
        self.attr_to_column = {}
        for attr in self.df_input:
            data_type = self.attr_to_datatype[attr]
            is_candidate_key = self.attr_to_is_candidate_key[attr]
            is_categorical = self.attr_to_is_categorical[attr]
            paras = (attr, is_candidate_key, is_categorical, self.histogram_bins, self.df_input[attr])
            if data_type is DataType.INTEGER:
                self.attr_to_column[attr] = IntegerAttribute(*paras)
            elif data_type is DataType.FLOAT:
                self.attr_to_column[attr] = FloatAttribute(*paras)
            elif data_type is DataType.DATETIME:
                self.attr_to_column[attr] = DateTimeAttribute(*paras)
            elif data_type is DataType.STRING:
                self.attr_to_column[attr] = StringAttribute(*paras)
            elif data_type is DataType.SOCIAL_SECURITY_NUMBER:
                self.attr_to_column[attr] = SocialSecurityNumberAttribute(*paras)
            else:
                raise Exception(f'The DataType of {attr} is unknown.')

    def inject_laplace_noise_into_distribution_per_attribute(self, epsilon=0.1):
        num_attributes_in_BN = self.data_description['meta']['num_attributes_in_BN']
        for column in self.attr_to_column.values():
            assert isinstance(column, AbstractAttribute)
            column.inject_laplace_noise(epsilon, num_attributes_in_BN)

    def encode_dataset_into_binning_indices(self):
        """Before constructing Bayesian network, encode input dataset into binning indices."""
        encoded_dataset = DataFrame()
        for attr in self.data_description['meta']['attributes_in_BN']:
            encoded_dataset[attr] = self.attr_to_column[attr].encode_values_into_bin_idx()
        return encoded_dataset

    def save_dataset_description_to_file(self, file_name):
        with open(file_name, 'w') as outfile:
            json.dump(self.data_description, outfile, indent=4)

    def display_dataset_description(self):
        print(json.dumps(self.data_description, indent=4))
