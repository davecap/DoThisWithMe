# The events classes
# Each of these classes implements an API that primarily finds events based on a location
# These classes can also filter by "translated preferences" (data generated from the Translator classes)
# Event finders must be able to handle request failures... since lots of APIs have request limits per day
# Logging of this data is important
#
# Basically, we will wrap a bunch of APIs.
#
# DTWM will support the following event types:
#
#   - Open and Friends' Facebook events
#   - Movies
#   - Concerts / Festivals3
#   - Other local events (Upcoming.org, Plancast, Outside.in, Meetup)
#
# Potential event types:
#   - Groupon?
#   - Restaurants (Yelp? hard to suggest restaurants based on FB data) 

# TODO:
#   - models for event data storage?
#   - cleaning up stored events that have passed?
#   - memcache?
#