import httpx, os, time

print("HTTP_PROXY:", repr(os.environ.get("HTTP_PROXY")))
print("HTTPS_PROXY:", repr(os.environ.get("HTTPS_PROXY")))
print("ALL_PROXY:", repr(os.environ.get("ALL_PROXY")))
print("NO_PROXY:", repr(os.environ.get("NO_PROXY")))

with httpx.Client(base_url="http://127.0.0.1:8000", timeout=30.0, trust_env=False) as client:
    # Health check
    r = client.get("/health")
    print("health:", r.status_code, r.json())

    # Register with unique email
    email = f"test{int(time.time())}@example.com"
    print("using email:", email)
    r = client.post("/api/auth/register", json={
        "name": "Test",
        "email": email,
        "password": "Pass123!",
        "confirmPassword": "Pass123!",
    })
    print("register:", r.status_code)
    print("  Set-Cookie headers:")
    for k, v in r.headers.multi_items():
        if k.lower() == "set-cookie":
            print("    ", v[:80], "...")
    print("  cookies in jar after register:", list(client.cookies.keys()))

    # Keyword search — the real Stage 2 test
    r = client.get("/api/keywords", params={"q": "grooming near me", "geo": "US"})
    print("keywords status:", r.status_code)
    if r.status_code == 200:
        d = r.json()["data"]
        print("  listings:", len(d["listings"]))
        print("  total results:", d["stats"]["totalResults"])
        print("  difficulty:", d["stats"]["difficulty"], d["stats"]["difficultyLabel"])
        print("  avg price:", d["stats"]["avgPrice"])
    else:
        print("  body:", r.text[:800])

    # FX
    r = client.get("/api/fx", params={"from": "PKR", "to": "USD"})
    print("fx:", r.status_code)
    if r.status_code == 200:
        print("  ", r.json())
    else:
        print("  body:", r.text[:400])