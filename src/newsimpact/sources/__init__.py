"""SOURCES - which news outlets we read, and how we collect their articles.

Start with a few outlets, add more later:
  * The outlets are a curated list in data/reference/sources.json. To add an
    outlet, add one row to that file. No code change is needed.
  * To support a new kind of feed (e.g. a licensed news API), add one file in
    adapters/ and register its `kind` in app/wiring.py.
  * Articles from outlets that are not on the list are ignored unless
    NI_ACCEPT_UNLISTED_SOURCES=true. Reliability is only meaningful for
    outlets we track.

Publishes: SourceRegistered, ArticleIngested
Consumes:  StorylineUpdated (searches the listed outlets for a story's next chapter)
"""
