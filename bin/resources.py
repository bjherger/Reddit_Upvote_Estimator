import gzip
import logging
import os

import gensim
import requests
from collections import defaultdict

from lib import get_conf


def download_embedding():
    """
    Prepare GoogleNews pre-trained word embeddings.

     - Check if compressed embeddings are available
     - If compressed embeddings are not available, download them
     - Check if uncompressed embeddings are available
     - If compressed embeddings are not available, uncompress embeddings

    :return: None
    :rtype: None
    """

    logging.info('Attempting to either validate or download and extract embeddings.')

    # Reference variables
    embedding_download_link = 'https://s3.amazonaws.com/dl4j-distribution/GoogleNews-vectors-negative300.bin.gz'
    embedding_downloaded_path = '../resources/compressed/GoogleNews-vectors-negative300.bin.gz'

    # Download embeddings, if necessary
    if not os.path.exists(embedding_downloaded_path):
        logging.warn('embedding_downloaded_path does not yet exist. Downloading embedding. This occurs once, and will take '
                     '10-20 minutes (due to large file size)')
        print('embedding_downloaded_path does not yet exist. Downloading embedding. This occurs once, and will take '
                     '10-20 minutes (due to large file size)')
        logging.info(
            'Downloading embedding data from: {} to: {}'.format(embedding_download_link, embedding_downloaded_path))

        download_file(embedding_download_link, embedding_downloaded_path)

    # Extract embeddings, if necessary
    if not os.path.exists(get_conf('embedding_path')):
        logging.warn('embedding_path does not exist. Extracting embedding.')
        logging.info(
            'Extracting embedding data from: {} to: {}'.format(embedding_downloaded_path, get_conf('embedding_path')))

        with gzip.open(embedding_downloaded_path, 'rb') as zipped, \
                open(get_conf('embedding_path'), 'w+') as unzipped:
            for line in zipped:
                unzipped.write(line)

    logging.info('Embeddings available at: {}'.format(get_conf('embedding_path')))


def download_file(url, local_file_path):
    """
    Download the file at `url` in chunks, to the location at `local_file_path`
    :param url: URL to a file to be downloaded
    :type url: str
    :param local_file_path: Path to download the file to
    :type local_file_path: str
    :return: The path to the file on the local machine (same as input `local_file_path`)
    :rtype: str
    """

    # Reference variables
    chunk_count = 0

    # Create connection to the stream
    r = requests.get(url, stream=True)

    # Open output file
    with open(local_file_path, 'wb') as f:

        # Iterate through chunks of file
        for chunk in r.iter_content(chunk_size=1048576):

            logging.debug('Downloading chunk: {} for file: {}'.format(chunk_count, local_file_path))

            # If there is a chunk to write to file, write it
            if chunk:
                f.write(chunk)

            # Increase chunk counter
            chunk_count = chunk_count + 1

    r.close()
    return local_file_path


def create_embedding_matrix():
    """
    Load embedding assets from file.

     - Load embedding binaries w/ gsensim
     - Extract embedding matrix from gensim model
     - Extract word to index lookup from gensim model
    :return: embedding_matrix, word_to_index
    :rtype: (numpy.array, {str:int})
    """

    logging.info('Reading embedding matrix and word to index dictionary from file')

    # Get word weights from file via gensim
    model = gensim.models.KeyedVectors.load_word2vec_format(get_conf('embedding_path'), binary=True)
    embedding_matrix = model.syn0

    # Filter out words with index not in w2v range
    word_to_index = dict([(k, v.index) for k, v in model.vocab.items()])

    # Transform embedding resources
    # Embedding: Update embedding to map any unknown words (words not in training vocabulary) to the unknown value
    default_dict_instance = defaultdict(lambda: word_to_index['UNK'])
    default_dict_instance.update(word_to_index)
    word_to_index = default_dict_instance

    logging.info('Created embedding matrix, of shape: {}'.format(embedding_matrix.shape))
    logging.info('Created word to index lookup, with min index: {}, max index: {}'.format(min(word_to_index.values()),
                                                                                          max(word_to_index.values())))

    return embedding_matrix, word_to_index