import os
from datetime import datetime, timedelta, timezone

import requests

STATE_FILE = "state/last_check.txt"

HUBSPOT_TOKEN = os.environ["HUBSPOT_TOKEN"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
HUBSPOT_PORTAL_ID = os.environ.get("HUBSPOT_PORTAL_ID", "")
DATE_PROPERTY = os.environ.get("HUBSPOT_DATE_PROPERTY", "createdate")


def read_last_check():
    try:
        with open(STATE_FILE, "r") as f:
            value = f.read().strip()
        if value:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except FileNotFoundError:
        pass
    return datetime.now(timezone.utc) - timedelta(minutes=10)


def write_last_check(dt):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        f.write(dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z")


def fetch_new_tickets(since):
    since_ms = int(since.timestamp() * 1000)
    url = "https://api.hubapi.com/crm/v3/objects/tickets/search"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": DATE_PROPERTY,
                "operator": "GT",
                "value": since_ms,
            }]
        }],
        "sorts": [{"propertyName": DATE_PROPERTY, "direction": "ASCENDING"}],
        "properties": ["subject", "hs_pipeline_stage", "hs_ticket_priority", DATE_PROPERTY],
        "limit": 100,
    }

    tickets = []
    after = None
    while True:
        if after:
            payload["after"] = after
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        tickets.extend(data.get("results", []))
        after = data.get("paging", {}).get("next", {}).get("after")
        if not after:
            break
    return tickets


def notify_telegram(ticket):
    ticket_id = ticket["id"]
    props = ticket.get("properties", {})
    subject = props.get("subject") or "(sem assunto)"
    priority = props.get("hs_ticket_priority") or "-"
    stage = props.get("hs_pipeline_stage") or "-"

    text = (
        "\U0001F3AB <b>Novo chamado no HubSpot</b>\n"
        f"<b>Assunto:</b> {subject}\n"
        f"<b>Prioridade:</b> {priority}\n"
        f"<b>Estágio:</b> {stage}"
    )
    if HUBSPOT_PORTAL_ID:
        text += (
            f'\n<a href="https://app.hubspot.com/contacts/{HUBSPOT_PORTAL_ID}/ticket/{ticket_id}">'
            "Abrir no HubSpot</a>"
        )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(
        url,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=30,
    )
    response.raise_for_status()


def main():
    last_check = read_last_check()
    run_time = datetime.now(timezone.utc)

    tickets = fetch_new_tickets(last_check)
    print(f"{len(tickets)} novo(s) chamado(s) encontrado(s) desde {last_check.isoformat()}")

    for ticket in tickets:
        notify_telegram(ticket)

    write_last_check(run_time)


if __name__ == "__main__":
    main()
