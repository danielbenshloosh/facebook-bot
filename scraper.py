from selenium.webdriver.common.keys import Keys
from time import sleep
import json
import os
import sys
import urllib.request
import yaml
import utils
import argparse

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import re
import pickle


# new tab .send_keys(Keys.COMMAND + 't')
def get_facebook_images_url(img_links):
    urls = []

    for link in img_links:
        if link != "None":
            valid_url_found = False
            driver.get(link)

            try:
                while not valid_url_found:
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, selectors.get("spotlight"))
                        )
                    )
                    element = driver.find_element_by_class_name(
                        selectors.get("spotlight")
                    )
                    img_url = element.get_attribute("src")

                    if img_url.find(".gif") == -1:
                        valid_url_found = True
                        urls.append(img_url)
            except Exception:
                urls.append("None")
        else:
            urls.append("None")

    return urls


# -------------------------------------------------------------
# -------------------------------------------------------------

# takes a url and downloads image from that url
def image_downloader(img_links, folder_name):
    """
    Download images from a list of image urls.
    :param img_links:
    :param folder_name:
    :return: list of image names downloaded
    """
    img_names = []

    try:
        parent = os.getcwd()
        try:
            folder = os.path.join(os.getcwd(), folder_name)
            utils.create_folder(folder)
            os.chdir(folder)
        except Exception:
            print("Error in changing directory.")

        for link in img_links:
            img_name = "None"

            if link != "None":
                img_name = (link.split(".jpg")[0]).split("/")[-1] + ".jpg"

                # this is the image id when there's no profile pic
                if img_name == selectors.get("default_image"):
                    img_name = "None"
                else:
                    try:
                        urllib.request.urlretrieve(link, img_name)
                    except Exception:
                        img_name = "None"

            img_names.append(img_name)

        os.chdir(parent)
    except Exception:
        print("Exception (image_downloader):", sys.exc_info()[0])
    return img_names


# -------------------------------------------------------------
# -------------------------------------------------------------


def extract_and_write_posts(elements, filename):
    try:
        f = open(filename, "w", newline="\r\n", encoding="utf-8")
        f.writelines(
            " TIME || TYPE  || TITLE || STATUS  ||   LINKS(Shared Posts/Shared Links etc) || POST_ID "
            + "\n"
            + "\n"
        )
        ids = []
        for x in elements:
            try:
                link = ""
                # id
                post_id = utils.get_post_id(x)
                ids.append(post_id)

                # time
                time = utils.get_time(x)

                link, status, title, post_type = get_status_and_title(link, x)

                line = (
                    str(time)
                    + " || "
                    + str(post_type)
                    + " || "
                    + str(title)
                    + " || "
                    + str(status)
                    + " || "
                    + str(link)
                    + " || "
                    + str(post_id)
                    + "\n"
                )

                try:
                    f.writelines(line)
                except Exception:
                    print("Posts: Could not map encoded characters")
            except Exception:
                pass
        f.close()
    except ValueError:
        print("Exception (extract_and_write_posts)", "Status =", sys.exc_info()[0])
    except Exception:
        print("Exception (extract_and_write_posts)", "Status =", sys.exc_info()[0])
    return


def get_status_and_title(link, x):
    # title
    title = utils.get_title(x, selectors)
    if title.text.find("shared a memory") != -1:
        x = x.find_element_by_xpath(selectors.get("title_element"))
        title = utils.get_title(x, selectors)
    status = utils.get_status(x, selectors)
    if title.text == driver.find_element_by_id(selectors.get("title_text")).text:
        if status == "":
            temp = utils.get_div_links(x, "img", selectors)
            if temp == "":  # no image tag which means . it is not a life event
                link = utils.get_div_links(x, "a", selectors).get_attribute("href")
                post_type = "status update without text"
            else:
                post_type = "life event"
                link = utils.get_div_links(x, "a", selectors).get_attribute("href")
                status = utils.get_div_links(x, "a", selectors).text
        else:
            post_type = "status update"
            if utils.get_div_links(x, "a", selectors) != "":
                link = utils.get_div_links(x, "a", selectors).get_attribute("href")

    elif title.text.find(" shared ") != -1:
        x1, link = utils.get_title_links(title)
        post_type = "shared " + x1
    elif title.text.find(" at ") != -1 or title.text.find(" in ") != -1:
        if title.text.find(" at ") != -1:
            x1, link = utils.get_title_links(title)
            post_type = "check in"
        elif title.text.find(" in ") != 1:
            status = utils.get_div_links(x, "a", selectors).text
    elif title.text.find(" added ") != -1 and title.text.find("photo") != -1:
        post_type = "added photo"
        link = utils.get_div_links(x, "a", selectors).get_attribute("href")

    elif title.text.find(" added ") != -1 and title.text.find("video") != -1:
        post_type = "added video"
        link = utils.get_div_links(x, "a", selectors).get_attribute("href")

    else:
        post_type = "others"
    if not isinstance(title, str):
        title = title.text
    status = status.replace("\n", " ")
    title = title.replace("\n", " ")
    return link, status, title, post_type


