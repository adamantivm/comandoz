import gst
import time
import gtk

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
        # We need to convince it that we're done configuring it apparently
        asr.set_property('configured', True)

        # Create the mechanics for transferring data from callbacks (which can't do
        # anything apparently) to the actual application
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::application', self.application_message)
        
        # Start the pipeline
        self.pipeline.set_state(gst.STATE_PLAYING)
        
    # Create callback proxies, which will in turn call the mechanism to actually
    # transfer the information to the application callbacks
    def asr_partial_result(self, asr, text, uttid):
        """Forward partial result signals on the bus to the main thread."""
        struct = gst.Structure('partial_result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', uttid)
        asr.post_message(gst.message_new_application(asr, struct))
    def asr_result(self, asr, text, uttid):
        """Forward result signals on the bus to the main thread."""
        struct = gst.Structure('result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', uttid)
        asr.post_message(gst.message_new_application(asr, struct))
    def application_message(self, bus, msg):
        """Receive application messages from the bus."""
        msgtype = msg.structure.get_name()
        if msgtype == 'partial_result':
            self.partial_result(msg.structure['hyp'], msg.structure['uttid'])
        elif msgtype == 'result':
            self.final_result(msg.structure['hyp'], msg.structure['uttid'])

    # Here are the actual callbacks
    def partial_result(self, hyp, uttid):
        pass
    def final_result(self, hyp, uttid):
        print "result %s: %s" % (uttid, hyp)

    # Stop the recorder
    def stop(self):
        self.pipeline.set_state(gst.STATE_PAUSED)
        

if __name__ == '__main__':
    recorder = ConsoleRecorder()
    gtk.main()
    while True:
        time.sleep(1)
    recorder.stop()

