import time
import gobject
import pygst
from lm import LanguageModel, ManualLanguageModel
import types
pygst.require('0.10')
gobject.threads_init()
import gst
import logging
import sys
import freevo_client as rc

logging.basicConfig(stream=sys.stdout,level=logging.DEBUG)

class StateMachine:
    def __init__(self):
        self.pipeline_init()
        self.change_state( 'InitialState')

    '''Create and init the pipeline''' 
    def pipeline_init(self):
        # Create the pipeline
        self.pipeline = gst.parse_launch('gconfaudiosrc ! audioconvert ! audioresample '
                                         + '! vader name=vad auto_threshold=true '
                                         + '! pocketsphinx name=asr ! fakesink')

        # Connect callbacks to the pocketsphinx component
        asr = self.pipeline.get_by_name('asr')
        asr.connect('result', self.asr_result)

    '''Update the pipeline configuration to use this state's configuration'''
    def change_state(self, new_state_class_name):
        clazz = getattr(__import__(__name__), new_state_class_name)
        self.current_state = clazz()

        # Modify the language model to the new state
        asr = self.pipeline.get_by_name('asr')
        if self.current_state.lm.lm_filename is not None:
            asr.set_property('lm', self.current_state.lm.lm_filename)
        if self.current_state.lm.dict_filename is not None:
            asr.set_property('dict', self.current_state.lm.dict_filename )
        asr.set_property('configured', True)

        logging.info("State changed. Active options: %s" % " ; ".join(self.current_state.keywords.keys()))

    # This is called from another thread so we need to be quick to process it
    def asr_result(self, asr, text, uttid):
        self.text_decoded = text

    # Main loop
    def run(self):
        self.pipeline.set_state(gst.STATE_PLAYING)
        while True:
            time.sleep(1)

            # There is an utterance waiting to be processed
            if hasattr(self,'text_decoded'):
                state_change = self.current_state.process( self.text_decoded)
                del self.text_decoded

                for state_transition_action in state_change:
                    logging.debug("Trying with %s" % type(state_transition_action))
                    # Execute transition function 
                    if type(state_transition_action) == types.FunctionType:
                        logging.debug("%s is a function" % state_transition_action)
                        state_transition_action()
                    # There has been a state change
                    else:
                        logging.debug("%s is a state class name" % state_transition_action)
                        # Pause the pipeline
                        self.pipeline.set_state(gst.STATE_PAUSED)
                        # Change the state
                        self.change_state( state_transition_action)
                        # Re-start the pipeline
                        self.pipeline.set_state(gst.STATE_PLAYING)

class State:
    def __init__(self):
        logging.info("Instantiating State class: %s" % self.__class__.__name__)
        if not hasattr(self,'lm'):
            logging.info("We need to create a LanguageModel for this State")
            commands_array = self.keywords.keys()
            self.lm = LanguageModel(self.__class__.__name__,commands_array)
            self.lm.update_all()
            logging.info("LanguageModel created")
        
    def process(self, text):
        state_change = []
        if text in self.keywords:
            state_change = self.keywords[text]
            if type(state_change) not in [list,tuple]:
                state_change = [ state_change ]
        logging.info('Processed text = %s with result = %s' % (text, state_change))
        return state_change

# Actual class model starts here:
class InitialState(State):
    lm = ManualLanguageModel('initial')   # Overrides automatic creation of language model
    keywords = {
        'MARY': 'Listening'
    }

class Listening(State):
    keywords = {
        'CANCEL': 'InitialState',
        'PLAY': (lambda: rc.play_radio_paradise(), 'PlayingMusic')
    }
    timeout = (10, 'InitialState')

class PlayingMusic(State):
    keywords = {
        'STOP': (lambda: rc.stop_playing(), 'Listening')
    }

if __name__ == '__main__':
    logging.info("Starting")
    s = StateMachine()
    s.run()

'''
Initial:
- (Mary, 'yes?'
'''