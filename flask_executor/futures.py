from collections import OrderedDict
import concurrent.futures


class FutureCollection:

    """A FutureCollection is an object to store and interact with :class:`concurrent.futures.Future`
    objects. It provides access to all attributes and methods of a Future by proxying attribute
    calls to the stored Future object.

    To access the methods of a Future from a FutureCollection instance, include a valid
    ``future_key`` value as the first argument of the method call. To access attributes, call them
    as though they were a method with ``future_key`` as the sole argument. If ``future_key`` does
    not exist, the call will always return None. If ``future_key`` does exist but the referenced
    Future does not contain the requested attribute an :exc:`AttributeError` will be raised.

    To prevent memory exhaustion a FutureCollection instance can be bounded by number of items using
    the ``max_length`` parameter. As a best practice, Futures should be popped once they are ready
    for use, with the proxied attribute form used to determine whether a Future is ready to be used
    or discarded.

    :param max_length: Maximum number of Futures to store. Oldest Futures are discarded first.

    """
    def __init__(self, max_length=50):

        self.max_length = max_length
        self._futures = OrderedDict()

    def __contains__(self, future):
        return future in self._futures.values()

    def __len__(self):
        return len(self._futures)

    def __getattr__(self, attr):
        # Call any valid Future method or attribute
        def _future_attr(future_key, *args, **kwargs):
            if future_key not in self._futures:
                return None
            future_attr = getattr(self._futures[future_key], attr)
            if callable(future_attr):
                return future_attr(*args, **kwargs)
            return future_attr
        return _future_attr

    def _check_size_limit(self):
        if self.max_length is not None:
            while len(self._futures) > self.max_length:
                self._futures.popitem(last=False)

    def add(self, future_key, future):
        """Add a new Future. If ``max_length`` limit was defined for the FutureCollection, old
        Futures may be dropped to respect this limit.

        :param future_key: Key for the Future to be added.
        :param future: Future to be added.
        """
        if future_key in self._futures:
            raise ValueError("future_key {} already exists".format(future_key))
        self._futures[future_key] = future
        self._check_size_limit()

    def pop(self, future_key):
        """Return a Future and remove it from the collection. Futures that are ready to be used
        should always be popped so they do not continue to consume memory.

        Returns ``None`` if the key doesn't exist.

        :param future_key: Key for the Future to be returned.
        """
        return self._futures.pop(future_key, None)