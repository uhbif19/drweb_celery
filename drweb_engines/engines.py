import logging
import sys
import subprocess
import re
from pathlib import Path

ENGINES_DIR = "engines-bin"

ENGINES = ["A", "B", "C", "D", "E"]
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
    # return subprocess.run(command_and_args, 
    #     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return subprocess.check_output(command_and_args)
def launch_exe(exe_path, args=[]):
    # -> subprocess.CompletedProcess
    """ Запускает указанный экзешник. """

    if args.__class__ != list:
        raise TypeError("Аргумент `args` должен иметь тип list.")

    if sys.platform.startswith("linux"):
        # Под Linux запускаем экзешник используя wine
        result = run_command(["wine", exe_path] + args)
    elif sys.platform.startswith("win"):
        result = run_command([exe_path] + args)
    else:
        raise RuntimeError("Платформа %s не поддерживается." % sys.platform)

    if b"wine: cannot find" in result:
        raise RuntimeError("Исполняемый файл %s не найден." % exe_path)

    return result

# Работа с самими engines

def get_engine_binary(engine_name):
    return ENGINE_BINARY.format(engine_name)

def get_logfile_name(engine_name):
    return ENGINE_LOGFILE.format(engine_name)

def get_engine_path(engine_name, engines_dir):
    exe_path = Path(engines_dir) / get_engine_binary(engine_name)
    return str(exe_path)

def fix_newline(text):
    """ Убирает символ возврата каретки "\r". 
        Он почему-то не парсится модулем `re` как перевод строки. """
    return text.replace("\r", "")

def parse_engine_output(engine_name, output) -> dict:
    """ Парсит полученный от Engine вывод, и возвращает словарь,
        отображающий название файла в результат его обработки. """
    line_regexp = ENGINE_RESULT_REGEXP[engine_name]
    output = fix_newline(output)
    line_matches = re.finditer(line_regexp, output, flags=re.MULTILINE)
    groups = [match.groupdict() for match in line_matches]
    clean = lambda text: text.strip("\r")
    return {clean(g["filename"]): clean(g["result"]) for g in groups}

def launch_engine(engine_name, file_paths, engines_dir=ENGINES_DIR) -> dict:
    assert engine_name in ENGINES
    assert file_paths.__class__ is list
    assert len(file_paths) == 1, "движки не умеют обрабатывать >1 файла за раз"
    exe_path = get_engine_path(engine_name, engines_dir)
    result = launch_exe(exe_path, file_paths)
    output = result.decode(ENGINES_ENCODING)
    return parse_engine_output(engine_name, output)