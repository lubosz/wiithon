#-*-coding: utf-8-*-
# http://crysol.org/es/node/911

import gtk
import gtk.glade

# Access to glade objects transparently
# Don't instantiate this class! Only inherit from it
class GladeWrapper:
    def __init__(self, glade_file, root_widget=None):
        self.__glade = gtk.glade.XML(glade_file, root_widget)
        self.__glade.signal_autoconnect(self)


    def get_widget(self, name):
        return self.__glade.get_widget(name)

    def __getattr__(self, name):
        try:
            return self.__dict__[name]

        except KeyError, e:
            if name.startswith("wg_"):
                try:
                    ret = self.__glade.get_widget(name[3:])
                except AttributeError:
                    raise AttributeError("You must call GladeWrapper.__init__() in your derived class")

                if ret:
                    self.__dict__[name] = ret
                    return ret

            raise AttributeError, "%s: %s" % (str(self.__class__), e)
