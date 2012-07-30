import os
import subprocess
from subprocess import CalledProcessError
import mechanize

# TODO: learn and use pythonic practice for finding
# files in the right locations

'''
LanguageModel class.
Used to abstract access to model files and creation of them
It is instantiated by creating an instance with a given file name
It works with files in the 'data' directory (variable base_dir) and
produces model files in the 'model' directory (variable work_dir)
As input, it expects a <name>.input file as input to exist in the data directory
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
        self.work_dir = os.getenv('CZ_WORK_DIR','model')

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

        # Work dir
        if not os.path.exists(self.work_dir):
            try:
                os.mkdir( self.work_dir)
            except:
                raise Exception("Couldn't create or use work directory: %s" % self.work_dir)

        # Input data
        self.name = name
        self.input_filename = self.work_dir + os.sep + self.name + ".input"
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
        self.lm_filename = self.work_dir + os.sep + self.name + ".lm"
        self.dict_filename = self.work_dir + os.sep + self.name + ".dic"
        
    '''Creates all necessary language model files for functioning'''
    def update_all(self,force=False):
        if self.good_and_current_file( self.dict_filename) and \
            self.good_and_current_file( self.lm_filename) and \
            not force:
            return
        
        br = mechanize.Browser()
        br.set_handle_robots(False)
        br.open("http://www.speech.cs.cmu.edu/tools/lmtool-new.html")
        br.select_form(nr=0)
        br.form.add_file(open(self.input_filename), 'text/plain', self.input_filename)
        br.submit()
        dict_contents = br.follow_link(text_regex=r".*\.dic", nr=0)
        dict_contents = dict_contents.read()
        br.back()
        lm_contents = br.follow_link(text_regex=r".*\.lm", nr=0)
        lm_contents = lm_contents.read()

        dict_f = open( self.dict_filename, 'w')
        dict_f.write( dict_contents)
        dict_f.close()
        lm_f = open( self.lm_filename, 'w')
        lm_f.write( lm_contents)
        lm_f.close()
        
    '''Deletes .lm and .dic files from directory'''
    def reset_files(self):
        os.unlink( self.dict_filename)
        os.unlink( self.lm_filename)

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

        