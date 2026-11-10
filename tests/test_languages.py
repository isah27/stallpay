from stallpay.agent import (
    close_if_agreed,
    handle_buyer_message,
    reset_sessions,
    set_session_language,
    start_session,
)
from stallpay.money import money
from stallpay.shops import get_shop


def setup_function():
    reset_sessions()


def _english_flow(shop_id, select_text, bargain_text, item_id, yes_text="Okay I want it"):
    session = start_session(shop_id)
    assert session.language == "en"
    assert session.messages[0].text == get_shop(shop_id).greeting_for("en")
    quoted = handle_buyer_message(session, select_text, prefer_llm=False)
    expected = get_shop(shop_id).item(item_id).selling_price()
    assert session.item_ids == [item_id]
    assert session.quoted_price == money(expected)
    assert "normally" in quoted["reply"] or quoted["reply"].startswith(get_shop(shop_id).item(item_id).name[:8])
    # Scripted English quotes mention "is normally" or "is " and "promo" or a price.
    assert "Theek hai" not in quoted["reply"]
    assert "cuestan" not in quoted["reply"]
    assert "na normally" not in quoted["reply"]
    bargained = handle_buyer_message(session, bargain_text, prefer_llm=False)
    assert session.quoted_price == money(expected)
    assert close_if_agreed(session)["ready"] is False
    assert "best price" in bargained["reply"] or "can't go lower" in bargained["reply"]
    blocked = handle_buyer_message(session, "not yet", prefer_llm=False)
    assert close_if_agreed(session)["ready"] is False
    assert not blocked.get("invoice_ready")
    handle_buyer_message(session, yes_text, prefer_llm=False)
    close = close_if_agreed(session)
    assert close["ready"] is True
    assert session.agreement_quote
    return session


def test_english_buyers_in_every_shop_select_quote_bargain_and_agree():
    _english_flow("lagos", "I want the native shirt", "I'll give you 5000", "native-shirt")
    reset_sessions()
    _english_flow("mexico", "I want the earrings", "Can I get them for 300?", "earrings")
    reset_sessions()
    _english_flow("jaipur", "I want the scarf", "I'll give you 200", "scarf", yes_text="yes I'll take it")


def test_ordinal_and_english_names_select_items():
    session = start_session("mexico")
    handle_buyer_message(session, "the first one", prefer_llm=False)
    assert session.item_ids == ["earrings"]
    reset_sessions()
    session = start_session("mexico")
    handle_buyer_message(session, "1", prefer_llm=False)
    assert session.item_ids == ["earrings"]
    reset_sessions()
    session = start_session("mexico")
    handle_buyer_message(session, "I want the silver hoop earrings", prefer_llm=False)
    assert session.item_ids == ["earrings"]
    reset_sessions()
    session = start_session("jaipur")
    handle_buyer_message(session, "the second one", prefer_llm=False)
    assert session.item_ids == ["stole"]


def test_typed_foreign_language_is_understood_but_replies_stay_english_until_picked():
    session = start_session("mexico")
    quoted = handle_buyer_message(session, "Quiero los aretes de aro de plata.", prefer_llm=False)
    assert session.language == "en"
    assert "normally" in quoted["reply"]
    assert "cuestan" not in quoted["reply"]
    bargained = handle_buyer_message(session, "Te doy 300 pesos.", prefer_llm=False)
    assert session.quoted_price == money(get_shop("mexico").item("earrings").selling_price())
    assert "best price" in bargained["reply"]
    agreed = handle_buyer_message(session, "De acuerdo, lo tomo.", prefer_llm=False)
    assert session.language == "en"
    assert agreed["reply"].startswith("Deal.")
    assert close_if_agreed(session)["ready"] is True

    reset_sessions()
    session = start_session("jaipur")
    handle_buyer_message(session, "Block-print scarf chahiye.", prefer_llm=False)
    handle_buyer_message(session, "Main 200 rupaye dunga.", prefer_llm=False)
    agreed = handle_buyer_message(session, "Theek hai, I will take the cotton stole.", prefer_llm=False)
    # That last line names the stole, so selection may switch; use a scarf yes instead if needed.
    # Re-run a clean scarf agreement:
    reset_sessions()
    session = start_session("jaipur")
    handle_buyer_message(session, "Scarf chahiye.", prefer_llm=False)
    handle_buyer_message(session, "Main 200 rupaye dunga.", prefer_llm=False)
    agreed = handle_buyer_message(session, "Theek hai, I will take it.", prefer_llm=False)
    assert session.language == "en"
    assert "Deal." in agreed["reply"]
    assert close_if_agreed(session)["ready"] is True

    reset_sessions()
    session = start_session("mexico")
    handle_buyer_message(session, "Je veux les aretes.", prefer_llm=False)
    assert session.item_ids == ["earrings"]
    assert session.language == "en"
    bargained = handle_buyer_message(session, "C'est trop cher, je vous donne 300.", prefer_llm=False)
    assert "best price" in bargained["reply"] or "can't go lower" in bargained["reply"]
    agreed = handle_buyer_message(session, "D'accord, je le prends.", prefer_llm=False)
    assert agreed["reply"].startswith("Deal.")
    assert close_if_agreed(session)["ready"] is True


