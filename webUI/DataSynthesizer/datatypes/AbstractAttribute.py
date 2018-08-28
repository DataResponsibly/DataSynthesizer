import bisect
from abc import ABCMeta, abstractmethod
from random import uniform

import numpy as np
import pandas as pd
from numpy.random import choice

from DataSynthesizer.lib import utils


class AbstractAttribute(object):
    __metaclass__ = ABCMeta

    def __init__(self, name, is_candidate_key=False, is_categorical=False, histogram_size=20):
        self.name = name
        self.is_candidate_key = is_candidate_key
        self.is_categorical = is_categorical
        self.histogram_size = histogram_size
        self.is_numerical = True
        self.data_type = None
        self.missing_rate = 0
        self.min = 0
        self.max = 0
        self.distribution_bins = []
        self.distribution_probabilities = []
        self.encoded = None
        self.data = None
        self.data_dropna = None

    @abstractmethod
    def infer_domain(self, column):
        """ Infer domain, including min, max, and 1-D distribution."""
        assert isinstance(column, pd.Series)
        self.data = column
        self.data_dropna = self.data.dropna()
        self.missing_rate = (self.data.size - self.data_dropna.size) / self.data.size
        self.min = float(self.data_dropna.min())
        self.max = float(self.data_dropna.max())

        if self.is_categorical:
            distribution = self.data_dropna.value_counts()
            distribution.sort_index(inplace=True)
            self.distribution_probabilities = utils.normalize_given_distribution(distribution).tolist()
            self.distribution_bins = np.array(distribution.index).tolist()
        else:
            distribution = np.histogram(self.data_dropna, bins=self.histogram_size)
            self.distribution_probabilities = utils.normalize_given_distribution(distribution[0]).tolist()
            bins = distribution[1][:-1].tolist()
            bins[0] = bins[0] - 0.001 * (bins[1] - bins[0])
            self.distribution_bins = bins

    def inject_laplace_noise(self, epsilon=0.1, num_valid_attributes=10):
        if epsilon > 0:
            noisy_scale = num_valid_attributes / (epsilon * self.data.size)
            laplace_noises = np.random.laplace(0, scale=noisy_scale, size=len(self.distribution_probabilities))
            noisy_distribution = np.asarray(self.distribution_probabilities) + laplace_noises
            self.distribution_probabilities = utils.normalize_given_distribution(noisy_distribution).tolist()

    def encode_values_into_binning_indices(self):
        """ Encode values into binning indices for distribution modeling."""
        dropna_index = self.data_dropna.index
        bins = self.distribution_bins
        self.encoded = self.data.copy()
        assert isinstance(self.encoded, pd.Series)

        if self.is_categorical:
            self.encoded[dropna_index] = self.data_dropna.map(lambda x: bins.index(x))
        else:
            self.encoded[dropna_index] = self.data_dropna.map(lambda x: bisect.bisect_left(bins, x) - 1)

        self.encoded.fillna(value=len(bins), inplace=True)
        return self.encoded

    def to_json(self):
        """ Encode attribution information in JSON / Python dictionary. """
        return {"name": self.name,
                "data_type": self.data_type.value,
                "is_categorical": self.is_categorical,
                "is_candidate_key": self.is_candidate_key,
                "min": self.min,
                "max": self.max,
                "missing_rate": self.missing_rate,
                "distribution_bins": self.distribution_bins,
                "distribution_probabilities": self.distribution_probabilities}

    @abstractmethod
    def generate_values_as_candidate_key(self, n):
        """ When attribute should be a candidate key in output dataset. """
        return np.arange(n)

    def sample_binning_indices_in_independent_attribute_mode(self, n):
        """ Sample an array of binning indices. """
        return pd.Series(choice(len(self.distribution_probabilities), size=n, p=self.distribution_probabilities))

    @abstractmethod
    def sample_values_from_binning_indices(self, binning_indices):
        """ Convert binning indices into values in domain. Used by both independent and correlated attribute mode. """
        return  binning_indices.apply(lambda x: self.uniform_sampling_within_a_bin(x))

    def uniform_sampling_within_a_bin(self, binning_index):
        binning_index = int(binning_index)
        if binning_index == len(self.distribution_bins):
            return np.nan
        elif self.is_categorical:
            return self.distribution_bins[binning_index]
        else:
            bins = self.distribution_bins.copy()
            bins.append(2 * bins[-1] - bins[-2])
            return uniform(bins[binning_index], bins[binning_index + 1])
