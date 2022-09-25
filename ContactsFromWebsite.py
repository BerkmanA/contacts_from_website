#!/usr/bin/env python
# @aberkman

import re
import requests
from bs4 import BeautifulSoup
from maltego_trx.transform import DiscoverableTransform
from maltego_trx.entities import Email, PhoneNumber, Telegram
from maltego_trx.maltego import UIM_PARTIAL
MAX_SCRAPES = 50


class ContactsFromWebsite(DiscoverableTransform):
    """
    on the input of a website, scrapes the website for contact information
    returns entities of emails, phone numbers and telegram links
    """

    @classmethod
    def create_entities(cls, request, response):
        website = request.Value
        contacts = []

        # get contact list
        try:
            contacts = cls.scan_page(contacts, [website])
        except IOError:
            response.addUIMessage("Could not scan website", messageType=UIM_PARTIAL)
            return

        # create entities
        for contact in contacts:
            try:
                # email
                for email in contact['email']:
                    ent = response.addEntity(Email, email)
                    ent.addCustomLinkProperty('description', 'description', contact['url'])

                # phone number
                for phone in contact['phone']:
                    if bool(set(phone) & set(['+', ' ', '-', ')'])):
                        ent = response.addEntity(PhoneNumber, phone)
                        ent.addCustomLinkProperty('description', 'description', contact['url'])

                # telegram
                for telegram in contact['telegram']:
                    tel_dict = cls.get_telegram_details(telegram)
                    ent = response.addEntity(Telegram, tel_dict['title'])
                    ent.addProperty('profile-image', 'Profile Image', '', tel_dict['image'])
                    ent.addProperty('name', 'Name', '', tel_dict['title'])
                    if tel_dict['description']:
                        ent.setNote(tel_dict['description'])
                    ent.addCustomLinkProperty('description', 'description', contact['url'])

            except IOError:
                response.addUIMessage("Could not create entities", messageType=UIM_PARTIAL)

    @classmethod
    def scan_page(cls, contact_list, urls, indx=0):
        """
        receives a list of urls to scrape
        for each url, calls scraping methods to find contact data
        returns dict with the results
        """
        contact = {'email': set(), 'phone': set(), 'telegram': set(), 'url': ''}  # contact dict

        # get html from page
        if indx < len(urls) and indx < MAX_SCRAPES:  # pages left to scrape
            page = urls[indx]  # page to be scraped
            try:
                html = requests.get(page)
                indx += 1
            except Exception:
                indx += 1
                return cls.scan_page(contact_list, urls, indx)  # ignore borken page and move to next url
        else:  # return if no pages left to scrape
            return contact_list

        # get emails and phone number from page
        contact = cls.get_email_and_phone(html.text, contact)

        # get telegrams and links
        container = {'pages': urls, 'telegrams': contact['telegram']}
        container = cls.get_telegram_and_links(html.content, container)
        urls = container['pages']
        contact['telegram'] = container['telegrams']

        # if contact info is found, add source and add to contact list
        if contact['email'] or contact['phone'] or contact['telegram']:
            contact['url'] = page
            contact_list.append(contact)

        # scrape next page in list
        return cls.scan_page(contact_list, urls, indx)

    @staticmethod
    def get_telegram_details(link):
        """
        scans given telegram link and returns a dict
        the dict contains the account pic url,
        the account name and description
        """
        tel_dict = {'image': '', 'title': '', 'description': ''}

        # get html
        try:
            html = requests.get(link).content
            soup = BeautifulSoup(html, 'html.parser')
        except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
            return tel_dict

        # get image url
        img_link = soup.findAll('img')[0].get('src')
        tel_dict['image'] = img_link

        # get title
        title = soup.find('div', class_='tgme_page_title')
        title = title.find('span').text
        tel_dict['title'] = title

        # get description
        description = soup.find('div', class_='tgme_page_description')
        tel_dict['descript'] = description

        return tel_dict

    @staticmethod
    def get_telegram_and_links(html, container):
        """
        on input of html
        scans the html for links and telegram links
        returns a dict with a list of new links to be scraped
        and telegram links
        """
        soup = BeautifulSoup(html, 'lxml')
        telegrams = set()

        # find all links
        for anchor in soup.find_all('a'):
            if 'href' in anchor.attrs:
                url = anchor.attrs['href']
                # check for telegram link
                if url.startswith('https://t.me/'):
                    container['telegrams'].update([url])
                # insert link to be scraped
                else:
                    if url not in container['pages']:
                        container['pages'].append(url)

        return container

    @staticmethod
    def get_email_and_phone(html, contact):
        """
        receives an html and scans it for emails and phone numbers
        returns dict witht he results
        """
        # regex for email and phone numbers
        rgx_email = re.compile(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.com")
        rgx_phone = re.compile("\s(\+?\(?\d{1,3}\)?\-?\ ?\(?\d{2,3}\)?\-?\ ?\d{3,4}\-?\ ?\d{3,4})")

        # find emails and phone numbers in html
        emails = set(re.findall(rgx_email, html))
        phone_numbers = set(re.findall(rgx_phone, html))

        # apply to contact
        contact['email'] = emails
        contact['phone'] = phone_numbers

        return contact
