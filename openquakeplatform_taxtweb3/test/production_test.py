#!/usr/bin/env python
import unittest
from openquake.moon import platform_get
from selenium.webdriver.common.action_chains import ActionChains
from openquake.moon import TimeoutError
import time

def hide_footer():

    pla = platform_get()

    footer = pla.xpath_finduniq("//footer")

    # hide
    pla.driver.execute_script(
        "$(arguments[0]).attr('style','display:none;')", footer)


class ProductionTest(unittest.TestCase):
    @staticmethod
    def setup_class():
        print('setup_class:begin')
        pla = platform_get()

    def permalink_test(self):
        pla = platform_get()
        prod_pla = pla.platform_create('admin', 'admin', jqheavy=None)
        prod_pla.init(config=('https://tools.openquake.org', 'admin', 'admin', 'test@openquake.org', ''),
                      autologin=False)
        prod_pla.get('/taxtweb')

        hide_footer()

        try:
            dontshow_tag = prod_pla.xpath_finduniq(
                "//div[@id='taxtweb_splash']//input[@name='dontshowmeagain']",
                times=10)
            prod_pla.wait_visibility(dontshow_tag)
            dontshow_tag.click()
            close_tag = prod_pla.xpath_finduniq(
                "//div[@id='taxtweb_splash']//button[@name='close_btn']")
            close_tag.click()
        except TimeoutError:
            pass

        permalink_page = '/taxtweb/DX+D99/CU+CIP/L99/DY+D99/CU+CIP/L99/H99/Y99/OC99/BP99/PLF99/IR99/EW99/RSH99+RMT99+R99+RWC99/F99+FWC99/FOS99'
        prod_pla.get(permalink_page)
        permalink = prod_pla.xpath_finduniq("//a[@id='permalink']")
        permalink_url = permalink.get_attribute('href')
        self.assertEqual(prod_pla.basepath + permalink_page, permalink_url)
        pla.platform_destroy(prod_pla)
