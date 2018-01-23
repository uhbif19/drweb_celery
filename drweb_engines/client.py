from functools import reduce
import operator
import itertools
import argparse
import os

import engines
import tasks
import file_storage

# Текстовые Описания

DESCRIPTION = ""
ENGINES_HELP = """список движков, которыми нужно обработать файл.
По умолчанию используются все доступные движки.
Доступные движки: %s""" % (", ".join(engines.ENGINES))

# Настройки парсера аргументов

parser = argparse.ArgumentParser(description=DESCRIPTION)
parser.add_argument('files', type=str, nargs="+",
                    help='файлы, которые отправится на обработку серверу')
parser.add_argument("--engines", metavar="ENGINE", nargs="+",
                    help=ENGINES_HELP)
parser.set_defaults(engines=engines.ENGINES)

# Проверка корректности введенных аргументов


def validate_engines(engines_list):
    bad_engines = set(engines_list) - set(engines.ENGINES)
    if len(bad_engines) > 0:
        bad_engines_str = ", ".join(bad_engines)
        print("Движки [%s] - не входят в список допустимых движков."
              % bad_engines_str)
        return False
    else:
        return True


def check_file_exists(file):
    file_exists = os.path.exists(file)
    if not file_exists:
        print("Файл '%s', похоже не существует." % file)
    return file_exists

def check_files_existing(files):
    check_results = map(check_file_exists, files)
    all_true = lambda x: reduce(operator.and_, x)
    return all_true(check_results)

def validate_arguments(args):
    return validate_engines(args.engines) and check_files_existing(args.files)

# Main

def filename(file_path):
    """ По пути к файлу выдает его название. """
    return os.path.basename(file_path)

def group_by_filename(results):
    get_filename = lambda result: filename(result.file)
    results.sort(key=get_filename)    
    return itertools.groupby(results, key=get_filename)

def print_results(results):
    for filename, values in group_by_filename(results):
        print("Для файла %s, полученны следующие результаты:" % filename)
        for value in values:
            engine_name = engines.get_engine_binary(value.engine)
            print("\tДвижок '%s' выдал '%s'." % (engine_name, value.response))

def main():
    args = parser.parse_args()
    if not validate_arguments(args):
        return
    else:
        file_storage.setup_file_storage()
        files = list(map(file_storage.put_to_storage, args.files))
        print("Файлы загружены в хранилище, запускаем обработчики.")
        results = tasks.process_files(files, args.engines)
        print_results(results)
        print("Обработчики все сделали. Закрываем хранилище.")
        file_storage.teardown_file_storage()


if __name__ == "__main__":
    main()