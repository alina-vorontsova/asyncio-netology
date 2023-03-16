import asyncio 
import platform 

from aiohttp import ClientSession 

from db import Session, engine 
from models import Character, Base


if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def get_num_of_characters(client_session: ClientSession) -> int:

    # print('Function get_num_of_characters started working.')
    async with client_session.get('https://swapi.dev/api/people/') as response:
        json_data = await response.json()
        number_of_characters = json_data.get('count') + 1 # В 'count' стоит 82, но персонаж №17 отдаёт 404-ый код, поэтому надо пройтись по 83 ссылкам, чтобы достать всех персонажей
        # print('Function get_num_of_characters stopped working.')

        return number_of_characters


async def get_items(links: list, type: str, client_session: ClientSession):

    # print(f'Function get_items started working for {links}.')
    titles_list = []
    for link in links:  
        async with client_session.get(link) as response: 
            json_data = await response.json()
            title = json_data.get(type)
            titles_list.append(title)
    titles = ', '.join(titles_list)
    # print(f'Function get_items stopped working for {links}.')

    return titles


async def get_character(char_id: int, client_session: ClientSession):

    # print(f'Function get_character started working for {char_id}.')
    async with client_session.get(f'https://swapi.dev/api/people/{char_id}') as response:
        json_data = await response.json()
        if json_data.get('detail') == "Not found":
            return None # Обработка персонажа № 17, отдающего 404-ый код 
        else:
            films_links = json_data.get('films')
            homeworld_link = [json_data.get('homeworld')]
            species_links = json_data.get('species')
            starships_links = json_data.get('starships')
            vehicles_links = json_data.get('vehicles')

            films_coro = get_items(films_links, 'title', client_session)
            homeworld_coro = get_items(homeworld_link, 'name', client_session)
            species_coro = get_items(species_links, 'name', client_session)
            starships_coro = get_items(starships_links, 'name', client_session)
            vehicles_coro = get_items(vehicles_links, 'name', client_session)

            fields = await asyncio.gather(films_coro, homeworld_coro, species_coro, starships_coro, vehicles_coro)
            films, homeworld, species, starships, vehicles_names = fields

            json_data['id'] = char_id
            json_data['films'] = films
            json_data['homeworld'] = homeworld
            json_data['species'] = species
            json_data['starships'] = starships
            json_data['vehicles'] = vehicles_names
            del json_data['url'], json_data['created'], json_data['edited']
            # print(f'Function get_character stopped working for {char_id}.')

            return json_data 


async def insert_into_db(character_data):
    
    # print(f'Function insert_into_db started working.')
    async with Session() as session: 
        new_character = Character(**character_data) 
        session.add(new_character)
        # print(f'Function insert_into_db stopped working.')

        await session.commit()


async def main():

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    
    async with ClientSession() as client_session: 
        quantity = await get_num_of_characters(client_session)

    async with ClientSession() as client_session:
        for i in range(1, quantity + 1):
            character = await get_character(i, client_session)
            if character: # Обработка персонажа № 17, отдающего 404-ый код 
                asyncio.create_task(insert_into_db(character))
    
    all_tasks = asyncio.all_tasks()
    all_tasks = all_tasks - {asyncio.current_task()}
    await asyncio.gather(*all_tasks)


asyncio.run(main())