#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import gtk
import libxml2

class TagCustom(gtk.TextTag):
    
    def __init__(self, name):
        gtk.TextTag.__init__(self, name=name)
        self.desactivar()
        
    def activar(self):
        self.activado = True
        
    def desactivar(self):
        self.activado = False

class TextViewCustom(gtk.TextView):

    def __init__(self):
        gtk.TextView.__init__(self)
        self.tabla = gtk.TextTagTable()
        self.buffer = gtk.TextBuffer(self.tabla)
        self.buffer.connect_after("insert-text", self.bufferInsert)
        self.set_buffer(self.buffer)
        self.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self.set_editable(False)
        self.set_cursor_visible(False)

    def nuevoTag(self, name ,**kwargs):
        tag = TagCustom(name)
        for key,val in kwargs.items():
            tag.set_property(key,val)
        self.tabla.add(tag)
        return tag

    def bufferInsert(self, buffer, itter, insertado, length):
        
        def aplicarTag(tag, datos):
            if tag.activado:
                buffer.apply_tag(tag, datos[0], datos[1])
        
        end = buffer.get_iter_at_mark(buffer.get_insert())
        start = end.copy()
        start.backward_chars(length)
        self.tabla.foreach(aplicarTag, (start, end))
        self.queue_draw()
    
    def imprimir(self, texto = ''):    
        self.buffer.insert_at_cursor("%s" % texto)
        
    def activarTag(self, name):
        tag = self.tabla.lookup(name)
        if tag is not None:
            tag.activar()
        
    def desactivarTag(self, name):
        tag = self.tabla.lookup(name)
        if tag is not None:
            tag.desactivar()

    def render_xml(self, xml):

        def recorrer_nodo(nodo):
            while nodo is not None:
                if nodo.type == 'element':
                    
                    if nodo.name == 'br':
                        self.imprimir('\n')
                    else:                    
                        self.activarTag(nodo.name)
                        if nodo.children.next == None:
                            self.imprimir(nodo.content.strip())
                        recorrer_nodo(nodo.children)
                        self.desactivarTag(nodo.name)
                nodo = nodo.next

        doc = libxml2.parseDoc(xml)
        ctxt = doc.xpathNewContext()
        nodo = ctxt.xpathEval("//*[name() = 'plantilla']")[0]
        recorrer_nodo(nodo.children)
        ctxt.xpathFreeContext()
        doc.freeDoc()

        # examples
        # http://www.pygtk.org/docs/pygtk/class-gtktexttag.html
        '''
        #import pango
        #a(b("strikethrough", strikethrough=True))
        #a(b("underline",underline=pango.UNDERLINE_SINGLE))
        #a(b("superscript",rise=5 * pango.SCALE, size=8 * pango.SCALE))
        #a(b("fg_black", foreground="black"))
        #a(b("fg_gray", foreground="gray"))
        #a(b("fg_darkgray", foreground="darkgray"))
        #a(b("fg_red", foreground="red"))
        #a(b("fg_blue", foreground="blue"))
        #a(b("fg_green", foreground="green"))
        #a(b("fg_darkcyan", foreground="darkcyan"))
        #a(b("fg_purple", foreground="purple"))
        #a(b("bg_white", background="white"))
        #a(b("bg_cyan", background="cyan"))
        #a(b("bg_green", background="green"))
        #a(b("bg_blue", background="blue"))
        #a(b("bg_lightgray", background="lightgray"))
        #a(b("bg_lightgreen", background="lightgreen"))
        #a(b("bg_hotpink", background="hotpink"))
        #a(b("bg_yellow", background="yellow"))
        #a(b("bg_lightyellow", background="lightyellow"))
        #a(b("bg_mistyrose", background="mistyrose"))
        #a(b("bg_lightblue", background="lightblue"))
        #a(b("bg_khaki", background="khaki"))
        #a(b("bg_selected", background="yellow"))
        #a(b("bold", weight=pango.WEIGHT_BOLD))
        #a(b("italic", style=pango.STYLE_ITALIC))
        #a(b("big_gap_before_line", pixels_above_lines=30))
        #a(b("big_gap_after_line", pixels_below_lines=30))
        #a(b("wide_margins", left_margin=10, right_margin=10))
        '''

