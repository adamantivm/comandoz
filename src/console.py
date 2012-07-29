import time
import gobject
import pygst
pygst.require('0.10')
gobject.threads_init()
import gst

class ConsoleRecorder:
    def __init__(self):
        # Create the pipeline
        self.pipeline = gst.parse_launch('gconfaudiosrc ! audioconvert ! audioresample '
                                         + '! vader name=vad auto_threshold=true '
                                         + '! pocketsphinx name=asr ! fakesink')

        # Connect callbacks to the pocketsphinx component
        asr = self.pipeline.get_by_name('asr')
        asr.connect('partial_result', self.asr_partial_result)
        asr.connect('result', self.asr_result)

        # Tune to particular language model
        asr.set_property('lm', 'data/3585.lm')
        asr.set_property('dict', 'data/3585.dic')
 
        # We need to convince it that we're done configuring it apparently
        asr.set_property('configured', True)

        # Start the pipeline
        self.pipeline.set_state(gst.STATE_PLAYING)

    # callbacks where we receive the utterances
    def asr_partial_result(self, asr, text, uttid):
        pass
    def asr_result(self, asr, text, uttid):
        print "result %s: %s" % (uttid, text)

    # Stop the recorder
    def stop(self):
        self.pipeline.set_state(gst.STATE_PAUSED)

if __name__ == '__main__':
    recorder = ConsoleRecorder()
    #gtk.main()
    while True:
        time.sleep(1)
    recorder.stop()
