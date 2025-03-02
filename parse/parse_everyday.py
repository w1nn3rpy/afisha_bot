import asyncio

from database.events_db import add_events, add_descriptions, get_events_without_description
from parse.afisha.parse_events import get_all_events
from parse.afisha.parse_description_of_events import get_descriptions

async def parse_everyday_afisha():
    # all_events_list_of_dicts = get_all_events()
    link_of_events = []

    # if all_events_list_of_dicts is not None:
    #     await add_events(all_events_list_of_dicts)

    list_of_links = await get_events_without_description()

    if list_of_links is not None:
        description = await get_descriptions(list_of_links)
        print('description type: ', type(description))
        print('description: ', description)
        await add_descriptions(description)


if __name__ == "__main__":
    asyncio.run(parse_everyday_afisha())