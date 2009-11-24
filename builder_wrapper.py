#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
# http://crysol.org/es/node/911

'''
Wrapper to use gtk.Builder() class on derived classes
'''

import gtk

import config

class GtkBuilderWrapper:
    '''Class used to inherit and use the adventages of Builder
    '''
    def __init__(self, builder_file):
        self.__builder = gtk.Builder()
        self.__builder.add_from_file( builder_file )
        self.__builder.set_translation_domain( config.APP )
        self.__builder.connect_signals(self)

    def get_widget(self, name):
        '''Used to get widgets directly by name. Deprecated method,
        use get_object instead
        '''
        return self.__builder.get_object(name)

    def get_object(self, name):
        '''Used to get widgets directly by name
        '''
        return self.__builder.get_object(name)

    def __getattr__(self, name):
        '''Return the widget on Builder user interface named
        with the var name after the wb_ prefix
        '''
        try:
            return self.__dict__[name]

        except KeyError, exception:
            if name.startswith("wb_"):
                try:
                    ret = self.__builder.get_object(name[3:])
                except AttributeError:
                    raise AttributeError(
                        "You must call GtkBuildWrapper.__init__()" + \
                        "in your derived class")


                if ret:
                    self.__dict__[name] = ret
                    return ret

            raise AttributeError, "%s: %s" % (str(self.__class__), exception)

