import argparse

from analyze.analyze import analyze_history, iterative_analysis, write_output
import logging

from analyze.git.utils.datetime import convert_gitdatestr_to_datetime

if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description='This tool extracts history related information from repositories.')
    subparsers = parser.add_subparsers(
        dest='command',
        help='<commands>',
        required=True
    )

    subparser_analyze_full = subparsers.add_parser(
        'analyze-full-history',
        help='analyze')

    subparser_analyze_full.add_argument(
        '--repository-path', metavar='<path>', type=str,
        help='The path to the history to be analyzed.',
        required=True)

    subparser_analyze_full.add_argument(
        '--include-deleted-contexts', action='store_true',
        help='The path to the history to be analyzed.',
        default=False, required=False)

    subparser_analyze_full.add_argument(
        '--start-date', metavar='<datetime>', type=str,
        help='The start date determining the file version start time',
        default=False, required=False)

    subparser_analyze_iterative = subparsers.add_parser(
        'iterative-analysis',
        help='analyze-effect-by-commit')

    subparser_analyze_iterative.add_argument(
        '--repository-path', metavar='<path>', type=str,
        help='The path to the history to be analyzed.',
        required=True)

    subparser_dump_data = subparsers.add_parser(
        'data-dump',
        help='create a data dump')

    subparser_dump_data.add_argument(
        '--repository-path', metavar='<path>', type=str,
        help='The path to the history to be analyzed.',
        required=True
    )

    args = parser.parse_args()
    command = args.command
    if command == 'analyze-full-history':
        repository_path = args.repository_path
        start_date = args.start_date
        include_deleted_contexts = args.include_deleted_contexts
        analyze_history(repository_path, include_deleted_contexts, start_date)
    if command == 'iterative-analysis':
        repository_path = args.repository_path
        iterative_analysis(repository_path)
    elif command == 'data-dump':
        repository_path = args.repository_path
        write_output(repository_path)
