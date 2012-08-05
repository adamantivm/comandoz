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
        self.current_state = None
        self.change_state( 'Idle')

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
    def change_state(self, new_state_class_name, restart_pipeline=False):
        old_state = self.current_state
        clazz = getattr(__import__(__name__), new_state_class_name)
        self.current_state = clazz()
        
        logging.info("State changed. New state = [%s]" % self.current_state)

        if old_state is None or old_state.lm != self.current_state.lm:
            if restart_pipeline:
                # Pause the pipeline
                self.pipeline.set_state(gst.STATE_PAUSED)
    
            # Modify the language model to the new state
            asr = self.pipeline.get_by_name('asr')
            if self.current_state.lm.lm_filename is not None:
                asr.set_property('lm', self.current_state.lm.lm_filename)
            if self.current_state.lm.dict_filename is not None:
                asr.set_property('dict', self.current_state.lm.dict_filename )
            asr.set_property('configured', True)
    
            logging.info("Active options now: %s" % " ; ".join(self.current_state.keywords.keys()))
    
            if restart_pipeline:
                # Re-start the pipeline
                self.pipeline.set_state(gst.STATE_PLAYING)

# SCREENSAVER_START / _STOP

    # This is called from another thread so we need to be quick to process it
    def asr_result(self, asr, text, uttid):
        self.text_decoded = text

    # Main loop
    def run(self):
        self.pipeline.set_state(gst.STATE_PLAYING)
        tics = 0
        context = 'menu'
        while True:
            time.sleep(1)
            tics += 1
            
            # Once every 10 tics, check to see if the context changed
            if tics > 9:
                tics = 0
                new_context = rc.read_context()
                if new_context != context:
                    logging.debug("There is a new context = %s" % new_context)
                    context = new_context
                    # Context is changed, switch states if appropriate
                    if hasattr(self.current_state,'context') and new_context in self.current_state.context:
                        self.change_state( self.current_state.context[new_context], True)

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
                        # Change the state
                        self.change_state( state_transition_action, True)


class State:
    def __init__(self):
        logging.info("Instantiating State class: %s" % self.__class__.__name__)
        #self.lm = all_state_lm
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
class Base(State):
    keywords = {
        'LOUDER': 'Base',
        'QUIETER': 'Base'
    }
    context = {
        'audio': 'PlayingMedia',
        'video': 'PlayingMedia'
    }
class Idle(Base):
    keywords = {
        'PLAY MUSIC': 'SelectMedia',
        'PLAY VIDEO': 'SelectMedia'
    }
class SelectMedia(Base):
    keywords = {
        'RADIO PARADISE': (lambda: rc.play_radio_paradise(), 'PlayingMedia'),
        'CANCEL': 'Idle'
    }
class PlayingMedia(Base):
    keywords = {
        'STOP': (lambda: rc.stop_playing(), 'Idle')
    }
    context = {
        'menu': 'Idle'
    }

# Create a LanguageModel that supports all the keywords defined in all the States
keywords = []
for state in [Base,Idle,SelectMedia,PlayingMedia]:
    keywords += state.keywords.keys()
all_state_lm = LanguageModel('all_state_lm', keywords)
all_state_lm.update_all()
Base.lm = all_state_lm
    
#########################################
# Old states - OBSOLETE
#########################################
    
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