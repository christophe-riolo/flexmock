import new

class InvalidMethodSignature(Exception):
  pass


class Expectation(object):
  def __init__(self, name, mock, args=None, return_value=None):
    self.method = name
    self.args = args
    self.return_value = return_value
    self.times_called = 0
    self.expected_calls = None
    self.exception = None
    self.mock = mock

  def __str__(self):
    return '%s(%s) -> %s' % (self.method, self.args, self.return_value)

  def with_args(self, args):
    self.args = args
    return self

  def and_return(self, value):
    self.return_value = value
    return self

  def times(self, number):
    self.expected_calls = number
    return self

  def and_raise(self, exception):
    self.exception = exception
    return self


class FlexMock(object):
  def __init__(self, object_class_or_name):
    if isinstance(object_class_or_name, str):
      self.name = object_class_or_name
      self.mock = self
    else:
      object_class_or_name.should_receive = self.should_receive
      object_class_or_name.expectations = self.expectations
      object_class_or_name.times_called = self.times_called
      object_class_or_name.verify_expectations = self.verify_expectations
      object_class_or_name._expectations = []
      self.mock = object_class_or_name
    self._expectations = []

  def should_receive(self, method, args=None, return_value=None):
    def mock_method(self, *kargs, **kwargs):
      arguments = kargs
      expectation = self.expectations(method, arguments)
      if expectation:
        expectation.times_called += 1
        if expectation.exception:
          raise expectation.exception
        return expectation.return_value
      else:
        raise InvalidMethodSignature(str(arguments))

    if method in [x.method for x in self._expectations]:
      expectation = [x for x in self._expectations if x.method == method][0]
      if expectation.args is None:
        expectation.args = args
      else:
        expectation = Expectation(method, self.mock, args, return_value)
    else:
      expectation = Expectation(method, self.mock, args, return_value)
    self._expectations.append(expectation)
    method_instance = mock_method
    setattr(self.mock, method, new.instancemethod(
        method_instance, self.mock, self.__class__))
    return expectation

  def expectations(self, name=None, args=None):
    if name:
      expectation = None
      for e in self._expectations:
        if e.method == name:
          if args:
            if self._match_args(args, (e.args,)):
              expectation = e
          else:
            expectation = e
      return expectation
    else:
      return self._expectations

  def _match_args(self, given_args, expected_args):
    if given_args == expected_args:
      return True
    try:
      if len(given_args) == 1 and isinstance(given_args[0], expected_args[0]):
        return True
    except:
      pass

  def times_called(self, method, args=None):
    expectation = self.expectations(method, (args,))
    if expectation:
      return expectation.times_called
    else:
      return None

  def verify_expectations(self):
    all_good = True
    for expectation in self._expectations:
      all_good = expectation.times_called == expectation.expected_calls
    return all_good
