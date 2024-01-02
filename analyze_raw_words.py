"""
Analyze raw words from inaugural addresses text files.

Usage::

    pip install joblib pandas wordcloud matplotlib nltk
    python analyze_raw_words.py

"""

import itertools
import logging
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from joblib import Parallel, delayed
from nltk.probability import FreqDist
from wordcloud import WordCloud

DATASET_BASE_PATH = Path("./data")
DATASET_RAW_PATH = DATASET_BASE_PATH / "raw"
DATASET_INTERIM_PATH = DATASET_BASE_PATH / "interim"
DATASET_INAUGURAL_RAW_PATH = DATASET_RAW_PATH / "inaugural-addresses"

METADATA_HEADERS = ("word", "frequency", "has_special_chars", "has_nums", "has_contraction")

PARALLEL_NUM_JOBS = -1
PARALLEL_VERBOSITY_LEVEL = 10

LOGGING_LEVEL = logging.INFO
LOGGING_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def _configure_logging():
    """Configure basic multiprocessing loggging."""
    if len(logging.getLogger().handlers) == 0:
        logging.basicConfig(level=LOGGING_LEVEL, format=LOGGING_FORMAT)


def generate_wordcloud(freq_dist=None):
    """Generate and save inaugural addresses word cloud."""
    logging.info("Generating inaugural addresses wordcloud ...")
    wordcloud = WordCloud(width=1600, height=800, background_color="white")
    wordcloud = wordcloud.generate_from_frequencies(freq_dist)

    plt.figure(figsize=(20, 10))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.title("Inaugural Addresses - Raw Word Cloud")

    wordcloud_path = DATASET_INTERIM_PATH / "inaugural_address_raw_words_wordcloud.png"
    logging.info(f"Saving inagural addresses wordcloud at {wordcloud_path}")
    plt.savefig(wordcloud_path, dpi=300)
    logging.info("Generating inaugural addresses wordcloud finished.")


def process_inaugural_word(word_freq=None):
    """Enrich inaugural address word with extra metadata."""
    _configure_logging()

    word, frequency = word_freq
    has_special_chars = True if re.search(r"[^a-zA-Z0-9\s]", word) else False
    has_contraction = "'" in word
    has_nums = True if re.search(r"\d", word) else False

    return word, frequency, has_special_chars, has_nums, has_contraction


def process_inaugural_file(inaugural_address_file=None):
    """Process each text line in inaugural address file."""
    _configure_logging()
    logging.info(f"Processing {inaugural_address_file.name} inaugural address file ...")
    with open(inaugural_address_file, "r") as text_lines:
        words = []
        for text_line in text_lines:
            words = words + text_line.strip().split()
        return words


def glob_inaugural_files(raw_dir=None):
    """Search and yield inaugural address files."""
    raw_dir_path = Path(raw_dir).expanduser().resolve()
    yield from raw_dir_path.glob("*.txt")


_configure_logging()
logging.info("Start.")

logging.info("Processing inaugural addresses files ...")
files = glob_inaugural_files(raw_dir=DATASET_INAUGURAL_RAW_PATH)
file_words = Parallel(n_jobs=PARALLEL_NUM_JOBS, verbose=PARALLEL_VERBOSITY_LEVEL)(
    delayed(process_inaugural_file)(file) for file in files
)
file_words = itertools.chain.from_iterable(file_words)
logging.info("Processing inaugural addresses files finished.")

logging.info("Generating inaugural addresses word frequency distribution ...")
freq_dist = FreqDist(file_words)
generate_wordcloud(freq_dist=freq_dist)
logging.info("Generating inaugural addresses word frequency distribution finished.")


logging.info("Processing inaugural addresses words ...")
words = Parallel(n_jobs=PARALLEL_NUM_JOBS, verbose=PARALLEL_VERBOSITY_LEVEL)(
    delayed(process_inaugural_word)(word) for word in freq_dist.items()
)
metadata_df = pd.DataFrame([dict(zip(METADATA_HEADERS, word)) for word in words])
metadata_df = metadata_df.sort_values(by="frequency", ascending=False)
metadata_path = DATASET_INTERIM_PATH / "inaugural_address_raw_words_metadata.csv"
logging.info(f"Saving inagural addresses words metadata at {metadata_path}")
metadata_df.to_csv(metadata_path, index=False)
logging.info("Processing inaugural addresses words finished.")

logging.info("Done.")
