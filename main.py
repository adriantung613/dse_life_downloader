import asyncio
import aiohttp
import os
from bs4 import BeautifulSoup


class Received:
    def __init__(self):
        self.received: list[str | bytes] = []


async def requesting_pool(url_list: list[str], received: Received):
    """
    :param url_list:
    :param received: Act as a class for the returned list, the returned list is all the responses from the requesting,
    binary str if response == 200, else str which represents the error
    """
    tasks = []
    returned_value_list: list[str] = [""] * len(url_list)
    async with aiohttp.ClientSession() as session:
        for index, url in enumerate(url_list):
            tasks += [requesting(session, url, returned_value_list, index)]

        await asyncio.gather(*tasks)

    received.received = returned_value_list


async def requesting(session: aiohttp.ClientSession, url: str,
                     returned_value_list: list, index: int):
    while True:
        try:
            async with session.get(url) as response:
                if response.status == 429:
                    await asyncio.sleep(int(response.headers["Retry-After"]))
                    continue

                if response.status != 200:
                    returned_value_list[index] = str(Exception(response))

                returned_value_list[index] = await response.read()
                break

        except Exception as e:
            returned_value_list[index] = str(e)
            break


def create_directory(path: str):
    if not os.path.exists(path) and path != "":
        os.makedirs(path)


def write_html_file(path: str, content: str):
    create_directory("/".join(path.split("/")[:-1]))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_byte_code_file(path: str, content: bytes):
    create_directory("/".join(path.split("/")[:-1]))
    with open(path, "wb") as f:
        f.write(content)


if __name__ == "__main__":
    receive = Received()

    asyncio.run(requesting_pool(["https://dsepp.ru/ppindex/index.html"], receive))

    write_html_file("ppindex/index.html", receive.received[0].decode("utf-8"))

    main_page_url_pool = []
    main_page_file_location_list = []

    soup = BeautifulSoup(receive.received[0].decode("utf-8"), 'html.parser')
    for tag in soup.find_all('a', class_=['nav-link', 'custom']):
        if type(tag.get('href')) != str:
            continue

        if "ppindex" not in tag.get("href"):
            continue

        main_page_url_pool += [tag.get('href').replace("..", "https://dsepp.ru")]
        tag["href"] = tag["href"].replace("../", "")
        main_page_file_location_list += [tag.get('href')]

    write_html_file("DseLife.html", str(soup))

    asyncio.run(requesting_pool(main_page_url_pool, receive))
    subject_webpage_received = receive.received

    while True:
        quit_loop = True
        for index, webpage_byte_string in enumerate(subject_webpage_received):
            subject_page_url_pool = []
            subject_page_file_location_list = []

            webpage_string = webpage_byte_string.decode("utf-8")
            write_html_file(main_page_file_location_list[index], webpage_string)
            soup = BeautifulSoup(webpage_string, 'html.parser')

            for tag in soup.find_all('a', class_=['nav-link', 'custom']):
                if type(tag.get('href')) != str:
                    continue

                if "static/pp" not in tag.get("href"):
                    continue

                subject_page_file_location = tag.get('href').replace("../../", "")
                if os.path.exists(subject_page_file_location):
                    continue

                subject_page_url_pool += [tag.get('href').replace("../..", "https://dsepp.ru")]
                subject_page_file_location_list += [subject_page_file_location]

            for chunk in range(((len(subject_page_url_pool) - 1) // 50) + 1):
                quit_loop = False

                print(f"Downloading: {subject_page_url_pool[chunk * 50: (chunk + 1) * 50]}")
                asyncio.run(requesting_pool(subject_page_url_pool[chunk * 50: (chunk + 1) * 50], receive))

                print("DO NOT QUIT THE PROGRAM NOW UNTIL THE NEXT PROMPT")
                for file_index in range(50):
                    if file_index > len(receive.received) - 1:
                        break

                    file_byte_string = receive.received[file_index]
                    if type(file_byte_string) != bytes:
                        print(f"Error occur when downloading this file: {subject_page_url_pool[chunk * 50 + file_index]}")
                        continue

                    subject_page_file_location = subject_page_file_location_list[chunk * 50 + file_index]
                    write_byte_code_file(subject_page_file_location, file_byte_string)

                print("These files are downloaded  \n\n")

        if quit_loop:
            break
