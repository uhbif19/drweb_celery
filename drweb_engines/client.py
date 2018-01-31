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
Доступные движки: %s""" % (", ".join(engines.engine_names))

# Проверка корректности введенных аргументов

def check_file_exists(file):
    return os.path.exists(file)

def exisisting_file(path):
    """ %TODO """
    if not check_file_exists(path):
        raise argparse.ArgumentTypeError(
            "Файл '%s', похоже не существует." % path)
    return path

# Настройки парсера аргументов

parser = argparse.ArgumentParser(description=DESCRIPTION)
parser.add_argument('files', type=exisisting_file, nargs="+", 
                    help='файлы, которые отправится на обработку серверу')
parser.add_argument("--engines", metavar="ENGINE", nargs="+",
                    choices=engines.engine_names, default=engines.engine_names,
                    help=ENGINES_HELP)

# Вывод результатов

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
            engine = engines.engines_by_name[value.engine]
            engine_name = engine.name
            print("\tДвижок '%s' выдал '%s'." % (engine_name, value.response))

# Main

def main():
    args = parser.parse_args()
    with file_storage.LocalFileStorage() as storage:
        file_ids = list(map(storage.put, args.files))
        print("Файлы загружены в хранилище, запускаем обработчики.")
        results = tasks.process_files(file_ids, args.engines)
        print_results(results)
        print("Обработчики все сделали. Закрываем хранилище.")

if __name__ == "__main__":
    main()