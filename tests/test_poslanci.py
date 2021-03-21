import unittest

import pandas as pd

from parlamentikon.PoslanciOsoby import Poslanci

class TestPoslanciLast(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print('setUpClass')
        self.poslanci = Poslanci()
        pass

    @classmethod
    def tearDownClass(self):
        # print('teardownClass')
        pass

    def setUp(self):
        # print('setUp')
        pass

    def tearDown(self):
        # print('tearDown')
        pass

    def test_poslanci_zakladni_vlastnosti_tabulky(self):
        self.assertEqual(self.poslanci.groupby('id_osoba').size().max(), 1)
        self.assertEqual(self.poslanci.groupby('id_osoba').size().min(), 1)

if __name__ == '__main__':
    unittest.main()

