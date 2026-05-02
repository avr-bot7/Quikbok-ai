import os
import re
import sys

from dotenv import load_dotenv
import google.generativeai as genai


# Ensure .env is loaded even when this module is used outside app.py
load_dotenv(override=True)


def _normalize_business_type(business_type: object) -> str:
    text = (str(business_type or "").strip().lower().replace("-", "_").replace(" ", "_"))
    if text in {"hotel", "resort", "stay", "lodging"}:
        return "hotel"
    if text in {"restaurant", "cafe", "dining", "food"}:
        return "restaurant"
    if text in {"tour_guide", "tourguide", "guide"}:
        return "tour_guide"
    if text in {"tour_operator", "touroperator", "tour", "travel"}:
        return "tour_operator"
    return "other"


def _booking_system_prompt(business_name: str, business_type: object) -> str:
    kind = _normalize_business_type(business_type)
    if kind == "hotel":
        return (
            f"You are a friendly AI booking assistant for {business_name} (hotel). "
            "You only handle room or stay bookings. If a customer asks for rafting, tours, transport, or anything outside rooms/stays, politely refuse and steer them back to room options. "
            "Collect and confirm: full name, check-in date, check-out date, room type, number of guests, and phone number. "
            "Reply in Hinglish and stay conversational. "
            "When all details are confirmed, end your message with exactly this marker on a new line: "
            "HOTEL_BOOKING_COMPLETE|name|check_in|check_out|room_type|guests|phone"
        )

    if kind == "restaurant":
        return (
            f"You are a friendly AI booking assistant for {business_name} (restaurant). "
            "You only handle table reservations. Do not offer room bookings, rafting, or tours. "
            "Collect and confirm: full name, reservation date, reservation time, number of people, and phone number. "
            "Reply in Hinglish and stay conversational. "
            "When all details are confirmed, end your message with exactly this marker on a new line: "
            "RESTAURANT_BOOKING_COMPLETE|name|date|time|people|phone"
        )

    if kind in {"tour_guide", "tour_operator"}:
        return (
            f"You are a friendly AI booking assistant for {business_name} ({kind.replace('_', ' ')}). "
            "You only handle tour bookings. Do not offer room bookings or restaurant table reservations. "
            "Collect and confirm: full name, tour type, date, number of people, and phone number. "
            "Reply in Hinglish and stay conversational. "
            "When all details are confirmed, end your message with exactly this marker on a new line: "
            "TOUR_BOOKING_COMPLETE|name|tour_type|date|people|phone"
        )

    return (
        f"You are a friendly AI booking assistant for {business_name} (other). "
        "You only handle general appointment or service bookings. "
        "Collect and confirm: full name, date, service, and phone number. "
        "Reply in Hinglish and stay conversational. "
        "When all details are confirmed, end your message with exactly this marker on a new line: "
        "OTHER_BOOKING_COMPLETE|name|date|service|phone"
    )


