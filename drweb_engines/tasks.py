import logging
import os
import collections
import operator
import itertools
from functools import reduce

import celery
from celery.result import GroupResult
from celery.signals import worker_init, worker_shutting_down

try:
    import engines
    import file_storage
except ImportError:
    import drweb_engines.engines as engines
    import drweb_engines.file_storage as file_storage

# Константы настроек

REDIS_DB = 'redis://localhost/'

# Собственно настройка очереди задач

queue = celery.Celery()
queue.conf.broker_url = REDIS_DB
queue.conf.result_backend = REDIS_DB


# Задачи

EngineResponse = collections.namedtuple(
    "EngineResponse", "engine,file,response")

@queue.task(bind=True, typed=True)
def process_file_with_engine(self, uploaded_path, engine_name):
    self.engine_name = engine_name
    with file_storage.LocalFileStorage() as storage:
        local_path = storage.get_file_path(uploaded_path)
        engine = engines.engines_by_name[engine_name]
        results_dict = engine.launch([local_path])
        assert len(results_dict) == 1
        result, *_ = results_dict.items()
        return EngineResponse(engine_name, result[0], result[1])
  
def process_files(uploaded_paths, engines):
    """ Запускаем паралельно задачи по обработке файла разными движками.

        Эту процедуру не получится выделить в task, из-за ограничений Celery.
        См.  http://docs.celeryq.org/en/latest/userguide/tasks.html#task-synchronous-subtasks """

    batch_job = celery.group((
        process_file_with_engine.s(path, engine)
        for engine in engines 
        for path in uploaded_paths))
    result = batch_job.apply_async().join()
    #%HACK: Celery забывает, что тип результатов - EngineResponse
    return list(itertools.starmap(EngineResponse, result))
