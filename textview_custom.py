#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import gtk
import pango
import libxml2

import util

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
                    elif nodo.name == 'pr':
                        self.imprimir(nodo.content)
                    else:                    
                        self.activarTag(nodo.name)
                        recorrer_nodo(nodo.children)
                        self.desactivarTag(nodo.name)
                nodo = nodo.next

        self.buffer.set_text('')
        doc = libxml2.parseDoc(xml)
        ctxt = doc.xpathNewContext()
        try:
            nodo = ctxt.xpathEval("//*[name() = 'xhtml']")[0]
            recorrer_nodo(nodo.children)
        except IndexError:
            pass
        ctxt.xpathFreeContext()
        doc.freeDoc()
               
    def cargar_tags_html(self):
        a = self.nuevoTag
        a("h1", underline=pango.UNDERLINE_SINGLE, size=17 * pango.SCALE, foreground='darkgray')
        a("rojo", foreground='red')
        a("verde", foreground='darkgreen')
        a("azul", foreground='blue')
        a("gris", foreground='darkgray')
        a("superbig", size=18 * pango.SCALE)
        a("big", size=14 * pango.SCALE)
        a("small", size=7 * pango.SCALE)
        a("b", weight=pango.WEIGHT_BOLD)
        a("i", style=pango.STYLE_ITALIC)
        a("u", underline=pango.UNDERLINE_SINGLE)
        a("justificar", justification=gtk.JUSTIFY_FILL)
        a("margin8", left_margin=8, right_margin=8)
        a("margin12", left_margin=12, right_margin=12)

    def cargar_otros_tags(self):
        # http://www.pygtk.org/docs/pygtk/class-gtktexttag.html
        a("strikethrough", strikethrough=True)
        a("underline",underline=pango.UNDERLINE_SINGLE)
        a("superscript",rise=5 * pango.SCALE, size=8 * pango.SCALE)
        a("fg_black", foreground="black")
        a("fg_gray", foreground="gray")
        a("fg_darkgray", foreground="darkgray")
        a("fg_red", foreground="red")
        a("fg_blue", foreground="blue")
        a("fg_green", foreground="green")
        a("fg_darkcyan", foreground="darkcyan")
        a("fg_purple", foreground="purple")
        a("bg_white", background="white")
        a("bg_cyan", background="cyan")
        a("bg_green", background="green")
        a("bg_blue", background="blue")
        a("bg_lightgray", background="lightgray")
        a("bg_lightgreen", background="lightgreen")
        a("bg_hotpink", background="hotpink")
        a("bg_yellow", background="yellow")
        a("bg_lightyellow", background="lightyellow")
        a("bg_mistyrose", background="mistyrose")
        a("bg_lightblue", background="lightblue")
        a("bg_khaki", background="khaki")
        a("bg_selected", background="yellow")
        a("bold", weight=pango.WEIGHT_BOLD)
        a("italic", style=pango.STYLE_ITALIC)
        a("big_gap_before_line", pixels_above_lines=30)
        a("big_gap_after_line", pixels_below_lines=30)
        a("wide_margins", left_margin=10, right_margin=10)
