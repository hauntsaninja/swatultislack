import asyncio
import base64
import bs4
import dateparser.search
import datetime
import hashlib
import functools
import urllib.request
import re
import slackreact as sr


def _normalise(s):
    return re.sub("[^\w ]", "", s).strip().lower()


class Sharples(sr.MessageContainsRule):
    async def get_applicable_channels(self):
        return ["im-hungry"]

    async def get_query_strings(self):
        return ["what"]

    @staticmethod
    @functools.lru_cache(maxsize=4)  # too lazy to asyncify but not too lazy to cache
    def get_meals_for_date(date_str):
        url = f"https://dash.swarthmore.edu/calendar/1768/{date_str}"
        with urllib.request.urlopen(url) as response:
            soup = bs4.BeautifulSoup(response.read(), "html.parser")
        meals = []
        for meal in soup.find_all(class_="dash-cal-event"):
            name = meal.find(class_="panel-heading").text.strip()
            time = meal.find(class_="event-time").text.strip()
            food = meal.find(class_="event-body").text.strip()
            meals.append((name, time, food))
        return meals

    async def get_response_text(self, event):
        date = dateparser.search.search_dates(
            event["text"], settings={"PREFER_DATES_FROM": "future"}
        )  # slow, but whatever
        date, date_text = (
            (date[0][1], date[0][1].strftime("%-m/%-d"))
            if date
            else (datetime.date.today(), "today")
        )
        meals = self.get_meals_for_date(date.isoformat())
        for name, time, food in meals:
            if name.lower() in event["text"].lower():
                return [f"{name} {date_text}:", food]
        return []


class Open(sr.MessageContainsRule):
    async def should_respond_to_channel(self, channel_id):
        return True

    async def get_query_strings(self):
        return ["open"]

    @staticmethod
    @functools.lru_cache(maxsize=2)
    def get_hours_for_date(date_str):
        with urllib.request.urlopen("https://dash.swarthmore.edu") as response:
            soup = bs4.BeautifulSoup(response.read(), "html.parser")
        hours = soup.find_all(lambda x: x.text == "Libraries")[0].parent
        hours = [line.stripped_strings for line in hours.find_all("li")]
        return [(place[:-1], time) for place, time, *_ in hours]

    async def get_response_text(self, event):
        hours = self.get_hours_for_date(datetime.date.today().isoformat())

        def is_subseq(sub, seq):
            it = iter(seq)
            return all(c in it for c in sub)

        tokens = _normalise(event["text"]).split()
        index = tokens.index("open")

        two_token_query = " ".join(tokens[max(0, index - 2) : index])
        one_token_query = " ".join(tokens[max(0, index - 1) : index])
        for query in (two_token_query, one_token_query):
            for place, time in hours:
                if is_subseq(query, _normalise(place)):
                    return f"{place} hours: {time}"
        return []


def code(token: bytes, password: str) -> bytes:
    assert len(token) <= 64
    key = hashlib.sha512(password.encode("utf-8")).digest()
    xor = lambda a, b: bytes(x ^ y for x, y in zip(a, b))
    return xor(token, key)


token = b"qQOeKuyR96HSGOEFPgfDZaILYqzf9HWyeUQPuFjV/Lv2oWjuo9Kd3eWX"
password = input("Password: ")
bot = sr.SlackBot(code(base64.b64decode(token), password).decode("utf-8"))
loop = asyncio.get_event_loop()
loop.run_until_complete(bot.run())
loop.close()