def extract_and_write_group_posts(elements, filename):
    try:
        f = create_post_file(filename)
        ids = []
        for x in elements:
            try:
                # id
                post_id = utils.get_group_post_id(x)
                ids.append(post_id)
            except Exception:
                pass
        total = len(ids)
        i = 0
        for post_id in ids:
            i += 1
            try:
                add_group_post_to_file(f, filename, post_id, i, total, reload=True)
            except ValueError:
                pass
        f.close()
    except ValueError:
        print("Exception (extract_and_write_posts)", "Status =", sys.exc_info()[0])
    except Exception:
        print("Exception (extract_and_write_posts)", "Status =", sys.exc_info()[0])
    return


def add_group_post_to_file(f, filename, post_id, number=1, total=1, reload=False):
    print("Scraping Post(" + post_id + "). " + str(number) + " of " + str(total))
    photos_dir = os.path.dirname(filename)
    if reload:
        driver.get(utils.create_post_link(post_id, selectors))
    line = get_group_post_as_line(post_id, photos_dir)
    try:
        f.writelines(line)
    except Exception:
        print("Posts: Could not map encoded characters")


def create_post_file(filename):
    """
    Creates post file and header
    :param filename:
    :return: file
    """
    f = open(filename, "w", newline="\r\n", encoding="utf-8")
    f.writelines(
        "TIME || TYPE  || TITLE || STATUS || LINKS(Shared Posts/Shared Links etc) || POST_ID || "
        "PHOTO || COMMENTS " + "\n"
    )
    return f


# -------------------------------------------------------------
# -------------------------------------------------------------


def save_to_file(name, elements, status, current_section):
    """helper function used to save links to files"""

    # status 0 = dealing with friends list
    # status 1 = dealing with photos
    # status 2 = dealing with videos
    # status 3 = dealing with about section
    # status 4 = dealing with posts
    # status 5 = dealing with group posts

    try:
        f = None  # file pointer

        if status != 4 and status != 5:
            f = open(name, "w", encoding="utf-8", newline="\r\n")

        results = []
        img_names = []

        # dealing with Friends
        if status == 0:
            # get profile links of friends
            results = [x.get_attribute("href") for x in elements]
            results = [create_original_link(x) for x in results]

            # get names of friends
            people_names = [
                x.find_element_by_tag_name("img").get_attribute("aria-label")
                for x in elements
            ]

            # download friends' photos
            try:
                if download_friends_photos:
                    if friends_small_size:
                        img_links = [
                            x.find_element_by_css_selector("img").get_attribute("src")
                            for x in elements
                        ]
                    else:
                        links = []
                        for friend in results:
                            try:
                                driver.get(friend)
                                WebDriverWait(driver, 30).until(
                                    EC.presence_of_element_located(
                                        (
                                            By.CLASS_NAME,
                                            selectors.get("profilePicThumb"),
                                        )
                                    )
                                )
                                l = driver.find_element_by_class_name(
                                    selectors.get("profilePicThumb")
                                ).get_attribute("href")
                            except Exception:
                                l = "None"

                            links.append(l)

                        for i, _ in enumerate(links):
                            if links[i] is None:
                                links[i] = "None"
                            elif links[i].find("picture/view") != -1:
                                links[i] = "None"

                        img_links = get_facebook_images_url(links)

                    folder_names = [
                        "Friend's Photos",
                        "Mutual Friends' Photos",
                        "Following's Photos",
                        "Follower's Photos",
                        "Work Friends Photos",
                        "College Friends Photos",
                        "Current City Friends Photos",
                        "Hometown Friends Photos",
                    ]
                    print("Downloading " + folder_names[current_section])

                    img_names = image_downloader(
                        img_links, folder_names[current_section]
                    )
                else:
                    img_names = ["None"] * len(results)
            except Exception:
                print(
                    "Exception (Images)",
                    str(status),
                    "Status =",
                    current_section,
                    sys.exc_info()[0],
                )

        # dealing with Photos
        elif status == 1:
            results = [x.get_attribute("href") for x in elements]
            results.pop(0)

            try:
                if download_uploaded_photos:
                    if photos_small_size:
                        background_img_links = driver.find_elements_by_xpath(
                            selectors.get("background_img_links")
                        )
                        background_img_links = [
                            x.get_attribute("style") for x in background_img_links
                        ]
                        background_img_links = [
                            ((x.split("(")[1]).split(")")[0]).strip('"')
                            for x in background_img_links
                        ]
                    else:
                        background_img_links = get_facebook_images_url(results)

                    folder_names = ["Uploaded Photos", "Tagged Photos"]
                    print("Downloading " + folder_names[current_section])

                    img_names = image_downloader(
                        background_img_links, folder_names[current_section]
                    )
                else:
                    img_names = ["None"] * len(results)
            except Exception:
                print(
                    "Exception (Images)",
                    str(status),
                    "Status =",
                    current_section,
                    sys.exc_info()[0],
                )

        # dealing with Videos
        elif status == 2:
            results = elements[0].find_elements_by_css_selector("li")
            results = [
                x.find_element_by_css_selector("a").get_attribute("href")
                for x in results
            ]

            try:
                if results[0][0] == "/":
                    results = [r.pop(0) for r in results]
                    results = [(selectors.get("fb_link") + x) for x in results]
            except Exception:
                pass

        # dealing with About Section
        elif status == 3:
            print("results:",results)

            # results = elements[0].text
            # f.writelines(results)

        # dealing with Posts
        elif status == 4:
            extract_and_write_posts(elements, name)
            return

        # dealing with Group Posts
        elif status == 5:
            extract_and_write_group_posts(elements, name)
            return


        """Write results to file"""
        if status == 0:
            for i, _ in enumerate(results):
                # friend's profile link
                f.writelines(results[i])
                f.write(",")

                # friend's name
                f.writelines(people_names[i])
                f.write(",")

                # friend's downloaded picture id
                f.writelines(img_names[i])
                f.write("\n")

        elif status == 1:
            for i, _ in enumerate(results):
                # image's link
                f.writelines(results[i])
                f.write(",")

                # downloaded picture id
                f.writelines(img_names[i])
                f.write("\n")

        elif status == 2:
            for x in results:
                f.writelines(x + "\n")

        f.close()

    except Exception:
        print("Exception (save_to_file)", "Status =", str(status), sys.exc_info()[0])

    return


