#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import os
import gtk
import pango
import libxml2

import util
import config

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
            
    def imprimir_imagen(self, ruta):
        if os.path.exists(ruta):
            iter = self.buffer.get_end_iter()
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(ruta, -1, config.SIZE_IMAGE_ACCESORIOS)
            self.buffer.insert_pixbuf( iter, pixbuf )
        elif config.DEBUG:
            print _("Falta la imagen %s") % ruta

    def render_xml(self, xml):

        def recorrer_nodo(nodo):
            while nodo is not None:
                if nodo.type == 'element':
                    
                    if nodo.name == 'br':
                        self.imprimir('\n')
                    elif nodo.name == 'pr':
                        self.imprimir(nodo.content)
                    elif nodo.name == 'img':
                        self.imprimir_imagen(nodo.content)
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
        a("negro", foreground='black')
        a("rojo", foreground='red')
        a("naranja", foreground='orange')
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
        for i in range(64):
            a("font%d" % i, size=i * pango.SCALE)    

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
        
        '''
  insert_one_tag_into_buffer(buffer, "heading", "weight", pango.WEIGHT_BOLD,
                     "size", 15 * PANGO_SCALE)
  
  insert_one_tag_into_buffer(buffer, "italic", "style", pango.STYLE_ITALIC)

  insert_one_tag_into_buffer(buffer, "bold", "weight", pango.WEIGHT_BOLD)  
  
  insert_one_tag_into_buffer(buffer, "big", "size", 20 * PANGO_SCALE)
  # points times the PANGO_SCALE factor
  
  insert_one_tag_into_buffer(buffer, "xx-small", "scale", pango.SCALE_XX_SMALL)

  insert_one_tag_into_buffer(buffer, "x-large", "scale", pango.SCALE_X_LARGE)
  
  insert_one_tag_into_buffer(buffer, "monospace", "family", "monospace")
  
  insert_one_tag_into_buffer(buffer, "blue_foreground", "foreground", "blue")  

  insert_one_tag_into_buffer(buffer, "red_background", "background", "red")

  #stipple = gtk.gdk.Pixmap(None,
  #                         gray50_bits, gray50_width,
  #                         gray50_height)
  
  #insert_one_tag_into_buffer(buffer, "background_stipple", "background_stipple", stipple)

  #insert_one_tag_into_buffer(buffer, "foreground_stipple", "foreground_stipple", stipple)

  #stipple = None

  insert_one_tag_into_buffer(buffer, "big_gap_before_line", "pixels_above_lines", 30)

  insert_one_tag_into_buffer(buffer, "big_gap_after_line", "pixels_below_lines", 30)

  insert_one_tag_into_buffer(buffer, "double_spaced_line", "pixels_inside_wrap", 10)

  insert_one_tag_into_buffer(buffer, "not_editable", "editable", gtk.FALSE)
  
  insert_one_tag_into_buffer(buffer, "word_wrap", "wrap_mode", gtk.WRAP_WORD)

  insert_one_tag_into_buffer(buffer, "char_wrap", "wrap_mode", gtk.WRAP_CHAR)

  insert_one_tag_into_buffer(buffer, "no_wrap", "wrap_mode", gtk.WRAP_NONE)
  
  insert_one_tag_into_buffer(buffer, "center", "justification", gtk.JUSTIFY_CENTER)

  insert_one_tag_into_buffer(buffer, "right_justify", "justification", gtk.JUSTIFY_RIGHT)

  insert_one_tag_into_buffer(buffer, "wide_margins", "left_margin", 50, "right_margin", 50)
  
  insert_one_tag_into_buffer(buffer, "strikethrough", "strikethrough", gtk.TRUE)
  
  insert_one_tag_into_buffer(buffer, "underline", "underline", pango.UNDERLINE_SINGLE)

  insert_one_tag_into_buffer(buffer, "double_underline", "underline", pango.UNDERLINE_DOUBLE)

  insert_one_tag_into_buffer(buffer, "superscript", "rise", 10 * PANGO_SCALE, 
			      "size", 8 * PANGO_SCALE)
  
  insert_one_tag_into_buffer(buffer, "subscript", "rise", -10 * PANGO_SCALE,
			      "size", 8 * PANGO_SCALE)

  insert_one_tag_into_buffer(buffer, "rtl_quote",
                             "wrap_mode", gtk.WRAP_WORD,
                             "direction", gtk.TEXT_DIR_RTL,
                             "indent", 30,
                             "left_margin", 20,
                             "right_margin", 20)

        '''
