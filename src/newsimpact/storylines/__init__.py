"""STORYLINES - link related news over time into one evolving story, and say
which decisions each stage typically triggers.

Example: public apology -> CEO steps down -> successor named. Each kind of
story is a playbook in data/reference/playbooks.json (editable by analysts).
For every open story it asks the sources module to search for the next stage.

Publishes: StorylineUpdated
Consumes:  ClaimsScored
"""
