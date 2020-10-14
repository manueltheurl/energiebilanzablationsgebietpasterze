
from testitest import save_measurement_handler, load_measurement_handler
from importlib import reload
import testitest
from testitest import Test
import sys

sdf = "sdfasdf"

Test.add_stuff()

Test.save_class(sdf)

Test = Test.load_class(sdf)
print(Test.x)
