#!/usr/bin/python
def test_landing_page_is_served_at_root(client):
    r = client.get("/")

    assert r.status_code == 200
    assert b"Wego Ride" in r.data
    # the same file is hosted on another domain, so links must be absolute
    assert b'href="/apidocs/"' not in r.data
    assert b"https://wego-ride-backend.onrender.com/apidocs/" in r.data
