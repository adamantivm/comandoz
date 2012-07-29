import unittest
from state_machine import Listening, InitialState

class TestStates(unittest.TestCase):
    def test_create_Listening(self):
        listening = Listening()
        self.assertNotEqual( listening.lm, None)
        self.assertTrue( listening.lm.is_ready(), True)

    '''Create a new state class programmatically, just like the state machine would do'''
    def test_new_state(self):
        initial = InitialState()
        clazz = getattr(__import__(__name__), initial.keywords['MARY'])
        listening = clazz()
        self.assertNotEqual( listening.lm, None)
        self.assertTrue( listening.lm.is_ready(), True)
        