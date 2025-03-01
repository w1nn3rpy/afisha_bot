import asyncio

from database.events_db import add_events, add_descriptions
from parse.afisha.parse_events import get_all_events
from parse.afisha.parse_description_of_events import get_descriptions

async def parse_everyday_afisha():
    # all_events_list_of_dicts = get_all_events()
    link_of_events = []

    # if all_events_list_of_dicts is not None:
    #     await add_events(all_events_list_of_dicts)

    await get_descriptions()


if __name__ == "__main__":
    asyncio.run(parse_everyday_afisha())