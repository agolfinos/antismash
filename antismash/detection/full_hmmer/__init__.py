# License: GNU Affero General Public License v3 or later
# A copy of GNU AGPL v3 should have been included in this software package in LICENSE.txt.

"""Full genome PFAM anotation"""

import logging
import os
from typing import List

from antismash.config import get_config
from antismash.common import path, pfamdb, hmmer
from antismash.config.args import ModuleArgs

NAME = "full_hmmer"
SHORT_DESCRIPTION = "Full genome PFAM anotation"

MIN_SCORE = 0.
MAX_EVALUE = 0.01


def get_arguments() -> ModuleArgs:
    """ Builds the module args """
    args = ModuleArgs('Full HMMer options', 'fullhmmer')
    args.add_analysis_toggle('fullhmmer',
                             dest='fullhmmer',
                             action='store_true',
                             default=False,
                             help="Run a whole-genome HMMer analysis.")
    args.add_option('pfamdb-version',
                    dest='pfamdb_version',
                    type=str,
                    default='latest',
                    help="PFAM database version number (e.g. 27.0) (default: %(default)s).")
    return args


def check_options(options) -> List[str]:
    """ Check the requested PFAM database exists """
    database_version = options.fullhmmer_pfamdb_version
    pfam_dir = os.path.join(options.database_dir, "pfam")
    if database_version == "latest":
        database_version = pfamdb.find_latest_database_version(options.database_dir)
    return pfamdb.check_db(os.path.join(pfam_dir, database_version))


def is_enabled(options) -> bool:
    """  Uses the supplied options to determine if the module should be run """
    return options.fullhmmer


def check_prereqs() -> List[str]:
    """ Ensure at least one database exists and is valid """
    failure_messages = []
    for binary_name in ['hmmscan']:
        if not path.locate_executable(binary_name):
            failure_messages.append("Failed to locate executable: %r" % binary_name)

    data_dir = get_config().database_dir
    try:
        version = pfamdb.find_latest_database_version(data_dir)
    except ValueError as err:
        failure_messages.append(str(err))
        return failure_messages

    data_path = os.path.join(data_dir, "pfam", version)
    failure_messages.extend(pfamdb.check_db(data_path))
    return failure_messages


def regenerate_previous_results(previous, record, options) -> hmmer.HmmerResults:
    """ Rebuild previous results """
    if not previous:
        return None
    db = pfamdb.get_db_path_from_version(options.fullhmmer_pfamdb_version, options.database_dir)
    return hmmer.HmmerResults.from_json(previous, record, MAX_EVALUE, MIN_SCORE, db)


def run_on_record(record, results, options) -> hmmer.HmmerResults:
    """ Run hmmsearch against PFAM for all CDS features within the record """
    if results:
        return results

    logging.info('Running whole-genome PFAM search')

    if options.fullhmmer_pfamdb_version == "latest":
        database_version = pfamdb.find_latest_database_version(options.database_dir)
    else:
        database_version = options.fullhmmer_pfamdb_version
    database = os.path.join(options.database_dir, 'pfam', database_version, 'Pfam-A.hmm')

    return hmmer.run_hmmer(record, record.get_cds_features(), MAX_EVALUE, MIN_SCORE, database, "fullhmmer")
