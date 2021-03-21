import unittest

import pandas as pd

from parlamentikon.Hlasovani import Hlasovani

class TestHlasovani(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('setUpClass')
        cls.hlasovani = Hlasovani(volebni_obdobi=2017, stahni=True)
        pass

    @classmethod
    def tearDownClass(cls):
        # print('teardownClass')
        pass

    def setUp(self):
        # print('setUp')
        pass

    def tearDown(self):
        # print('tearDown')
        pass

    def test_nacti_hlasovani(self):
        print(self)
        #self.assertIsInstance(TestHlasovani.tbl['hlasovani'], pd.core.frame.DataFrame)
        #self.assertIsInstance(TestHlasovani.tbl['_hlasovani'], pd.core.frame.DataFrame)
        pass

if __name__ == '__main__':
    unittest.main()

