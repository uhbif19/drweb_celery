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
except ImportError:
    import drweb_engines.engines as engines


# Константы настроек

REDIS_DB = 'redis://localhost/'

# Собственно настройка очереди задач

queue = celery.Celery()
queue.conf.broker_url = REDIS_DB
queue.conf.result_backend = REDIS_DB

# Хелпер

def concat(ll):
    return reduce(operator.add, ll)

# Задачи

EngineResponse = collections.namedtuple(
    "EngineResponse", "engine,file,response")

@queue.task(bind=True, typed=True)
def process_file_with_engine(self, uploaded_path, engine):
    self.engine = engine
    result, *_ = engines.launch_engine(engine, [uploaded_path]).items()
    return EngineResponse(engine, result[0], result[1])
  
def process_files(uploaded_paths, engines):
    """ Запускаем паралельно задачи по обработке файла разными движками.

        Эту процедуру не получится выделить в task, из-за ограничений Celery.
        См.  http://docs.celeryq.org/en/latest/userguide/tasks.html#task-synchronous-subtasks """

    batch_job = celery.group((
        process_file_with_engine.s(path, engine)
        for engine in engines 
        for path in uploaded_paths))
    result = batch_job.apply_async().join()
    #%HACK
    return list(itertools.starmap(EngineResponse, result))
