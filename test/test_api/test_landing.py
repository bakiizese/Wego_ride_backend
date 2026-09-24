#!/usr/bin/python
def test_landing_page_is_served_at_root(client):
    r = client.get("/")

    assert r.status_code == 200
    assert b"Wego Ride" in r.data
    # relative on purpose: the same page is also served from the Cloudflare
    # front (which proxies /apidocs/ to Render), so it must not hardcode a host
    assert b'href="/apidocs/"' in r.data


def test_favicon_is_served(client):
    r = client.get("/favicon.svg")

    assert r.status_code == 200
    assert r.mimetype == "image/svg+xml"
