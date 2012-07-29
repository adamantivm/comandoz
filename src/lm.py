import os
import subprocess
from subprocess import CalledProcessError

# TODO: learn and use pythonic practice for finding
# files in the right locations

'''
LanguageModel class.
Used to abstract access to model files and creation of them
It is instantiated by creating an instance with a given file name
It works with files created in the 'data' directory (variable base_dir)
As input, it expects a <name>.vocab file as input to exist in the data directory
It will produce and use a <name>.lm and <name>.dic file also in the same directory

Files:
- <name>.input --> input file. List of commands you want to use
- <name>.lm ---> lm file
- <name>.dic --> dictionary file
- <name>.vocab --> vocabulary file (one WORD per line)
- <name>.sent --> sentence file (starts and ends for <s> </s>)
'''
class LanguageModel:
    def __init__(self, name, input_array=None):
        self.base_dir = os.getenv('CZ_DATA_DIR','data')
        self.main_dict = self.base_dir + os.sep + 'cmu07a.dic'
        self.context_filename = self.base_dir + os.sep + 'default.ccm'
        
        # These files are mandatory for operation
        if not os.path.exists( self.main_dict):
            raise Exception("Missing base dictionary file: %s" % self.main_dict)
        if not os.path.exists( self.context_filename):
            try:
                self.write_file( self.context_filename, "<s>\n</s>\n")
            except:
                raise Exception("Couldn't find nor create context cues file: %s" % self.context_filename)

        # Input data
        self.name = name
        self.input_filename = self.base_dir + os.sep + self.name + ".input"
        self.input_commands = self.get_input_commands()
        
        # If an array of commands is provided as input check, use that one unless
        # it's the same as the one on disk - in that case don't save to avoid
        # altering the timestamps
        if input_array is not None and \
            (self.input_commands is None or input_array.sort() != self.input_commands.sort()):
                self.input_commands = input_array
                self.write_file( self.input_filename, self.input_commands)

        # Can't work without input!
        if self.input_commands is None:
            raise Exception("Missing input file (%s) or input command array" % self.input_filename)
        
        # Output files
        self.lm_filename = self.base_dir + os.sep + self.name + ".lm"
        self.dict_filename = self.base_dir + os.sep + self.name + ".dic"
        
        # Optional files
        self.sentences_filename = self.base_dir + os.sep + self.name + ".sent"

        # Intermediate files
        self.vocab_filename = self.base_dir + os.sep + self.name + ".vocab"
        self.idngram_filename = self.base_dir + os.sep + self.name + ".idngram"
    
    '''Creates all necessary language model files for functioning'''
    def update_all(self,force=False):
        self.update_dict(force)
        self.update_lm(force)
        self.delete_intermediate_files()

    '''Creates or updates the .dic file for this model'''
    def update_dict(self, force=False):
        if self.good_and_current_file( self.dict_filename) and not force:
            return

        dict_array = []
        for term in self.get_vocabulary():
            if term.find('S>') != -1:
                continue
            try:
                dict_term = subprocess.check_output(["grep","-i","^%s\s" % term,"%s" % self.main_dict])
                dict_array.append( dict_term.strip())
            except CalledProcessError:
                raise Exception("Term not found in master dictionary: %s" % term)

        self.write_file( self.dict_filename, dict_array)
        return dict_array
    
    def update_lm(self, force=False):
        if self.good_and_current_file( self.lm_filename) and not force:
            return
        
        self.update_sentences()
        self.update_vocabulary()
        
        os.system("text2idngram -vocab %s -idngram %s < %s" %
            (self.vocab_filename,self.idngram_filename,self.sentences_filename))
        os.system("idngram2lm -absolute -context %s -vocab_type 0 -idngram %s -vocab %s -arpa %s" %
            (self.context_filename, self.idngram_filename,self.vocab_filename,self.lm_filename))

    def get_vocabulary(self):
        if not self.good_and_current_file( self.vocab_filename):
            self.update_vocabulary()
        return self.read_file( self.vocab_filename)

    def update_vocabulary(self, force=False):
        if self.good_and_current_file( self.vocab_filename) and not force:
            return
        self.update_sentences()
        os.system("text2wfreq < %s | wfreq2vocab | grep -v '##' > %s" % (self.sentences_filename,self.vocab_filename))

    def update_sentences(self, force=False):
        if self.good_and_current_file( self.sentences_filename) and not force:
            return
        sentences = map(lambda x: "<s> %s </s>" % x.upper(), self.input_commands)
        self.write_file( self.sentences_filename, sentences)
        return sentences
    
    def delete_intermediate_files(self):
        if os.path.exists( self.idngram_filename):
            os.unlink( self.idngram_filename)
        if os.path.exists( self.vocab_filename):
            os.unlink( self.vocab_filename)

    def write_file(self, filename, array):
        f = open( filename, 'w')
        for line in array:
            f.write( "%s\n" % line)
        f.close()

    def read_file(self, filename):
        f = open( filename)
        array = map(lambda x: x.strip().upper(), f.readlines())
        f.close()
        return array

    def get_input_commands(self):
        if os.path.exists(self.input_filename) and os.path.getsize(self.input_filename) != 0:
            return self.read_file( self.input_filename)

    '''Checks whether a given file exists, it's not empty and it's newer than the
        input file'''
    def good_and_current_file(self, filename):
        if not os.path.exists( filename):
            # Missing file
            return False
        if os.path.getsize( filename) == 0:
            # Empty file
            return False
        if os.path.getmtime( filename) < os.path.getmtime( self.input_filename):
            # File is outdated
            return False
        return True
    
    '''Checks whether the given model name is up to date and ready to use'''
    def is_ready(self):
        if not self.good_and_current_file( self.lm_filename):
            return False
        if not self.good_and_current_file( self.dict_filename):
            return False
        return True

'''A LM file that doesn't do any of the LM creation magic. Used simply as
   a data object to keep the file names of the lm and dict files, or provide defaults'''
# TODO: Implement something useful here
class ManualLanguageModel(LanguageModel):
    def __init__(self, name):
        self.name = name
        self.lm_filename = None
        self.dict_filename = None

        