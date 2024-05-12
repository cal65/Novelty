from bs4 import BeautifulSoup
import requests
import sys

cookies = {
    'ccsid': '981-7720517-4539359',
    'p': 'dkCKV365TjqNenOKY4VtqQ6sIm7CTPX-c9d94GhAzRXKWDHD',
    'likely_has_account': 'true',
    'allow_behavioral_targeting': 'true',
    'session-id': '141-6452885-9687058',
    'logged_out_browsing_page_count': '2',
    'srb_1': '0',
    'ubid-main': '131-4250835-4161367',
    'lc-main': 'en_US',
    'csm-hit': 'tb:28PZZBK444T48GAAWQ0H+b-4K51QZ90N1KMGMJX1EGE|1667883949756&t:1667883949756&adb:adblk_no',
    'srb_8': '0_ar',
    '__qca': 'P0-58208308-1679029998916',
    'locale': 'en',
    'ntvSession': '{"id":7105107,"placementID":1210536,"lastInteraction":1689465068498,"sessionStart":1689465068498,"sessionEndDate":1689490800000,"experiment":""}',
    'csm-sid': '269-3996257-5017812',
    'session-id-time': '2320515620l',
    'session-token': 'Bll6D6eAe4nNvOkehUMOOiTy4c4dutA4SyuqLzIqhZ5cMhyT2bANWizk46rCLq+4aX5D5pqBvnIaX6QsPa56vc5gkxqXminijtEMeUbLF3qOik7AZPmfvytj6nPBPfT+t9A42Dp7xlKFAZnaVO+Foi21M9N3xAh3QCCPxdSAaPZkhowMHaJGGjttzEyUu2EUX1DMzy5acpvzFWv7UwT1gUzeFee0FrxSfSh8k0dQdkCZP6+7WRHUAIM3gV1xnOzb',
    'x-main': '"4EosvwpQCoL@Zqhj7Zl8DtXYnjfXD7IkpvU@N8xOvXojNJjDQltTAFj8AHu9yDRf"',
    'at-main': 'Atza|IwEBIMkjx-aTGd5k5nOkjWE2S50ghFqGwXFblgQVwqkLIK0PpWxkaYVh4LWhhqF7qP3bEFDHsQ8VS7vyBC8aHWvY47-Aef9fMP5aQ01xHNps59k6kvGGqoqG_Jm2mvZsKHzygEteaxC0K45nhUEsdIYZ-KMEQqxV_EsImxEkPmQ3860AaQ7DN9cCviswebYV8FYkIU3I4WLenkGiH7jIfFAi15_BlpSTMsGYft98wFpjb5pKFxRpIs91oQvD7tCfLVf3MwnGve3V_zcWcr_Ft-PbS1KD',
    'sess-at-main': '"L4X7nx1bEIpiwwD4dl1RnG+lCVmCeLZhDOTptos71YI="',
    '_session_id2': '709591c189ab49250a9d5e92eaf6ef6d',
    '__gads': 'ID=df0a6707150d114d:T=1670897981:RT=1690310731:S=ALNI_MZfGBQsHE3Vk7tICMIg8zJxLI8e8Q',
    '__gpi': 'UID=0000097ff616a3c7:T=1682402001:RT=1690310731:S=ALNI_MY4xLYySL-kyW09g_nl8AuOjCRIbQ',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'DNT': '1',
    'If-None-Match': 'W/"9404a63aaa98659fb1000399ea02cdf3"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

def ids_from_article(url):
    page = requests.get(url, cookies=cookies, headers=headers, timeout=5)
    soup = BeautifulSoup(page.content, "html.parser")
    links_raw = soup.findAll('i')
    a_refs = [link.find('a') for link in links_raw]
    a_refs = [a for a in a_refs if a is not None]
    links = [a.attrs['href'] for a in a_refs]
    book_ids = [link.split('/')[-1].split('-')[0] for link in links]
    return book_ids


def ids_from_user_list(url):
    soup = BeautifulSoup(requests.get(url, cookies=cookies, headers=headers).content, "html.parser")
    titles = soup.findAll('td', {'class': 'field title'})
    links_raw = [t.find('a').attrs['href'] for t in titles]
    book_ids = [int(link.split('/')[-1].split('-')[0].split('.')[0]) for link in links_raw]
    return book_ids

