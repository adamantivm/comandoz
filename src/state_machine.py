import time
import gobject
import pygst
pygst.require('0.10')
gobject.threads_init()
import gst
import logging
import sys

logging.basicConfig(stream=sys.stdout)

class StateMachine:
    def __init__(self):
        self.pipeline_init()
        self.change_state( InitialState)

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
    def change_state(self, new_state_class):
        self.current_state = new_state_class()

        # Modify the language model to the new state
        asr = self.pipeline.get_by_name('asr')
        asr.set_property('lm', self.current_state.sphinx_lm)
        asr.set_property('dict', self.current_state.sphinx_dict)
        asr.set_property('configured', True)

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
                new_state_class = self.current_state.process( self.text_decoded)
                del self.text_decoded

                # There has been a state change
                if new_state_class is not None:
                    # Pause the pipeline
                    self.pipeline.set_state(gst.STATE_PAUSED)
                    # Change the state
                    self.change_state( new_state_class)
                    # Re-start the pipeline
                    self.pipeline.set_state(gst.STATE_PLAYING)

class State:
    sphinx_lm = 'models/2503.lm'
    sphinx_dict = 'models/2503.dic'
    
    def process(self, text):
        print text
        new_state = None
        orig_text = text
        if text in self.synonyms:
            text = self.synonyms[text]
        if text in self.keywords:
            new_state = self.keywords[text]
        logging.info('Processed text = %s with result = %s' % (orig_text, new_state))
        return new_state

class Listening:
    pass
class PlayingMusic:
    pass
class InitialState(State):
    keywords = {
        'mary': Listening
    }
    synonyms = {}

class Listening(State):
    keywords = {
        'cancel': InitialState,
        'play music': PlayingMusic
    }
    synonyms = {
        'cancel': ('no','go back')
    }
    timeout = (10, InitialState)

class PlayingMusic(State):
    keywords = {
        'stop': Listening
    }

if __name__ == '__main__':
    s = StateMachine()
    s.run()

'''
Initial:
- (Mary, 'yes?'
'''