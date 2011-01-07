# Translation Library
# 
# Translations in DTWM turn Facebook data into generalized terms for comparison
# The premise is that most people don't have overlapping likes, movies, books, etc...
# What these libraries do is translate "media objects" into higher level data.
#
# For example:
#   If somebody has True Grit as a movie they like, the movie translator (MovieTranslator) will turn that into:
#       - directors: Ethan Coen, Joel Coen
#       - actors: Jeff Bridges, Matt Damon and Hailee Steinfeld
#       - genres: Adventure, Drama, Western
#   This data is then fed into the EventFinder subclass MovieEventFinder

class Translator(object):
    """ The root translation class """
    def __init__(self, user):
        pass
    
class MovieTranslator(Translator):
    """ The movie translator class """
    pass
    
class BookTranslator(Translator):
    """ The book translator class """
    pass

class TelevisionTranslator(Translator):
    """ The TV show translator class """
    pass
    
class InterestsTranslator(Translator):
    """ The interests translator class """
    pass
    
class MusicTranslator(Translator):
    """ The music translator class """
    pass
    
class LikeTranslator(Translator):
    """ The like translator """
    # this one is probably the hardest to implement... no idea how to do this yet
    pass

class EventTranslator(Translator):
    """ The event translator. Translates the user's past events. """ 
    pass
    