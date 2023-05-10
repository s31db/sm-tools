from unittest import TestCase
# import hypothesis.strategies as st
# from hypothesis import given, example
from config import config


# class Test(TestCase):
#     def test_config(self):
#         self.fail()

class TestConfig(TestCase):
    # @given(fields=st.lists(st.text(), min_size=1, max_size=10))
    # @given(path='test_ressources/test_config.ini')
    # @given(path=st.data('../test_ressources/test_config.ini'))
    # @given(path=st.text())
    # @example('../test_ressources/test_config.ini')
    # def test_config_hypothesis(self, path):
    #     c = config(path)
    #     assert c['PROJECT_1']['path_project'] == '/PROJECT_1'
    #     assert c['PROJECT_1']['path_tmp'] == 'C:/tmp'
    #     assert c.PROJECT_1['path_tmp'] == 'C:/tmp'
    #     assert c.PROJECT_1.path_tmp == 'C:/tmp'
    #     assert c['PROJECT_2'].path_tmp == 'C:/tmp'
    #     assert c.PROJECT_2.path_project == '/PROJECT_2'

    def test_config(self):
        c = config('tests/test_resources/test_config.ini')
        assert c['PROJECT_1']['path_project'] == '/PROJECT_1'
        assert c['PROJECT_1']['path_tmp'] == 'C:/tmp'
        assert c.PROJECT_1['path_tmp'] == 'C:/tmp'
        assert c.PROJECT_1.path_tmp == 'C:/tmp'
        assert c['PROJECT_2'].path_tmp == 'C:/tmp'
        assert c.PROJECT_2.path_project == '/PROJECT_2'
