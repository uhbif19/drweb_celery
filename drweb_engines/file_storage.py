""" Работа с игрушечным хранилищем файлов. """

import abc
from abc import abstractmethod
import contextlib

import shutil
import tempfile
import os.path
import pathlib

# Константы

temp_dir_path = pathlib.Path(tempfile.gettempdir())
LOCAL_STORAGE_DIR = temp_dir_path / "drweb_engines"

# Абстрактные классы

class AbstractContextManager(abc.ABC):
    """ Интерфейс contextlib.AbstractContextManager,
        который доступен только с 3.6 версии питона. 

        https://docs.python.org/3/library/contextlib.html#contextlib.AbstractContextManager"""

    @abstractmethod
    def __enter__(self):
        return self

    @abstractmethod
    def __exit__(self, *args):
        pass

class FileStorageUploader(abc.ABC):
    """ Интерфейс загрузки/удаления файлов в хранилище на сервере. """

    @abstractmethod
    def put(self, file_path):
        """ Положить файл в хранилище, 
            и вернуть id местоположения на сервере. """

    @abstractmethod
    def delete(self, uploaded_id):
        """ Удалить файл с указанным id. """

class FileStorageServer(abc.ABC):
    """ Интерфейс для прямого доступа к файлам хранилища.
        Предназначен для самого сервера хранилища. """
    
    @abstractmethod
    def get_file_path(self, uploaded_id):
        """ По id загруженного файла вернуть к нему на сервере. """


# Реализации

def remove_all_files(dir_path):
    for file in dir_path.glob("*"):
        file.unlink() # Удаляем файл

class LocalFileStorage(
    FileStorageUploader, AbstractContextManager,
    FileStorageServer):
    """ %TODO
        Для LocalFileStorage id файла это и есть его путь. """
    
    # Управление хранилищем: создание/закрытие

    _storage_dir: pathlib.Path = None
    
    @property
    def _is_connected(self):
        return self._storage_dir is not None

    def __enter__(self):
        LOCAL_STORAGE_DIR.mkdir(exist_ok=True)
        self._storage_dir = LOCAL_STORAGE_DIR
        return self

    def __exit__(self, *args):
        remove_all_files(LOCAL_STORAGE_DIR)
        self._storage_dir = None

    # Реализация клиента

    def put(self, file_path):
        assert self._is_connected 
        uploaded_path = shutil.copy(file_path, str(self._storage_dir))
        return uploaded_path

    def delete(self, uploaded_path):
        assert self._is_connected
        os.remove(uploaded_path)

    # Реализация сервера

    def get_file_path(self, uploaded_path):
        assert self._is_connected
        return uploaded_path