# ----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


def scrape_data(url, scan_list, section, elements_path, save_status, file_names):
    """Given some parameters, this function can scrap friends/photos/videos/about/posts(statuses) of a profile"""
    page = []

    if save_status == 4 or save_status == 5:
        page.append(url)

    page += [url + s for s in section]

    for i, _ in enumerate(scan_list):
        try:
            driver.get(page[i])

            if (
                (save_status == 0) or (save_status == 1) or (save_status == 2)
            ):  # Only run this for friends, photos and videos

                # the bar which contains all the sections
                sections_bar = driver.find_element_by_xpath(
                    selectors.get("sections_bar")
                )

                if sections_bar.text.find(scan_list[i]) == -1:
                    continue

            if save_status != 3:
                utils.scroll(total_scrolls, driver, selectors, scroll_time)
                pass

            data = driver.find_elements_by_xpath(elements_path[i])
            print("\n\n\n\n\n\n\n")
            print(WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
                (By.XPATH, "//span[normalize-space()='FIND US']//following::span[2]"))))
            print("\n\n\n\n\n\n\n")

            save_to_file(file_names[i], data, save_status, i)

        except Exception:
            print(
                "Exception (scrape_data)",
                str(i),
                "Status =",
                str(save_status),
                sys.exc_info()[0],
            )


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


def create_original_link(url):
    if url.find(".php") != -1:
        original_link = (
            facebook_https_prefix + facebook_link_body + ((url.split("="))[1])
        )

        if original_link.find("&") != -1:
            original_link = original_link.split("&")[0]

    elif url.find("fnr_t") != -1:
        original_link = (
            facebook_https_prefix
            + facebook_link_body
            + ((url.split("/"))[-1].split("?")[0])
        )
    elif url.find("_tab") != -1:
        original_link = (
            facebook_https_prefix
            + facebook_link_body
            + (url.split("?")[0]).split("/")[-1]
        )
    else:
        original_link = url

    return original_link


def scrap_profile():
    data_folder = os.path.join(os.getcwd(), "data")
    utils.create_folder(data_folder)
    os.chdir(data_folder)

    # execute for all profiles given in input.txt file
    url = driver.current_url
    user_id = create_original_link(url)

    print("\nScraping:", user_id)

    try:
        target_dir = os.path.join(data_folder, user_id.split("/")[-1])
        utils.create_folder(target_dir)
        os.chdir(target_dir)
    except Exception:
        print("Some error occurred in creating the profile directory.")
        os.chdir("../..")
        return

    to_scrap = ["About"] #"Friends", "Photos", "Videos",, "Posts"
    for item in to_scrap:
        print("----------------------------------------")
        print("Scraping {}..".format(item))

        if item == "Posts":
            scan_list = [None]
        elif item == "About":
            scan_list = [None] * 7
        else:
            scan_list = params[item]["scan_list"]

        section = params[item]["section"]
        elements_path = params[item]["elements_path"]
        file_names = params[item]["file_names"]
        save_status = params[item]["save_status"]

        scrape_data(user_id, scan_list, section, elements_path, save_status, file_names)

        print("{} Done!".format(item))

    print("Finished Scraping Profile " + str(user_id) + ".")
    os.chdir("../..")

    return


