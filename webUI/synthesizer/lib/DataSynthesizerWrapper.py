import json

import numpy as np
import pandas as pd

from DataSynthesizer.DataDescriber import DataDescriber
from DataSynthesizer.DataGenerator import DataGenerator
from DataSynthesizer.lib.utils import pairwise_attributes_mutual_information, read_json_file


def get_dataset_info(file_name):
    d = DataDescriber()
    d.describe_dataset_in_independent_attribute_mode(file_name)

    dataset_info = {'candidate_attributes': [],
                    'categorical_attributes': [],
                    'attribute_datatypes': {},
                    'number_of_tuples': d.dataset_description['meta']['num_tuples'],
                    'attribute_list': d.dataset_description['meta']['all_attributes']}

    for attribute in d.dataset_description['attribute_description']:
        current_attribute_info = d.dataset_description['attribute_description'][attribute]
        if current_attribute_info['is_candidate_key']:
            dataset_info['candidate_attributes'].append(attribute)
        if current_attribute_info['is_categorical']:
            dataset_info['categorical_attributes'].append(attribute)
        dataset_info['attribute_datatypes'][attribute] = current_attribute_info['data_type']

    return dataset_info


def get_histogram_data_of_attribute_for_dataset(attribute_name, dataset_filename):
    df = pd.read_csv(dataset_filename)
    df[attribute_name + 'y'] = 0
    return df.as_matrix(columns=[attribute_name, attribute_name + 'y']).tolist()


def generate_data(username):
    configuration = read_json_file('{}_parameters.json'.format(username))
    input_dataset_file = '{}.csv'.format(username)
    description_file = '{}_description.json'.format(username)
    synthetic_dataset_file = '{}_synthetic_data.csv'.format(username)

    initial_dataset_info = get_dataset_info(input_dataset_file)

    attribute_to_is_candidate = {}
    for attr in initial_dataset_info['attribute_list']:
        if attr in configuration['candidate_atts']:
            attribute_to_is_candidate[attr] = True
        else:
            attribute_to_is_candidate[attr] = False

    attribute_to_is_categorical = {}
    for attr in initial_dataset_info['attribute_list']:
        if attr in configuration['categorical_atts']:
            attribute_to_is_categorical[attr] = True
        else:
            attribute_to_is_categorical[attr] = False

    if configuration['tuple_n'] == '':
        n = initial_dataset_info['number_of_tuples']
    else:
        n = int(configuration['tuple_n'])

    # if configuration['categorical_threshold'] == '':
    #     categorical_threshold = 10
    # else:
    #     categorical_threshold = int(configuration['categorical_threshold'])

    if configuration['seed'] == '':
        seed = 0
    else:
        seed = int(configuration['seed'])

    generator = DataGenerator()
    if configuration['chose_mode'] == 'mode1':
        describer = DataDescriber()
        describer.describe_dataset_in_random_mode(input_dataset_file, {}, attribute_to_is_categorical, attribute_to_is_candidate, seed)
        describer.save_dataset_description_to_file(description_file)
        generator.generate_dataset_in_random_mode(n, description_file, seed)
    else:

        if configuration['histogram_size'] == '':
            histogram_size = 20
        else:
            histogram_size = int(configuration['histogram_size'])

        if configuration['epsilon'] == '':
            epsilon = 0.1
        else:
            epsilon = configuration['epsilon']

        attribute_to_datatype = configuration['type_atts']

        describer = DataDescriber(histogram_size)
        if configuration['chose_mode'] == 'mode2':
            describer.describe_dataset_in_independent_attribute_mode(input_dataset_file, epsilon, attribute_to_datatype,
                                                                     attribute_to_is_categorical, attribute_to_is_candidate, seed)
            describer.save_dataset_description_to_file(description_file)
            generator.generate_dataset_in_independent_mode(n, description_file, seed)
        elif configuration['chose_mode'] == 'mode3':
            if configuration['max_degree'] == '':
                max_degree = 3
            else:
                max_degree = int(configuration['max_degree'])

            describer.describe_dataset_in_correlated_attribute_mode(input_dataset_file,
                                                                    max_degree,
                                                                    epsilon,
                                                                    attribute_to_datatype,
                                                                    attribute_to_is_categorical,
                                                                    attribute_to_is_candidate,
                                                                    seed)
            describer.save_dataset_description_to_file(description_file)
            generator.generate_dataset_in_correlated_attribute_mode(n, description_file, seed)

    generator.save_synthetic_data(synthetic_dataset_file)