def test_picked_language_switches_greeting_and_replies():
    session = start_session("mexico", "es")
    assert session.language == "es"
    assert "Hola" in session.messages[0].text
    quoted = handle_buyer_message(session, "I want the earrings", prefer_llm=False)
    assert "cuestan" in quoted["reply"] or "promo" in quoted["reply"].lower()
    assert "normally" not in quoted["reply"] or "normalmente" in quoted["reply"]
    bargained = handle_buyer_message(session, "Can I get them for 300?", prefer_llm=False)
    assert "mejor" in bargained["reply"]
    agreed = handle_buyer_message(session, "Okay I want it", prefer_llm=False)
    assert "Trato hecho" in agreed["reply"]
    assert close_if_agreed(session)["ready"] is True

    reset_sessions()
    session = start_session("lagos")
    assert "Welcome." in session.messages[0].text
    set_session_language(session, "fr")
    assert session.language == "fr"
    assert "Bienvenue" in session.messages[0].text
    quoted = handle_buyer_message(session, "I want the native shirt", prefer_llm=False)
    assert "coûte" in quoted["reply"] or "promo" in quoted["reply"]


def test_api_language_picker_and_english_invoice(client):
    home = client.get("/").text
    assert 'id="lang-select"' in home
    assert "English" in home and "Español" in home and "हिन्दी" in home
    assert "Pidgin" in home and "Français" in home
    assert "Select the shop you want to buy from." in home

    started = client.post("/api/chats", json={"shop_id": "mexico"}).json()
    assert started["language"] == "en"
    assert "Welcome." in started["messages"][0]["text"]
    assert started.get("pay_url") in {None, ""}
    sid = started["id"]
    client.post(f"/api/chats/{sid}/messages", json={"text": "I want the earrings", "prefer_llm": False})
    bargained = client.post(
        f"/api/chats/{sid}/messages",
        json={"text": "Can I get them for 300?", "prefer_llm": False},
    ).json()
    assert bargained["session"]["quoted_price"] == str(get_shop("mexico").item("earrings").selling_price())
    assert bargained["session"].get("pay_url") in {None, ""}
    blocked = client.post(f"/api/chats/{sid}/messages", json={"text": "not yet", "prefer_llm": False}).json()
    assert blocked["session"].get("pay_url") in {None, ""}
    yes = client.post(
        f"/api/chats/{sid}/messages",
        json={"text": "ok", "prefer_llm": False},
    )
    body = yes.json()
    assert yes.status_code == 200
    assert body.get("invoiced") is True
    assert body["session"]["pay_url"]
    assert body["invoice"]["status"] == "sent"

    spanish = client.post("/api/chats", json={"shop_id": "jaipur", "language": "es"}).json()
    assert spanish["language"] == "es"
    assert "Bienvenido" in spanish["messages"][0]["text"]
    switched = client.post(f"/api/chats/{spanish['id']}/language", json={"language": "fr"}).json()
    assert switched["language"] == "fr"
    assert "Bienvenue" in switched["messages"][0]["text"]
