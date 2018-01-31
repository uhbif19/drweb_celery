import logging
import sys
import subprocess
import re
from pathlib import Path

ENGINES_DIR = "engines-bin"
ENGINE_BINARY = "Engine{}.exe"
ENGINE_LOGFILE = "Engine{}.log"
ENGINES_ENCODING = "utf8" #%TODO: разобраться, какой он будет по виндой
ENGINE_RESULT_REGEXP = {
    "A": r"^'(?P<filename>.+)' scanned\. Result: (?P<result>.+)$",
    "B": r"^{\"(?P<filename>.+)\": \"(?P<result>.+)\"}",
    "C": r"^'(?P<filename>.+)'\|\|\|(?P<result>.+)$",
    "D": r"^(?P<result>.+) from '(?P<filename>.+)'$",
    "E": r"^The '(?P<filename>.+)' is (?P<result>.+)$"
}

# Запуск экзешников

def run_command(command_and_args):
    return subprocess.check_output(command_and_args)

def prune_wine_warnings(text):
    REGEXP = r"^.*:fixme:.*$"
    pruned = re.sub(REGEXP, "", text, flags=re.MULTILINE)
    return pruned

def launch_exe(exe_path, args=None):
    # -> subprocess.CompletedProcess
    """ Запускает указанный экзешник. """

    if args is None:
        args = []
        
    if args.__class__ != list:
        raise TypeError("Аргумент `args` должен иметь тип list.")

    if sys.platform.startswith("linux"):
        # Под Linux запускаем экзешник используя wine
        result = run_command(["wine", exe_path] + args)
        result = result.decode(ENGINES_ENCODING)
        result = prune_wine_warnings(result)
        if "wine: cannot find" in result:
            raise RuntimeError("Исполняемый файл %s не найден." % exe_path)
    elif sys.platform.startswith("win"):
        result = run_command([exe_path] + args)
        result = result.decode(ENGINES_ENCODING)
    else:
        raise RuntimeError("Платформа %s не поддерживается." % sys.platform)

    return result

# Работа с самими engines

def fix_newline(text):
    """ Убирает символ возврата каретки "\r". 
        Он почему-то не парсится модулем `re` как перевод строки. """
    return text.replace("\r", "")

class Engine:

    name = None
    result_line_regexp = None
    engines_dir = ENGINES_DIR

    def __init__(self, engine_name):
        assert engine_name in engine_names
        self.name = engine_name
        self.result_line_regexp = ENGINE_RESULT_REGEXP[engine_name]

    @property
    def binary_file(self):
        return ENGINE_BINARY.format(self.name)

    @property
    def binary_path(self):
        exe_path = Path(self.engines_dir) / self.binary_file
        return str(exe_path)

    @property
    def logfile(self):
        return ENGINE_LOGFILE.format(self.name)

    def parse_engine_output(self, output) -> dict:
        """ Парсит полученный от Engine вывод, и возвращает словарь,
        отображающий название файла в результат его обработки. """
        line_regexp = self.result_line_regexp
        output = fix_newline(output)
        line_matches = re.finditer(line_regexp, output, flags=re.MULTILINE)
        groups = [match.groupdict() for match in line_matches]
        clean = lambda text: text.strip("\r")
        return {clean(g["filename"]): clean(g["result"]) for g in groups}

    def launch(self, file_paths) -> dict:
        assert file_paths.__class__ is list
        assert len(file_paths) == 1, \
            "движки не умеют обрабатывать >1 файла за раз"
        result = launch_exe(self.binary_path, file_paths)
        return self.parse_engine_output(result)

# Список всех доступных движков

engine_names = ["A", "B", "C", "D", "E"]
engines_by_name = {name: Engine(name) for name in engine_names}