def _extract_name(text: str) -> str | None:
    match = re.search(r"\b(?:my\s+name\s+is|i\s+am)\s+([A-Za-z][A-Za-z\s]{1,60})\b", text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_phone(text: str) -> str | None:
    match = re.search(r"(\+?\d{1,3}[\s-]?)?\d{10}\b", text)
    return match.group(0).strip() if match else None


def _extract_iso_dates(text: str) -> list[str]:
    return re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", text)


def _extract_time(text: str) -> str | None:
    match = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b", text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_hotel_room_type(text: str) -> str | None:
    match = re.search(
        r"\b(?:book|reserve|need|want)\s+(?:a|an|the)?\s*([A-Za-z0-9][A-Za-z0-9\s-]{0,60}?room)\b",
        text,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _extract_tour_type(text: str) -> str | None:
    match = re.search(
        r"\b(?:book|reserve|want|need)\s+(?:a|an|the)?\s*([A-Za-z0-9][A-Za-z0-9\s-]{0,60}?)\s+tour\b",
        text,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _synthesize_booking_marker(user_message: str, business_type: object) -> str | None:
    text = user_message or ""
    kind = _normalize_business_type(business_type)
    name = _extract_name(text)
    phone = _extract_phone(text)
    dates = _extract_iso_dates(text)

    if kind == "hotel":
        room_type = _extract_hotel_room_type(text)
        guests = re.search(r"\b(\d+)\s+guests?\b", text, flags=re.IGNORECASE)
        if name and phone and room_type and len(dates) >= 2 and guests:
            return (
                "HOTEL_BOOKING_COMPLETE|"
                f"{name}|{dates[0]}|{dates[1]}|{room_type}|{guests.group(1)}|{phone}"
            )

    elif kind == "restaurant":
        people = re.search(r"\b(\d+)\s+(?:people|persons|guests?)\b", text, flags=re.IGNORECASE)
        time_text = _extract_time(text)
        if name and phone and people and dates and time_text:
            return (
                "RESTAURANT_BOOKING_COMPLETE|"
                f"{name}|{dates[0]}|{time_text}|{people.group(1)}|{phone}"
            )

    elif kind in {"tour_guide", "tour_operator"}:
        tour_type = _extract_tour_type(text)
        people = re.search(r"\b(\d+)\s+(?:people|persons|guests?)\b", text, flags=re.IGNORECASE)
        if name and phone and tour_type and dates and people:
            return (
                "TOUR_BOOKING_COMPLETE|"
                f"{name}|{tour_type}|{dates[0]}|{people.group(1)}|{phone}"
            )

    else:
        service_match = re.search(
            r"\b(?:book|booking|reserve|reservation|appointment|consultation)\s+(?:for\s+)?([A-Za-z0-9][A-Za-z0-9\s-]{1,60})\b",
            text,
            flags=re.IGNORECASE,
        )
        service = service_match.group(1).strip() if service_match else None
        if name and phone and dates and service:
            return f"OTHER_BOOKING_COMPLETE|{name}|{dates[0]}|{service}|{phone}"

    return None


def _printable(text: object) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    # If the current stdout can't encode it, escape non-ascii.
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
        return text
    except Exception:
        return text.encode("ascii", errors="backslashreplace").decode("ascii")

class BookingAgent:
    def __init__(self):
        self._client = None
        self._api_key = None

    @property
    def client(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key.strip() == "":
            raise ValueError("Gemini API key is missing")

        debug = os.getenv("GEMINI_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
        if debug:
            print(f"[GEMINI DEBUG] GEMINI_API_KEY len={len(api_key)} suffix=...{api_key[-6:]}")

        # Configure the global genai client if the API key changed (v0.8.3)
        if self._client is None or self._api_key != api_key:
            genai.configure(api_key=api_key)
            # Use a truthy marker for the client since genai is globally configured
            self._client = True
            self._api_key = api_key
        return self._client

    def get_response(self, conversation_history, user_message, business_name, business_type):
        system_prompt = _booking_system_prompt(business_name, business_type)
        try:
            debug = os.getenv("GEMINI_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}

            # Build role-based multi-turn contents for Gemini.
            history = list(conversation_history or [])
            # Keep only the most recent turns to prevent runaway prompts.
            if len(history) > 20:
                history = history[-20:]
            history.append({"role": "user", "content": user_message})

            contents = []
            debug_contents = []
            for msg in history:
                role = msg.get("role")
                text = msg.get("content", "")
                if role == "assistant":
                    gemini_role = "model"
                else:
                    gemini_role = "user"
                contents.append(genai.types.Content(role=gemini_role, parts=[genai.types.Part(text=text)]))
                debug_contents.append({"role": gemini_role, "text": text})

            if debug:
                print("[GEMINI DEBUG] conversation_history sent to Gemini:")
                for i, item in enumerate(history, start=1):
                    print(f"  {i:02d}. {item.get('role')}: {_printable(item.get('content'))}")
                print("[GEMINI DEBUG] contents payload:")
                for i, item in enumerate(debug_contents, start=1):
                    print(f"  {i:02d}. {item['role']}: {_printable(item['text'])}")

            # Use v0.8.3-compatible API: create a GenerativeModel and call generate_content
            model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=system_prompt)
            response = model.generate_content(
                contents,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=512,
                )
            )

            reply = response.text or ""

            if debug:
                print("[GEMINI DEBUG] raw Gemini response text:")
                print(_printable(reply))

            if not any(marker in reply for marker in (
                "HOTEL_BOOKING_COMPLETE|",
                "RESTAURANT_BOOKING_COMPLETE|",
                "TOUR_BOOKING_COMPLETE|",
                "OTHER_BOOKING_COMPLETE|",
                "BOOKING_COMPLETE|",
            )):
                synthesized_marker = _synthesize_booking_marker(user_message, business_type)
                if synthesized_marker:
                    reply = f"{reply.rstrip()}\n\n{synthesized_marker}".strip()
                    if debug:
                        print("[GEMINI DEBUG] synthesized booking marker:")
                        print(_printable(synthesized_marker))

            history.append({"role": "assistant", "content": reply})
            return reply, history
            
        except Exception as e:
            print(f"Error in get_response: {e}")
            # Return placeholder message if API fails
            placeholder = "Namaste! Main aapke booking ke liye yahan hoon. Aap konsa service book karna chahte hain?"
            history = list(conversation_history or [])
            history.append({"role": "assistant", "content": placeholder})
            return placeholder, history

    @staticmethod
    def extract_booking_details_from_text(text: str):
        """Best-effort extraction when user message already contains all 4 fields.

        This is a deterministic fallback for demos when the model reply does not
        include BOOKING_COMPLETE.
        """
        if not text:
            return None

        # Name
        name_match = re.search(
            r"\b(?:my\s+name\s+is|i\s+am)\s+([A-Za-z][A-Za-z\s]{1,60})\b",
            text,
            flags=re.IGNORECASE,
        )
        name = name_match.group(1).strip() if name_match else None

        # Phone (keeps +country if present; also works with plain 10-digit)
        phone_match = re.search(r"(\+?\d{1,3}[\s-]?)?\d{10}\b", text)
        phone = phone_match.group(0).strip() if phone_match else None

        # Date (prefer ISO)
        date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
        date = date_match.group(1) if date_match else None

        # Optional time
        time_match = re.search(r"\b(?:at|@)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b", text, flags=re.IGNORECASE)
        if date and time_match:
            date = f"{date} {time_match.group(1).strip()}"

        # Service
        service_match = re.search(
            r"\b(?:book|booking|reserve|reservation)\s+(?:a|an|the)?\s*([A-Za-z0-9][A-Za-z0-9\s]{1,60})\b",
            text,
            flags=re.IGNORECASE,
        )
        service = service_match.group(1).strip() if service_match else None

        if name and phone and date and service:
            return {"name": name, "phone": phone, "date": date, "service": service}
        return None

    @staticmethod
    def detect_booking_complete(message):
        """Parse booking markers from the AI reply and normalize to the booking schema."""
        try:
            if not message:
                return None

            lines = [line.strip() for line in str(message).splitlines() if line.strip()]
            marker_prefixes = (
                "HOTEL_BOOKING_COMPLETE|",
                "RESTAURANT_BOOKING_COMPLETE|",
                "TOUR_BOOKING_COMPLETE|",
                "OTHER_BOOKING_COMPLETE|",
                "BOOKING_COMPLETE|",
            )

            marker_line = None
            for line in lines:
                if any(line.startswith(prefix) for prefix in marker_prefixes):
                    marker_line = line
                    break

            if not marker_line:
                return None

            parts = [part.strip() for part in marker_line.split("|")]
            marker = parts[0]
            values = parts[1:]

            if marker == "HOTEL_BOOKING_COMPLETE" and len(values) >= 6:
                name, check_in, check_out, room_type, guests, phone = values[:6]
                return {
                    "name": name,
                    "date": f"{check_in} to {check_out}",
                    "service": f"Room booking: {room_type} | Guests: {guests}",
                    "phone": phone,
                }

            if marker == "RESTAURANT_BOOKING_COMPLETE" and len(values) >= 5:
                name, date, time, people, phone = values[:5]
                return {
                    "name": name,
                    "date": f"{date} {time}".strip(),
                    "service": f"Table reservation for {people} people",
                    "phone": phone,
                }

            if marker == "TOUR_BOOKING_COMPLETE" and len(values) >= 5:
                name, tour_type, date, people, phone = values[:5]
                return {
                    "name": name,
                    "date": date,
                    "service": f"Tour booking: {tour_type} | People: {people}",
                    "phone": phone,
                }

            if marker == "OTHER_BOOKING_COMPLETE" and len(values) >= 4:
                name, date, service, phone = values[:4]
                return {
                    "name": name,
                    "date": date,
                    "service": service,
                    "phone": phone,
                }

            if marker == "BOOKING_COMPLETE" and len(values) >= 4:
                name, date, service, phone = values[:4]
                return {
                    "name": name,
                    "date": date,
                    "service": service,
                    "phone": phone,
                }

            return None
        except Exception as e:
            print(f"Error in detect_booking_complete: {e}")
            return None