def get_plot_data(input_dataset_file, synthetic_dataset_file, description_file):
    description = read_json_file(description_file)
    df_before = pd.read_csv(input_dataset_file)
    df_after = pd.read_csv(synthetic_dataset_file)
    plot_data = {'histogram': {}, 'barchart': {}, 'heatmap': {}}
    for attr in df_before:
        if description['attribute_description'][attr]['is_categorical']:
            bins_before, counts_before = get_barchart_data(df_before, attr)
            bins_after, counts_after = get_barchart_data(df_after, attr)
            plot_data['barchart'][attr] = {'before': {'bins': bins_before, 'counts': counts_before},
                                           'after': {'bins': bins_after, 'counts': counts_after}}
        elif description['attribute_description'][attr]['data_type'] in {'Integer', 'Float'}:
            plot_data['histogram'][attr] = {'before': get_histogram_data(df_before, attr),
                                            'after': get_histogram_data(df_after, attr)}

    plot_data['heatmap']['before'] = get_heatmap_data(input_dataset_file)
    plot_data['heatmap']['after'] = get_heatmap_data(synthetic_dataset_file)
    plot_file_name = input_dataset_file.replace(".csv", "_plot.json")
    with open(plot_file_name, 'w') as outfile:
        json.dump(plot_data, outfile, indent=4)


def get_categorical_attributes_csv(input_file_name, categorical_threshold=20):
    # get the categorical attributes using data describer
    df = pd.read_csv(input_file_name)
    numeric_attributes = df.describe().columns

    categorical_attributes = []

    for attr in df:
        if df[attr].dropna().unique().size <= categorical_threshold:
            categorical_attributes.append(attr)
        elif attr in numeric_attributes:
            pass
        else:
            categorical_attributes.append(attr)
    return categorical_attributes

def get_binary_attributes_csv(input_file_name, categorical_threshold=2):
    # get the categorical attributes using data describer
    df = pd.read_csv(input_file_name)
    binary_attributes = []

    for attr in df:
        if df[attr].dropna().unique().size == categorical_threshold:
            binary_attributes.append(attr)
    return binary_attributes

def get_categorical_attributes(plot_json_file):
    plot_data = read_json_file(plot_json_file)
    return list(plot_data['barchart'].keys())


def get_drawable_attributes(plot_json_file):
    plot_data = read_json_file(plot_json_file)
    return list(plot_data['barchart'].keys()) + list(plot_data['histogram'].keys())


def get_barchart_data(df, col, sort_index=True):
    distribution = df[col].dropna().value_counts()
    if sort_index:
        distribution.sort_index(inplace=True)

    bins = distribution.index.tolist()
    if (distribution.index.dtype == 'int64'):
        bins = [int(x) for x in distribution.index]
    return bins, distribution.tolist()


def get_histogram_data(df, col):
    distribution = np.histogram(df[col].dropna(), bins=20)
    return [[float(distribution[1][i]), int(distribution[0][i])] for i in range(len(distribution[0]))]


def get_barchart_data_of_top_frequencies(df, col, bins=20):
    distribution = df[col].dropna().value_counts()[:bins]
    bins = distribution.index.tolist()
    if (distribution.index.dtype == 'int64'):
        bins = [int(x) for x in distribution.index]
    return bins, distribution.tolist()


def get_heatmap_data(dataset_filename):
    df = pd.read_csv(dataset_filename)
    values = pairwise_attributes_mutual_information(df)
    out = []
    attributes = values.columns
    for x, xattr in enumerate(attributes):
        for y, yattr in enumerate(attributes):
            out.append([x, y, int(round(1000 * values.loc[xattr, yattr])) / 1000])
    return out


def get_histograms_of(input_dataset_file, categorical_threshold=20):
    df = pd.read_csv(input_dataset_file)
    numeric_attributes = df.describe().columns
    plot_data = {'histogram': {}, 'barchart': {}}

    all_attributes = list(df.columns)
    drawable_attributes = []
    categorical_attributes = []
    attribute_information = {'all_atts': all_attributes,
                             'drawable_atts': drawable_attributes,
                             'cate_atts': categorical_attributes,
                             "numeric_atts":numeric_attributes}

    for attr in df:
        if df[attr].dropna().unique().size <= categorical_threshold:
            bins, counts = get_barchart_data(df, attr, False)
            plot_data['barchart'][attr] = {'bins': bins, 'counts': counts}
            categorical_attributes.append(attr)
            drawable_attributes.append(attr)
        elif attr in numeric_attributes:
            plot_data['histogram'][attr] = get_histogram_data(df, attr)
            drawable_attributes.append(attr)
        else:
            bins, counts = get_barchart_data_of_top_frequencies(df, attr)
            plot_data['barchart'][attr] = {'bins': bins, 'counts': counts}
            categorical_attributes.append(attr)
            drawable_attributes.append(attr)

    plot_file_name = input_dataset_file.replace(".csv", "_plot.json")
    with open(plot_file_name, 'w') as outfile:
        json.dump(plot_data, outfile, indent=4)

    return attribute_information


if __name__ == '__main__':
    data = '~/GitLab/data-responsibly-webUI/dataResponsiblyUI/static/data/adult_mini_1.csv'
