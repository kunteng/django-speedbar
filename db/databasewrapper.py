from django.db.backends.util import CursorWrapper
from django.db.utils import load_backend
from mixcloud.speedbar.modules import SqlQueries
from django.conf import settings

from time import time
import traceback

# Import everything except DatabaseWrapper from the wrapped backend
wrappedbackend = load_backend(settings.DATABASE_BACKEND_TO_TRACE)

class _DetailedTracingCursorWrapper(CursorWrapper):
    def execute(self, sql, params=()):
        self.set_dirty()
        start = time()
        try:
            return self.cursor.execute(sql, params)
        finally:
            stop = time()
            duration = stop - start
            sql = self.db.ops.last_executed_query(self.cursor, sql, params)
            stack = traceback.extract_stack()
            instance = SqlQueries.instance()
            if instance:
                instance.record_query_details(sql, duration, stack)

    def executemany(self, sql, param_list):
        self.set_dirty()
        start = time()
        try:
            return self.cursor.executemany(sql, param_list)
        finally:
            stop = time()
            duration = stop - start
            try:
                times = len(param_list)
            except TypeError:           # param_list could be an iterator
                times = None
            stack = traceback.extract_stack()
            instance = SqlQueries.instance()
            if instance:
                instance.record_query_details(sql, duration, stack, times)


class DatabaseWrapper(wrappedbackend.DatabaseWrapper):
    def cursor(self, *args, **kwargs):
        cursor = super(DatabaseWrapper, self).cursor(*args, **kwargs)
        return _DetailedTracingCursorWrapper(cursor, self)