def get_comments():
    comments = []
    try:
        data = driver.find_element_by_xpath(selectors.get("comment_section"))
        reply_links = driver.find_elements_by_xpath(
            selectors.get("more_comment_replies")
        )
        for link in reply_links:
            try:
                driver.execute_script("arguments[0].click();", link)
            except Exception:
                pass
        see_more_links = driver.find_elements_by_xpath(
            selectors.get("comment_see_more_link")
        )
        for link in see_more_links:
            try:
                driver.execute_script("arguments[0].click();", link)
            except Exception:
                pass
        data = data.find_elements_by_xpath(selectors.get("comment"))
        for d in data:
            try:
                author = d.find_element_by_xpath(selectors.get("comment_author")).text
                text = d.find_element_by_xpath(selectors.get("comment_text")).text
                replies = utils.get_replies(d, selectors)
                comments.append([author, text, replies])
            except Exception:
                pass
    except Exception:
        pass
    return comments


def get_group_post_as_line(post_id, photos_dir):
    try:
        data = driver.find_element_by_xpath(selectors.get("single_post"))
        time = utils.get_time(data)
        title = utils.get_title(data, selectors).text
        # link, status, title, type = get_status_and_title(title,data)
        link = utils.get_div_links(data, "a", selectors)
        if link != "":
            link = link.get_attribute("href")
        post_type = ""
        status = '"' + utils.get_status(data, selectors).replace("\r\n", " ") + '"'
        photos = utils.get_post_photos_links(data, selectors, photos_small_size)
        comments = get_comments()
        photos = image_downloader(photos, photos_dir)
        line = (
            str(time)
            + "||"
            + str(post_type)
            + "||"
            + str(title)
            + "||"
            + str(status)
            + "||"
            + str(link)
            + "||"
            + str(post_id)
            + "||"
            + str(photos)
            + "||"
            + str(comments)
            + "\n"
        )
        return line
    except Exception:
        return ""


def create_folders():
    """
    Creates folder for saving data (profile, post or group) according to current driver url
    Changes current dir to target_dir
    :return: target_dir or None in case of failure
    """
    folder = os.path.join(os.getcwd(), "data")
    utils.create_folder(folder)
    os.chdir(folder)
    try:
        item_id = get_item_id(driver.current_url)
        target_dir = os.path.join(folder, item_id)
        utils.create_folder(target_dir)
        os.chdir(target_dir)
        return target_dir
    except Exception:
        print("Some error occurred in creating the group directory.")
        os.chdir("../..")
        return None


def get_item_id(url):
    """
    Gets item id from url
    :param url: facebook url string
    :return: item id or empty string in case of failure
    """
    ret = ""
    try:
        link = create_original_link(url)
        ret = link.split("/")[-1]
        if ret.strip() == "":
            ret = link.split("/")[-2]
    except Exception as e:
        print("Failed to get id: " + format(e))
    return ret


def scrape_group(url):
    if create_folders() is None:
        return
    group_id = get_item_id(url)
    # execute for all profiles given in input.txt file
    print("\nScraping:", group_id)

    to_scrap = ["About"]  # , "Photos", "Videos", "About"]
    for item in to_scrap:
        print("----------------------------------------")
        print("Scraping {}..".format(item))

        if item == "GroupPosts":
            scan_list = [None]
        elif item == "About":
            scan_list = [None] * 7
        else:
            scan_list = params[item]["scan_list"]

        section = params[item]["section"]
        elements_path = params[item]["elements_path"]
        file_names = params[item]["file_names"]
        save_status = params[item]["save_status"]

        scrape_data(url, scan_list, section, elements_path, save_status, file_names)

        print("{} Done!".format(item))

    print("Finished Scraping Group " + str(group_id) + ".")
    os.chdir("../..")

    return


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


