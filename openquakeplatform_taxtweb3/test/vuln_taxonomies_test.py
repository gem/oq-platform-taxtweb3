#!/usr/bin/env python
import unittest
import os
import sys
import time
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

from openquake.moon import platform_get
from openquake.moon import TimeoutError


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


def tag_and_val_get(xpath, times):
    pla = platform_get()

    hide_footer()

    resulte_tag = pla.xpath_finduniq(xpath, times=times)
    resulte_val = resulte_tag.get_attribute("value")
    return (resulte_tag, resulte_val)


def make_function(func_name, taxonomy, run_slow):
    def generated(self):
        pla = platform_get()

        hide_footer()

        col_red = "rgba(255, 223, 191, 1)"
        col_green = "rgb(191, 255, 191)"

        taxonomy_loc = taxonomy
        if taxonomy_loc[-1] == '/':
            taxonomy_loc = taxonomy_loc[0:-1]

        pla.get('/taxtweb/%s' % taxonomy_loc)

        pla.waituntil_js(10, ("try { return (window.gem_pageloaded"
                              " == true); } catch (exc) { return false; }"))

        typeoftax_tag, typeoftax_val = tag_and_val_get(
            "//select[@id='OutTypeCB']", 20)
        typeoftax_sel = Select(typeoftax_tag)
        for i in range(0, 3):
            typeoftax_sel.select_by_index(i)
            resulte_tag, resulte_val = tag_and_val_get(
                "//input[@id='resultE']", 20)
            if resulte_val == taxonomy_loc:
                break
        else:
            self.assertEqual(resulte_val, taxonomy_loc)

        if run_slow:
            time.sleep(1)
            resulte_tag.click()
            resulte_tag.send_keys(Keys.END)  # Positions the cursor at the end of string
            if len(resulte_val) > 0 and resulte_val[-1] == '/':
                resulte_tag.send_keys(Keys.BACK_SPACE)
                resulte_tag, resulte_val = tag_and_val_get(
                    "//input[@id='resultE']", 20)

            while len(resulte_val) > 0:
                prev_len = len(resulte_val)
                last = resulte_val[-1]
                resulte_tag.send_keys(Keys.BACK_SPACE)
                resulte_tag, resulte_val = tag_and_val_get(
                    "//input[@id='resultE']", 20)

                self.assertNotEqual(len(resulte_val), prev_len)

                resulte_bgcol = resulte_tag.value_of_css_property(
                    'background-color')
                self.assertNotEqual(resulte_bgcol, col_red)

                if last == "/":
                    # check integrity
                    virtual_tag, virtual_val = tag_and_val_get(
                        "//input[@id='resultE_virt']", 20)

                    self.assertEqual(resulte_bgcol, col_green)
                    self.assertEqual(resulte_val, virtual_val)

                if resulte_val == "":
                    break

    generated.__name__ = func_name
    return generated


def generator():
    data_path = os.path.join(os.path.dirname(
        sys.modules[VulnTaxonomiesTest.__module__].__file__), 'data')

    with open(os.path.join(data_path, 'taxonomies.txt')) as f:
        ct = 0
        r = 1
        for taxonomy in f:
            if taxonomy[0] == '#':
                r += 1
                continue
            run_slow = False
            # these numbers are dimensioned to obtain 5 minutes test
            if ct < 25:
                run_slow = True
            if ct >= 60:
                break
            taxonomy = taxonomy.strip()
            func_name = "r%04d_%s_%s_test" % (r, taxonomy.replace('.', '~'),
                                              "slow" if run_slow else "fast")
            test_func = make_function(func_name, taxonomy, run_slow)
            setattr(VulnTaxonomiesTest, func_name, test_func)
            ct += 1
            r += 1


generator()
