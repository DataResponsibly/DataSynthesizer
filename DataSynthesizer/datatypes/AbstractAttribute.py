from abc import ABCMeta, abstractmethod
from bisect import bisect_right
from random import uniform
from typing import List, Union

import numpy as np
from numpy.random import choice
from pandas import Series

from DataSynthesizer.datatypes.utils import DataType
from DataSynthesizer.lib import utils


class AbstractAttribute(object):
    __metaclass__ = ABCMeta

    def __init__(self, name: str, is_candidate_key, is_categorical, histogram_size: Union[int, str], data: Series):
        self.name = name
        self.is_candidate_key = is_candidate_key
        self.is_categorical = is_categorical
        self.histogram_size: Union[int, str] = histogram_size
        self.data: Series = data
        self.data_dropna: Series = self.data.dropna()
        self.missing_rate: float = (self.data.size - self.data_dropna.size) / (self.data.size or 1)

        self.is_numerical: bool = None
        self.data_type: DataType = None
        self.min = None
        self.max = None
        self.distribution_bins: np.ndarray = None
        self.distribution_probabilities: np.ndarray = None

    @abstractmethod
    def infer_domain(self, categorical_domain: List = None, numerical_range: List = None):
        """Infer categorical_domain, including min, max, and 1-D distribution.

        """
        if categorical_domain:
            self.min = min(categorical_domain)
            self.max = max(categorical_domain)
            self.distribution_bins = np.array(categorical_domain)
        elif numerical_range:
            self.min, self.max = numerical_range
            self.distribution_bins = np.array([self.min, self.max])
        else:
            self.min = float(self.data_dropna.min())
            self.max = float(self.data_dropna.max())
            if self.is_categorical:
                self.distribution_bins = self.data_dropna.unique()
            else:
                self.distribution_bins = np.array([self.min, self.max])

        self.distribution_probabilities = np.full_like(self.distribution_bins, 1 / self.distribution_bins.size)

    @abstractmethod
    def infer_distribution(self):
        if self.is_categorical:
            distribution = self.data_dropna.value_counts()
            for value in set(self.distribution_bins) - set(distribution.index):
                distribution[value] = 0
            distribution.sort_index(inplace=True)
            self.distribution_probabilities = utils.normalize_given_distribution(distribution)
            self.distribution_bins = np.array(distribution.index)
        else:
            distribution = np.histogram(self.data_dropna, bins=self.histogram_size, range=(self.min, self.max))
            self.distribution_bins = distribution[1][:-1]  # Remove the last bin edge
            self.distribution_probabilities = utils.normalize_given_distribution(distribution[0])

    def inject_laplace_noise(self, epsilon, num_valid_attributes):
        if epsilon > 0:
            sensitivity = 2 / self.data.size
            privacy_budget = epsilon / num_valid_attributes
            noise_scale = sensitivity / privacy_budget
            laplace_noises = np.random.laplace(0, scale=noise_scale, size=len(self.distribution_probabilities))
            noisy_distribution = self.distribution_probabilities + laplace_noises
            self.distribution_probabilities = utils.normalize_given_distribution(noisy_distribution)

    def encode_values_into_bin_idx(self):
        """Encode values into bin indices for Bayesian Network construction.

        """
        if self.is_categorical:
            value_to_bin_idx = {value: idx for idx, value in enumerate(self.distribution_bins)}
            encoded = self.data.map(lambda x: value_to_bin_idx[x], na_action='ignore')
        else:
            encoded = self.data.map(lambda x: bisect_right(self.distribution_bins, x) - 1, na_action='ignore')

        encoded.fillna(len(self.distribution_bins), inplace=True)
        return encoded.astype(int, copy=False)

    def to_json(self):
        """Encode attribution information in JSON format / Python dictionary.

        """
        return {"name": self.name,
                "data_type": self.data_type.value,
                "is_categorical": self.is_categorical,
                "is_candidate_key": self.is_candidate_key,
                "min": self.min,
                "max": self.max,
                "missing_rate": self.missing_rate,
                "distribution_bins": self.distribution_bins.tolist(),
                "distribution_probabilities": self.distribution_probabilities.tolist()}

    @abstractmethod
    def generate_values_as_candidate_key(self, n):
        """When attribute should be a candidate key in output dataset.

        """
        return np.arange(n)

    def sample_binning_indices_in_independent_attribute_mode(self, n):
        """Sample an array of binning indices.

        """
        return Series(choice(len(self.distribution_probabilities), size=n, p=self.distribution_probabilities))

    @abstractmethod
    def sample_values_from_binning_indices(self, binning_indices):
        """Convert binning indices into values in domain. Used by both independent and correlated attribute mode.

        """
        return binning_indices.apply(lambda x: self.uniform_sampling_within_a_bin(x))

    def uniform_sampling_within_a_bin(self, bin_idx: int):
        num_bins = len(self.distribution_bins)
        if bin_idx == num_bins:
            return np.nan
        elif self.is_categorical:
            return self.distribution_bins[bin_idx]
        elif bin_idx < num_bins - 1:
            return uniform(self.distribution_bins[bin_idx], self.distribution_bins[bin_idx + 1])
        else:
            # sample from the last interval where the right edge is missing in self.distribution_bins
            neg_2, neg_1 = self.distribution_bins[-2:]
            return uniform(neg_1, self.max)
