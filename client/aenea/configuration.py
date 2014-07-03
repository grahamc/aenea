import json
import os

import aenea.config


class ConfigWatcher(object):
    '''Watches a config file for changes, and reloads as necessary based on
       mtime. Path is relative to project root and may be string or list.
       Exceptions are squelched with a warning. File not existing is
       never an error.'''

    def __init__(self, path, default={}):
        if not isinstance(path, basestring):
            path = os.path.join(*path)
        self._path = path = os.path.join(aenea.config.PROJECT_ROOT, path) + '.json'
        self._mtime_size = (0, 0)
        self.conf = default
        self._exists = False
        self._default = default

        self.read()

    def __getitem__(self, item):
        self.refresh()
        return self.conf[item]

    def __setitem__(self, item, value):
        self.refresh()
        self.conf[item] = value

    def write(self):
        '''Writes the config file to disk.'''
        try:
            with open(self._path, 'w') as fd:
                json.dump(self.conf, fd)
        except Exception as e:
            print 'Error writing config file %s: %s.' % (self._path, str(e))

    def read(self):
        '''Forces to read the file regardless of whether it's mtime has
           changed.'''
        self._exists = os.path.exists(self._path)
        if not os.path.exists(self._path):
            self.conf = self._default.copy()
            return
        stat = os.stat(self._path)
        self._mtime_size = stat.st_mtime, stat.st_size
        try:
            with open(self._path) as fd:
                self.conf = json.load(fd)
        except Exception as e:
            print 'Error reading config file %s: %s.' % (self._path, str(e))

    def refresh(self):
        '''Rereads the file if it has changed. Returns True if it changed.'''
        if os.path.exists(self._path) != self._exists:
            self.read()
            return True

        if not os.path.exists(self._path):
            return False

        try:
            stat = os.stat(self._path)
            mtime = stat.st_mtime, stat.st_size
        except OSError:
            self.read()
            return True
        if mtime != self._mtime_size:
            self.read()
            return True
        return False


class ConfigDirWatcher(object):
    '''Watches a config directory for changes in it or its files, and reloads
       as necessary based on mtime. Path is relative to project root and may
       be string or list. Exceptions are squelched with a warning. Directory
       not existing is never an error.'''

    def __init__(self, path, default={}):
        self._rawpath = path
        if not isinstance(path, basestring):
            path = os.path.join(*path)
        self._path = path = os.path.join(aenea.config.PROJECT_ROOT, path)
        self.files = {}
        self._exists = False
        self._default = default

        self.read()

    def refresh(self):
        '''Rereads the directory if it has changed. Returns True if any files
           have changed.'''
        if os.path.exists(self._path) != self._exists:
            self.read()
            return True

        if not os.path.exists(self._path):
            return False

        files = set(x[:-5] for x in os.listdir(self._path)
                    if x.endswith('.json'))
        if set(files) != set(self.files):
            self.read()
            return True
        else:
            return any(c.refresh() for c in self.files.itervalues())

    def read(self):
        self._exists = os.path.exists(self._path)
        if not os.path.exists:
            self.files.clear()
            return

        files = set(x[:-5] for x in os.listdir(self._path)
                    if x.endswith('.json'))
        for k in self.files.keys():
            if k not in files:
                del self.files[k]

        for fn in files:
            if fn not in self.files:
                self.files[fn] = ConfigWatcher(
                    (self._rawpath, fn), self._default)
            else:
                self.files[fn].refresh()


def make_grammar_commands(module_name, mapping, config_key='commands'):
    '''Given the command map from default spoken phrase to actions in mapping,
       constructs a mapping that takes user config, if specified, into account.
       config_key may be a key in the JSON to use (for modules with multiple
       mapping rules.) If a user phrase starts with !,
       no mapping is generated for that phrase.'''
    conf_path = ('grammar_config', module_name)
    conf = ConfigWatcher(conf_path).conf.get(config_key, {})
    commands = mapping.copy()

    # Nuke the default if the user sets one or more aliases.
    for default_phrase in set(conf.itervalues()):
        del commands[str(default_phrase)]

    for (user_phrase, default_phrase) in conf.iteritems():
        # Dragonfly chokes on unicode, JSON's default.
        user_phrase = str(user_phrase)
        default_phrase = str(default_phrase)
        assert default_phrase in mapping, ('Invalid mapping value in module %s config_key %s: %s' % (module_name, config_key, default_phrase))

        # Allow users to nuke a command with !
        if not user_phrase.startswith('!'):
            commands[user_phrase] = mapping[default_phrase]
    return commands
