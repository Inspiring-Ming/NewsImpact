"""IDENTITY - who is using the product, and what they may do.

A User has an id, an optional email and roles ("admin" may run updates and
change settings). The Authenticator port turns a request's sign-in token into
a User. Adapters:
  local.py    one built-in admin user, no sign-in (a single person on their own
              computer; today's setup)
  (next)      cognito.py: verifies Amazon Cognito sign-in tokens, so many people
              can register; one entry in app/wiring/plugins.py AUTH

Everything per person (followed companies, alerts) is stored under user_id.
Publishes: nothing. Consumes: nothing (the API asks it on every request).
"""
