#-*-coding: utf-8-*-

class NonRepeatList(list):
    def __init__(self, *args):
        list.__init__(self, *args)

    def append(self, element):
        if not self.count(element):
            list.append(self, element)

    def extend(self, iterable):
        for i in iterable:
            self.append(i)


class Observable:
    def __init__(self, topic_list):
        self.__observers = {}

        for topic in topic_list:
            self.__observers[topic] = []


    def subscribe(self, topic, callback):
        if isinstance(topic, list):
            for t in topic:
                if self.__observers.has_key(t):
                    # ESTO PETA
                    self.__observers[t].append(callback)

                else:
                    raise SubscriptionError(t)

        else:
            if self.__observers.has_key(topic):
                self.__observers[topic].append(callback)

            else:
                raise SubscriptionError(topic)

    def notify(self, topic, what):
        if self.__observers.has_key(topic):
            for observer_cb in self.__observers[topic]:
                observer_cb(what)

        else:
            print 'revisa código macho, que el topic no existe'



class SubscriptionError(Exception):
    def __init__(self, topic=None):
        Exception.__init__(self)
        if topic:
            self.msg = 'The topic "%s" doesn\'t exist' %(topic)

        else:
            self.msg = 'Topic not exist'

    def __str__(self):
        return self.msg