def login(email, password):
    """ Logging into our own profile """
    useCookies=True
    try:
        global driver

        options = Options()

        #  Code to disable notifications pop up of Chrome Browser
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--mute-audio")
        # options.add_argument("headless")
        options.add_argument("user-data-dir=selenium") # cookies using

        try:

            driver = webdriver.Chrome(
                executable_path=ChromeDriverManager().install(), options=options
            )
        except Exception:
            print("Error loading chrome webdriver " + sys.exc_info()[0])
            exit(1)
        fb_path = facebook_https_prefix + facebook_link_body

        if not isFbLoggedIn():
            try:
                print("Facebook is not logged in")
                print("Facebook logged in is starting")
                # filling the form
                driver.find_element_by_name("email").send_keys(email)
                driver.find_element_by_name("pass").send_keys(password)
                # clicking on login button
                driver.find_element_by_id("loginbutton").click()
            except NoSuchElementException:
                # Facebook new design
                driver.find_element_by_name("login").click()
        else:
            print("Facebook is logged in!")

        driver.get(fb_path)
        driver.maximize_window()

        # if your account uses multi factor authentication
        mfa_code_input = utils.safe_find_element_by_id(driver, "approvals_code")

        if mfa_code_input is None:
            return

        mfa_code_input.send_keys(input("Enter MFA code: "))
        driver.find_element_by_id("checkpointSubmitButton").click()

        # there are so many screens asking you to verify things. Just skip them all
        while (
            utils.safe_find_element_by_id(driver, "checkpointSubmitButton") is not None
        ):
            dont_save_browser_radio = utils.safe_find_element_by_id(driver, "u_0_3")
            if dont_save_browser_radio is not None:
                dont_save_browser_radio.click()

            driver.find_element_by_id("checkpointSubmitButton").click()

    except Exception:
        print("There's some error in log in.")
        print(sys.exc_info()[0])
        exit(1)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


def scraper(**kwargs):
    with open("credentials.yaml", "r") as ymlfile:
        cfg = yaml.safe_load(stream=ymlfile)
    if ("password" not in cfg) or ("email" not in cfg):
        print("Your email or password is missing. Kindly write them in credentials.txt")
        exit(1)
    urls = [
    "https://www.facebook.com/MaslulimMMF"

    ]
    print(urls)
    if len(urls) > 0:
        print("\nStarting Scraping...")
        login(cfg["email"], cfg["password"])
        for url in urls:
            driver.get(url)
            link_type = utils.identify_url(driver.current_url)
            if link_type == 0:
                scrap_profile()
            elif link_type == 1:
                # scrap_post(url)
                pass
            elif link_type == 2:
                scrape_group(driver.current_url)
            elif link_type == 3:
                file_name = params["GroupPosts"]["file_names"][0]
                item_id = get_item_id(driver.current_url)
                if create_folders() is None:
                    continue
                f = create_post_file(file_name)
                add_group_post_to_file(f, file_name, item_id)
                f.close()
                os.chdir("../..")
        driver.close()
    else:
        print("Input file is empty.")


# -------------------------------------------------------------
# -------------------------------------------------------------
# -------------------------------------------------------------
def test():
    try:
        global driver

        options = Options()

        #  Code to disable notifications pop up of Chrome Browser
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--mute-audio")
        # options.add_argument("headless")

        try:
            driver = webdriver.Chrome(
                executable_path=ChromeDriverManager().install(), options=options
            )

        except Exception:
            print("Error loading chrome webdriver " + sys.exc_info()[0])
            exit(1)

        fb_path = facebook_https_prefix + facebook_link_body
        driver.get("https://www.flaticon.com/")
        # driver.maximize_window()
        elements=driver.find_elements_by_class_name("lazyload--done")
        print(len(elements))
        for element in elements:
            try:
                # response = element.click()
                # response = element.send_keys(Keys.COMMAND + 't')
                print("element",element.get_attribute("href"))
                print()
                attributes = driver.execute_script(
                    'var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;',
                    element)
                site = attributes["data-pin-url"]
                print(site)
                driver.execute_script(f"window.open('{site}', 'new_window')")

                # print("response",response)
                sleep(5)
                driver.back()
                sleep(5)
            except Exception as e:
                print(e)
                print("FAILED In for test")

    except Exception:
        print("There's some error in log in.")
        print(sys.exc_info()[0])
        exit(1)

def scrapeProfile(url):
    driver.get(url)
    sleep(2)

    htmlCodeByPageSource = driver.page_source
    htmlCodeByScript = driver.execute_script("return document.documentElement.outerHTML;")

    try:
        print("\n\n\n\n\n\n\n\n")

        # Script code
        if htmlCodeByScript != None:
            numberByScript = numberIsExist(htmlCodeByScript)
            siteByScript = siteIsExist(htmlCodeByScript)
            emailByScript = emailIsExist(htmlCodeByScript)
            print("By Script code:\n", "Number : ", numberByScript, "Email : ",
                  emailByScript)  # ,"Site : ",siteByScript

        print("\n\n\n\n\n\n\n\n")

        # Page source code
        if htmlCodeByPageSource != None:
            numberByPageSource = numberIsExist(htmlCodeByPageSource)
            siteByScriptPageSource = siteIsExist(htmlCodeByPageSource)
            emailByScriptPageSource = emailIsExist(htmlCodeByPageSource)
            print("By Page source code:\n", "Number : ", numberByPageSource, "Email : ",
                  emailByScriptPageSource)  # ,"Site : ",siteByScriptPageSource

        print("\n\n\n\n\n\n\n\n")

    except Exception as e:
        print(e)


