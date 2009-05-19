#!/usr/bin/python
# vim: set fileencoding=utf-8 :
# http://crysol.org/es/node/911

import gtk
import gtk.glade

class GladeWrapper:
    def __init__(self, glade_file, root_widget=None):
        # glade esta siendo abandonado en lugar de gtk.Builder
        # svn co http://svn.gnome.org/svn/glade3/trunk glade3
        # Mini tutorial http://www.danigm.net/node/71
	self.__glade = gtk.Builder()
	self.__glade.add_from_file( glade_file )
	self.__glade.set_translation_domain("wiithon")
	self.__glade.connect_signals(self)

    def get_widget(self, name):
        return self.__glade.get_object(name)

    def __getattr__(self, name):
        try:
            return self.__dict__[name]

        except KeyError, e:
            if name.startswith("wg_"):
                try:
                    ret = self.__glade.get_object(name[3:])
                except AttributeError:
                    raise AttributeError( "You must call GladeWrapper.__init__() in your derived class" )

                if ret:
                    self.__dict__[name] = ret
                    return ret

            raise AttributeError, "%s: %s" % (str(self.__class__), e)

