import os
import unittest
from lm import LanguageModel

class TestLanguageModel(unittest.TestCase):

    def setUp(self):
        os.environ['CZ_DATA_DIR'] = 'test' + os.sep + 'data'
        os.environ['CZ_WORK_DIR'] = 'test' + os.sep + 'work'
        
    def test_inexistent(self):
        self.assertRaises( Exception, LanguageModel, ('test-no-exist'))
    
    def test_create_existing(self):
        lm = LanguageModel('2503')
        self.assertTrue(lm.is_ready())
        
    def test_create_new(self):
        lm = LanguageModel('playing')
        self.assertFalse( lm.is_ready())
        
    def test_get_input_commands(self):
        lm = LanguageModel('playing')
        self.assertEqual( len(lm.get_input_commands()), 7)
        # Exercise reading again, just in case the second time triggers a caching error
        lm.get_input_commands()
        
    def test_update_sentences(self):
        lm = LanguageModel('playing')

    def test_update_all(self):
        lm = LanguageModel('playing')
        lm.update_all( True)
        lm.reset_files()

if __name__ == '__main__':
    unittest.main()
