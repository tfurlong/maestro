#!python
# SCons based build file for the property template crap
# Base file
import SCons;
import sys;
import os;
import string;
#import wing.wingdbstub;       # stuff for debugging
import SConsAddons.Util as sca_util

pj = os.path.join;

# Pyuic builder
def registerPyuicBuilder(env):
  #pyuic_build_str = 'pyuic4 -x -i3 -o $TARGET $SOURCE';
  pyuic_build_str = 'pyuic4 -x -i3 $SOURCE | grep -v "# Created: " > $TARGET';
  pyuic_builder = Builder(action = pyuic_build_str,
                          src_suffix = '.ui',
                          suffix = '.py');                            env.Append(BUILDERS = {'Pyuic' : pyuic_builder});

  #pyuic_build_str = 'pyrcc4 -compress 5 -o $TARGET $SOURCE';
  pyuic_build_str = 'pyrcc4 -compress 5 $SOURCE | grep -v "# Created: " > $TARGET';
  pyuic_builder = Builder(action = pyuic_build_str,
                          src_suffix = '.qrc',
                          suffix = '.py');                            env.Append(BUILDERS = {'Pyrcc' : pyuic_builder});
  #pyuic_build_str = 'pyuic4 -x -i3 -subimpl ${TARGET.filebase} -o $TARGET $SOURCE';
  #pyuic_builder = Builder(action = pyuic_build_str,
  #                        src_suffix = '.ui',
  #                        suffix = '.py');                            env.Append(BUILDERS = {'PyuicImpl' : pyuic_builder});


# ###############################
# Create builder
# ###############################

env = Environment(ENV=os.environ)

registerPyuicBuilder(env);    # Register custom builders


opts = Options(files = ['options.cache', 'options.custom']);  # Add options


# Python UI files
pyuic_src_files = []
for path, dirs, files in sca_util.WalkBuildFromSource('.',env):
   pyuic_src_files += [pj(path,f) for f in files if f.endswith('.ui')]

#print pyuic_src_files

pyuic_rc_files = []
for path, dirs, files in sca_util.WalkBuildFromSource('.',env):
   pyuic_rc_files += [pj(path,f) for f in files if f.endswith('.qrc')]

#print pyuic_rc_files

for sfile in pyuic_src_files:
  env.Pyuic(sfile);
for sfile in pyuic_rc_files:
  env.Pyrcc(sfile);

Default(".");
Help(help_text); 