def createDriver():
    try:
        global driver

        options = Options()

        #  Code to disable notifications pop up of Chrome Browser
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--mute-audio")
        # options.add_argument("headless")
        # options.add_argument("user-data-dir=selenium") # cookies using

        try:

            driver = webdriver.Chrome(
                executable_path=ChromeDriverManager().install(), options=options
            )
        except Exception:
            print("Error loading chrome webdriver " + str(sys.exc_info()[0]))
            exit(1)

    except Exception as e:
        print(e)
        print("Error createDriver " +str(sys.exc_info()[0]))
        exit(1)
def scrapeObject():

    createDriver()
    ################# Define XPATHS #################
    #"//*[text()='View more comments']"
    # xpathMoreCommentsComments="//*[contains(text(), 'View more comments')]"
    xpathOpenComment="/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[4]/div/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div[2]/div/div[4]/div/div/div/div/div[1]/div/div[2]/div[1]/div/span"
    xpathMoreComments="//span[contains(text(), 'comments')]"
    xpathPreviewComments="//*[@id='mount_0_0']/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[4]/div/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div[2]/div/div[4]/div/div/div[2]/div[2]/div/div[2]"
    xpathMoreComments="//*[@id='mount_0_0']/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div[4]/div[2]/div[1]/div[2]/span"
    xpathComments="//div[contains(@aria-label,'Comment')]"
    # xpathProfile="//div//svg//mask//g//*"
    xpathProfile="//*[@id='mount_0_0']/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div[4]/ul/li[*]/div[1]/div/div[2]/div/div[1]/div/div[1]/div/div/span/span"
        #"//*[@id='mount_0_0']/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div[4]/ul/li[5]/div[1]/div/div[2]/div/div[1]/div/div[1]/div/div/span/span"

    xpathCommentsContent = "//*[@id='mount_0_0']/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[4]/div/div/div/div/div/div[1]/div/div/div/div/div/div/div/div/div[2]/div/div[4]/div/div/div[2]/ul/li[*]/div[1]/div/div[2]/div/div[1]/div/div[1]/div/div"

