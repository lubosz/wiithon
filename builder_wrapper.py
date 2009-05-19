#!/usr/bin/python
# vim: set fileencoding=utf-8 :
# http://crysol.org/es/node/911

import gtk

class GtkBuilderWrapper:
    def __init__(self, builder_file, root_widget=None):
        # glade esta siendo abandonado en lugar de gtk.Builder
        # svn co http://svn.gnome.org/svn/glade3/trunk glade3
        # Mini tutorial http://www.danigm.net/node/71
	self.__builder = gtk.Builder()
	self.__builder.add_from_file( builder_file )
	self.__builder.set_translation_domain("wiithon")
	self.__builder.connect_signals(self)

    def get_widget(self, name):
        return self.__builder.get_object(name)

    def __getattr__(self, name):
        try:
            return self.__dict__[name]

        except KeyError, e:
            if name.startswith("wb_"):
                try:
                    ret = self.__builder.get_object(name[3:])
                except AttributeError:
                    raise AttributeError( "You must call GtkBuildWrapper.__init__() in your derived class" )

                if ret:
                    self.__dict__[name] = ret
                    return ret

            raise AttributeError, "%s: %s" % (str(self.__class__), e)

