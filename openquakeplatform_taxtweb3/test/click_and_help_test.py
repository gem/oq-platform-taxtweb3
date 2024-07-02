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


class VulnTaxonomiesTest(unittest.TestCase):
    @staticmethod
    def setup_class():
        pla = platform_get()
        pla.get('/taxtweb')

        hide_footer()

        try:
            dontshow_tag = pla.xpath_finduniq(
                "//div[@id='taxtweb_splash']//input[@name='dontshowmeagain']",
                times=10)
            pla.wait_visibility(dontshow_tag)
            dontshow_tag.click()
            close_tag = pla.xpath_finduniq(
                "//div[@id='taxtweb_splash']//button[@name='close_btn']")
            close_tag.click()
        except TimeoutError:
            pass

    def click_and_help_simple_test(self):
        pla = platform_get()

        direction = pla.xpath_finduniq(
            "//li[@id='id_help_form']")

        hide_footer()

        first_tab_tag = pla.xpath_finduniq(
            "//li[span[normalize-space(text()) = 'Structural System']]")
        first_tab_tag.click()

        click_and_help_tag = pla.xpath_finduniq(
            "//li[@id='id_help_form']")
        click_and_help_tag.click()

        simple_help = pla.xpath_finduniq(
            "//li[span[normalize-space(text()) = 'Direction X']]")

        # check width / 2, height / 2 of simple_help
        simpl_help_width = simple_help.size['width'] / 2
        simpl_help_height = simple_help.size['height'] / 2

        # click with offset
        action_simple_help = ActionChains(pla.driver)
        action_simple_help.move_to_element_with_offset(
            simple_help, simpl_help_width, simpl_help_height).click().perform()

        pla.select_window_by_name(".*Direction X.*", timeout=5.0,
                                  is_regex=True)
        pla.window_close()
        pla.select_main_window()

    def click_and_help_complex_test(self):
        pla = platform_get()

        hide_footer()

        third_tab_tag = pla.xpath_finduniq(
            "//li[span[normalize-space(text()) = 'Exterior Attributes']]")
        third_tab_tag.click()

        click_and_help_tag = pla.xpath_finduniq(
            "//li[@id='id_help_form']")
        click_and_help_tag.click()

        select_tag = pla.xpath_finduniq(
            "//select[@id='PositionCB']")

        action_select_tag = ActionChains(pla.driver)
        action_select_tag.move_to_element(select_tag).click().perform()

        item_tag = pla.xpath_finduniq(
            "//div[@id='gem_help_select']/span[normalize-space(text()) = "
            "'Adjoining building(s) on two sides']")

        item_tag_width = item_tag.size['width'] / 2
        item_tag_height = item_tag.size['height'] / 2

        action_item_tag = ActionChains(pla.driver)
        action_item_tag.move_to_element_with_offset(
            item_tag, item_tag_width, item_tag_height).click().perform()

        pla.select_window_by_name(".*Adjoining buildings on two sides.*",
                                  timeout=5.0, is_regex=True)
        pla.window_close()
        pla.select_main_window()

    def explanation_test(self):
        pla = platform_get()
        pla.get('/taxtweb/CU+CIP/HBET:1,12')

        hide_footer()

        exp_btn = pla.xpath_finduniq(
            "//a[@id='do_explanation']")
        exp_btn.click()

        time.sleep(2)

        res = pla.xpath_finduniq("//div[@id='explanation']")
        self.assertEqual(res.text,
                         ('Material type: Concrete, unreinforced\n'
                          'Material technology: Cast-in-place concrete\n'
                          'Number of storeys above ground - Range of'
                          ' the number of storeys: between 1 and 12.'))
