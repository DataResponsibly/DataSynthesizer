from pathlib import Path

import pandas as pd

from DataSynthesizer.DataDescriber import DataDescriber
from DataSynthesizer.DataGenerator import DataGenerator
from DataSynthesizer.ModelInspector import ks_test, kl_test
from DataSynthesizer.lib.utils import pairwise_attributes_mutual_information


def test_datasynthesizer():
    data_dir = Path(__file__).parent / 'data'
    input_data = data_dir / 'adult_tiny.csv'
    description_file = data_dir / 'description.json'
    output_data = data_dir / 'output.csv'
    uniform_data = data_dir / 'output_uniform.csv'

    threshold_value = 20
    categorical_attributes = {'education': True}
    epsilon = 1
    degree_of_bayesian_network = 2
    num_tuples_to_generate = 10000

    describer = DataDescriber(category_threshold=threshold_value)
    describer.describe_dataset_in_correlated_attribute_mode(dataset_file=input_data,
                                                            epsilon=epsilon,
                                                            k=degree_of_bayesian_network,
                                                            attribute_to_is_categorical=categorical_attributes)

    describer.save_dataset_description_to_file(description_file)

    generator = DataGenerator()
    generator.generate_dataset_in_correlated_attribute_mode(num_tuples_to_generate, description_file)
    generator.save_synthetic_data(output_data)
    generator.generate_dataset_in_random_mode(num_tuples_to_generate, description_file)
    generator.save_synthetic_data(uniform_data)

    df_input = pd.read_csv(input_data, skipinitialspace=True)
    df_output = pd.read_csv(output_data)
    df_uniform = pd.read_csv(uniform_data)

    for col in df_input:
        if col == 'age':
            assert ks_test(df_input, df_output, col) < 0.1
        else:
            assert kl_test(df_input, df_output, col) < 0.01

    df_input_mi = pairwise_attributes_mutual_information(df_input)
    df_output_mi = pairwise_attributes_mutual_information(df_output)
    df_uniform_mi = pairwise_attributes_mutual_information(df_uniform)

    output_diff = (df_output_mi - df_input_mi).abs().sum().sum()
    uniform_diff = (df_uniform_mi - df_input_mi).abs().sum().sum()

    assert output_diff < 5 * uniform_diff
