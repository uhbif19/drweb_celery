""" Работа с игрушечным хранилищем файлов. """

import shutil
import tempfile
import os.path

FILE_STORAGE = None # Директория на "сервере", в которую "загружаются" файлы

# Управление хранилищем: создание/закрытие

def setup_file_storage():
    global FILE_STORAGE
    FILE_STORAGE = tempfile.mkdtemp(prefix="drweb_")

def teardown_file_storage():
    global FILE_STORAGE
    shutil.rmtree(FILE_STORAGE)
    FILE_STORAGE = None

# Управление файлами

def put_to_storage(file_path):
    assert FILE_STORAGE is not None
    uploaded_path = shutil.copy(file_path, FILE_STORAGE)
    return uploaded_path

def remove_from_storage(uploaded_path):
    os.remove(uploaded_path)