############## Post photo xpath working !!!!
    # xpathCommentsContent="//*[@id='mount_0_0']/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div[4]/ul/li[*]/div[1]/div/div[2]/div/div[1]/div/div[1]/div/div/div/span/div/div"
    # xpathProfile="//*[@id='mount_0_0']/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div[2]/div/div/div/div[1]/div[4]/ul/li[*]/div[1]/div/div[2]/div/div[1]/div/div[1]/div/div/span/span"



    ################# Define URL #################

    url="https://www.facebook.com/groups/secrettelaviv/permalink/10158628159535943/"
    # url="https://www.facebook.com/groups/secrettelaviv/permalink/10158630646610943/"
    # url="https://www.facebook.com/instagram/photos/a.372558296163354/3534592773293208/?type=3&theater"
    # url="https://www.facebook.com/llbean/photos/a.55494987414/10158220276487415/?type=3&theater"
    # url="https://www.facebook.com/Starbucks/photos/a.10150362709023057/10158872299233057"
    # url="https://www.facebook.com/backyard.org.il/posts/673419573345065"
    # xpathComments="//div[@aria-posinset]//div[contains(@aria-label,'Comment by')]//a/span/span[@dir='auto']"

    ################# Define Flags #################

    flagGetCommentsContect=False
    flagGetProfilesComments=True
    flagGetMoreViews=True


    try:
        driver.get(url)
        sleep(3)
        try:
            xpathToRemove = "//*[@id='mount_0_0']/div/didrv[1]/div/div[3]/div/div/div[1]/div[2]/div"
            elementToRemove = driver.find_element_by_xpath(xpathToRemove)
            driver.execute_script("arguments[0].setAttribute('class','vote-link up voted')", elementToRemove)
        except Exception as e:
            print(e)
            print("elementToRemove Exception - Not exist")
        if flagGetMoreViews:
            try:
                # Open comments
                openCommentsButton = driver.find_element_by_xpath(xpathOpenComment)
                if openCommentsButton == None:

                    print("open Views Buttons is NOT Exist!")
                else:
                    attributes = driver.execute_script(
                        'if(arguments[0].attributes!==undefined){var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;} else return "No attributes!!!!!!!"',
                        openCommentsButton)
                    print("openCommentsButton sattributes:", attributes)
                try:
                    openCommentsButton.click()
                    sleep(1)
                    print("openCommentsButton clicked")
                except Exception:
                    print("failed to click on open comments")
            except Exception as e:
                print(e)
                print
            flagMoreViews = True
            countClicks = 0

            while(flagMoreViews):
                if countClicks == 3:
                    break
                moreCommentsButton = None
                try:
                    moreCommentsButton = driver.find_element_by_xpath(xpathPreviewComments)
                    if moreCommentsButton == None:
                        flagMoreViews = False
                        print("More Views Buttons is NOT Exist!")
                        break
                    try:
                        moreCommentsButton.click()
                        countClicks += 1
                        print("moreCommentsButton clicked")
                    except Exception:
                        print("failed to click on more comments")
                    print("moreCommentsButton:")
                    print("innerHTML:", moreCommentsButton.get_attribute('innerHTML'))
                    print("moreCommentsButton.text:", moreCommentsButton.text)

                    attributes = driver.execute_script(
                        'if(arguments[0].attributes!==undefined){var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;} else return "No attributes!!!!!!!"',
                        moreCommentsButton)
                    print("attributes:", attributes)

                    print(moreCommentsButton)

                except Exception as e:
                    flagMoreViews = False
                    print("More Views Buttons is NOT Exist!")
                    break
                    print(e)
                print("Clicked:",countClicks)
                sleep(2)
        if flagGetProfilesComments:
            # sleep(1)
            try:
                profiles = driver.find_elements_by_xpath(xpathProfile)
                print("profiles len:",len(profiles))

                print("profiles:")
                for profile in profiles:
                    print("profiles innerHTML:", profile.get_attribute('innerHTML'))
                    print("profiles.text:", profile.text)

                    attributes = driver.execute_script(
                        'if(arguments[0].attributes!==undefined){var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;} else return "No attributes!!!!!!!"',
                        profile)
                    print("profiles attributes:", attributes)

                    print(profile)
                    print("\n")
                    try:
                        profile.click()
                        print("Clicked profile")
                    except Exception:
                        print("failed to click on profile")

            except Exception as e:
                print(e)
                print
        if flagGetCommentsContect:
            comments = driver.find_elements_by_xpath(xpathCommentsContent)
            print("\n\n")
            print("comments:",comments)
            print("comments len:",len(comments))
            i = 1
            for comment in comments:
                try:
                    print("Comment number", i)
                    try:
                        comment.click()
                    except Exception:
                        print("failed to click on comment")
                    # newDriver=comment.send_keys(Keys.COMMAND + 't')
                    attributes = driver.execute_script(
                        'var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;',
                        comment)
                    print("attributes:", attributes)
                    print("Comment innerHTML:", comment.get_attribute('innerHTML'))
                    print("Comment.text:", comment.text)

                    # sleep(5)
                    # break

                except Exception as e:
                    print(e)
                i += 1
            print(len(comments))
            sleep(20)
    except Exception as e:
        print(e)
        print("Objects Exception")

def scrapePost(url):
    driver.get(url)
    sleep(2)
    try:
        comments = driver.find_elements_by_xpath(
            "//div[@aria-posinset]//div[contains(@aria-label,'Comment by')]//a/span/span[@dir='auto']")
        print(comments)
        print(len(comments))
        i = 1
        for comment in comments:
            try:
                print("Comment number", i)
                # newDriver=comment.send_keys(Keys.COMMAND + 't')
                attributes = driver.execute_script(
                    'var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;',
                    comment)
                print("attributes:", attributes)

                sleep(20)
                break

            except Exception as e:
                print(e)
            i += 1
        print(len(comments))
        sleep(20)
    except Exception as e:
        print(e)
        print("Comments Exception")


def scrape_email_phone(url):

    fromSelenium=True
    fromGroup=True

    if fromSelenium:
        with open("info.html", "r") as info:
            infoHtml = info.read()
        with open("credentials.yaml", "r") as ymlfile:
            cfg = yaml.safe_load(stream=ymlfile)
            print(cfg)

        with open("secrets.json", "r") as jsonfile:
            cfg = json.loads(jsonfile.read())
            print(cfg)

        if ("password" not in cfg) or ("email" not in cfg):
            print("Your email or password is missing. Kindly write them in credentials.txt")
            exit(1)

        print("\nStarting Scraping...")
        login(cfg["email"], cfg["password"])
        sleep(3)
        scrapePost(url)
        sleep(2.5)

    if fromSelenium:
        driver.close()
    # # wait some time
    # print(WebDriverWait(driver, 5).until(
    #     EC.visibility_of_element_located((By.XPATH, "//span[normalize-space()='FIND US']//following::span[2]"))))

    # address_elements = driver.find_elements_by_xpath(
    #     "//span[text()='FIND US']/../following-sibling::div//button[text()='Get Directions']/../../preceding-sibling::div[1]/div/span")
    # address_elements = driver.find_elements_by_xpath(
    #     "// span[normalize - space() = 'FIND US'] // following::span[2]")

    # for item in address_elements:
    #     print
    #     item.text

def saveHtmlCodeToFile(htmlCodeByScript,htmlCodeByPageSource):
    # Script code
    f = open("htmls/htmlByScript.html", "a+")
    f.write(htmlCodeByScript)
    f.close()

    # Page source code
    f = open("htmls/htmlByPageSource.html", "a+")
    f.write(htmlCodeByPageSource)
    f.close()

def numberIsExist(string):
    regexp = re.compile(r'\d{3}[-]\d{3}[-]\d{4}')
    if regexp.search(string):
        print ("number matched")
        response=regexp.findall(string)
        print(response)
        return response
    return False

def emailIsExist(string):
    regexp = re.compile("r'[\w\.-]+@[\w\.-]+'")
    print("In emailIsExist")
    stringToFind = '"mailto:'
    startIndex=string.index(stringToFind)+8
    print("STRING:",str(string[startIndex]))
    if string.__contains__(stringToFind):
        flagQuote = True
        i = 0
        email = ""
        while(flagQuote):
            if i >= 100 :
                print("email",email)
                break
            if string[startIndex + i] == '"':
                print("Found It!")
                print(email)
                flagQuote = False
                break
            else:
                email += str(string[startIndex + i])

            i+=1

    # if regexp.search(string):
    #     print("email matched")
    #     response=regexp.findall(string)
    #     print(response)
    #     return response


    return False

def siteIsExist(string):
    regexp = re.compile(r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)')
    if regexp.search(string):
        print ("site matched")
        response=regexp.findall(string)
        # print(response)
        return response
    return False


def getPageHTML():
    try:
        return driver.get_attribute('innerHTML')

    except Exception as e:
        print(e)
        print("Cannot get HTML page")
        return False

def writeToCSV():

    print("NEED TO CHECK IF MAIL IS VALID!!!!!!!!!!")

def isFbLoggedIn():
    driver.get("https://facebook.com")
    if 'Facebook – log in or sign up' in driver.title:
        return False
    else:
        return True



if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    # PLS CHECK IF HELP CAN BE BETTER / LESS AMBIGUOUS
    ap.add_argument(
        "-dup",
        "--uploaded_photos",
        help="download users' uploaded photos?",
        default=True,
    )
    ap.add_argument(
        "-dfp", "--friends_photos", help="download users' photos?", default=True
    )
    ap.add_argument(
        "-fss",
        "--friends_small_size",
        help="Download friends pictures in small size?",
        default=True,
    )
    ap.add_argument(
        "-pss",
        "--photos_small_size",
        help="Download photos in small size?",
        default=True,
    )
    ap.add_argument(
        "-ts",
        "--total_scrolls",
        help="How many times should I scroll down?",
        default=30,
    )
    ap.add_argument(
        "-st", "--scroll_time", help="How much time should I take to scroll?", default=8
    )

    args = vars(ap.parse_args())
    print(args)

    # ---------------------------------------------------------
    # Global Variables
    # ---------------------------------------------------------

    # whether to download photos or not
    download_uploaded_photos = utils.to_bool(args["uploaded_photos"])
    download_friends_photos = utils.to_bool(args["friends_photos"])

    # whether to download the full image or its thumbnail (small size)
    # if small size is True then it will be very quick else if its false then it will open each photo to download it
    # and it will take much more time
    friends_small_size = utils.to_bool(args["friends_small_size"])
    photos_small_size = utils.to_bool(args["photos_small_size"])

    total_scrolls = int(args["total_scrolls"])
    scroll_time = int(args["scroll_time"])

    current_scrolls = 0
    old_height = 0

    driver = None

    with open("selectors.json") as a, open("params.json") as b:
        selectors = json.load(a)
        params = json.load(b)

    firefox_profile_path = selectors.get("firefox_profile_path")
    facebook_https_prefix = selectors.get("facebook_https_prefix")
    facebook_link_body = selectors.get("facebook_link_body")

    # get things rolling
    #scraper()
    # scrape_email_phone("https://www.facebook.com/groups/268799249931777/permalink/2393845007427180/")
    # test()
    # scrapePost("")
    scrapeObject()


    # style="visibility:hidden"