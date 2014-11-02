#!/usr/bin/python
# -*- coding: utf-8 -*-

# freeseer - vga/presentation capture software
#
# Copyright (C) 2013 Free and Open Source Software Learning Centre
# http://fosslc.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# For support, questions, suggestions or any other inquiries, visit:
# http://wiki.github.com/Freeseer/freeseer/

import pygst
pygst.require("0.10")  # required before import gst

from collections import defaultdict
from functools import partial
import gst
import os
import pytest
import re
import sys

from freeseer.framework.config import Config
from freeseer.framework.config.profile import ProfileManager
from freeseer.framework.plugin import IAudioInput
from freeseer.framework.plugin import PluginManager
from freeseer.framework.config import options


@pytest.fixture
def plugin_manager(tmpdir):
    """Constructs a plugin manager using a fake profile with a temporary directory."""
    profile_manager = ProfileManager(str(tmpdir))
    profile = profile_manager.get('testing')
    return PluginManager(profile)


@pytest.fixture(scope='module')
def plugin_platform_category_cache():
    """
    Test Helper fixture used to create a count of the number of plugins a platform supports by category
    """
    platforms = ['linux', 'linux2', 'win32', 'cygwin', 'darwin', 'fake-dos']
    pluginpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, "plugins")

    categories = []
    # Categories are folder names in the plugins directory such as 'audioinput', 'audiomixer', etc.
    for directory in os.listdir(pluginpath):
        if os.path.isdir(os.path.join(pluginpath, directory)):
            categories.append(directory)

    plugin_platform_category_count = defaultdict(partial(defaultdict, int))  # {platform : {category : count, category2 : count2}}

    for category in categories:
        for root, directories, files in os.walk(os.path.join(pluginpath, category)):
            for filename in files:
                if filename.endswith('.freeseer-plugin'):
                    plugin_name, _ = os.path.splitext(filename)

                    if os.path.isfile(os.path.join(root, '{}.py'.format(plugin_name))):
                        # Case one: the plugin name is plugin.py
                        plugin_file_name = os.path.join(root, '{}.py'.format(plugin_name))
                    elif os.path.isfile(os.path.join(root, plugin_name, '__init__.py')):
                        # Case two: the plugin is in the __init__.py file of the directory named plugin
                        plugin_file_name = os.path.join(root, plugin_name, '__init__.py')
                    else:
                        # Case three, we could not find the plugin in the expected locations.
                        assert False, 'Failed to find plugin file but saw plugin.freeseer-plugin file.'

                    with open(plugin_file_name, 'r') as search_file:
                        for line in search_file:
                            if re.match('\s*os =.*', line):  # find a string like " os = ['win32',..,'platforms']"
                                for platform in platforms:
                                    if platform in line:
                                        plugin_platform_category_count[platform][category] += 1
    return plugin_platform_category_count


@pytest.mark.parametrize('plugin_info, expected_instance', [
    (('AudioInput', 'get_audioinput_bin'), gst.Bin),
    (('AudioMixer', 'get_audiomixer_bin'), gst.Bin),
    (('VideoInput', 'get_videoinput_bin'), gst.Bin),
    (('VideoMixer', 'get_videomixer_bin'), gst.Bin),
    (('Output', 'get_output_bin'), gst.Bin)
])
def test_plugin_bin(plugin_manager, plugin_info, expected_instance):
    """Check that a plugin and its get method returns the proper gst.Bin object"""
    plugin_name, get_plugin_method = plugin_info
    plugins = plugin_manager.get_plugins_of_category(plugin_name)

    for plugin in plugins:
        plugin.plugin_object.load_config(plugin_manager)
        if plugin.name == "Firewire Source":
            # FIXME: There is a link error in firewiresrc/__init__.py on the line:
            # dv1394dvdemux.link(dv1394q2)
            # Related gh#141
            # Issue gh#644
            continue
        plugin_bin = getattr(plugin.plugin_object, get_plugin_method)()
        assert isinstance(plugin_bin, expected_instance)


def test_os_supported(plugin_manager, monkeypatch):
    """
    Verifies that the os_supported function returns true when a plugin claims to support a given OS.
    Verifies that the os_supported function returns false when a fake operating system is given.
    """
    plugins = plugin_manager.get_all_plugins()
    assert plugins, "The list of plugins should not be empty."
    for plugin in plugins:
        if 'linux2' in plugin.plugin_object.os:
            monkeypatch.setattr(sys, 'platform', 'linux2')
            assert plugin_manager._os_supported(plugin)
        if 'darwin' in plugin.plugin_object.os:
            monkeypatch.setattr(sys, 'platform', 'darwin')
            assert plugin_manager._os_supported(plugin)
        if 'win32' in plugin.plugin_object.os:
            monkeypatch.setattr(sys, 'platform', 'win32')
            assert plugin_manager._os_supported(plugin)

        monkeypatch.setattr(sys, 'platform', 'fake-dos')
        assert not plugin_manager._os_supported(plugin)  # Fake os should not be supported


def test_get_supported_plugins(plugin_manager, monkeypatch):
    """
    Verifies per platform that all plugins returned are indeed supported.
    Also checks that an expected number of plugins are returned.
    """
    unfiltered_plugins = plugin_manager.plugmanc.getAllPlugins()
    monkeypatch.setattr(sys, 'platform', 'linux2')
    linux_plugins = plugin_manager._get_supported_plugins(unfiltered_plugins)
    assert linux_plugins
    for plugin in linux_plugins:
        assert 'linux2' in plugin.plugin_object.os

    monkeypatch.setattr(sys, 'platform', 'darwin')
    darwin_plugins = plugin_manager._get_supported_plugins(unfiltered_plugins)
    assert darwin_plugins
    for plugin in darwin_plugins:
        assert 'darwin' in plugin.plugin_object.os

    monkeypatch.setattr(sys, 'platform', 'win32')
    win32_plugins = plugin_manager._get_supported_plugins(unfiltered_plugins)
    assert win32_plugins
    for plugin in win32_plugins:
        assert 'win32' in plugin.plugin_object.os

    monkeypatch.setattr(sys, 'platform', 'fake-dos')
    fakeos_plugins = plugin_manager._get_supported_plugins(unfiltered_plugins)
    assert not fakeos_plugins


@pytest.mark.parametrize('plugin_name, plugin_category', [
    ('Audio Feedback', 'Output'),
    ('Video Preview', 'Output'),
    ('Rss FeedParser', 'Importer'),
    ('CSV Importer', 'Importer')
])
def test_get_plugin_by_name(plugin_manager, plugin_name, plugin_category):
    """
    Verify that the get_plugin_by_name function returns given existing functions.
    """
    plugin = plugin_manager.get_plugin_by_name(plugin_name, plugin_category)
    assert plugin.plugin_object
    assert plugin.plugin_object.name == plugin_name
    assert plugin.plugin_object.CATEGORY == plugin_category


def test_get_plugin_by_name_fake_plugin(plugin_manager):
    """
    Verify that the get_plugin_by_name function does not return values when a fake name or category is given.
    """
    assert not plugin_manager.get_plugin_by_name('fakename', 'no category')
    assert not plugin_manager.get_plugin_by_name('Audio Feedback', 'fake category')
    assert not plugin_manager.get_plugin_by_name('fakename', 'Output')


@pytest.mark.parametrize('platform', ['linux2', 'win32', 'darwin', 'fake-dos'])
def test_get_all_plugins(plugin_manager, monkeypatch, plugin_platform_category_cache, platform):
    """
    Verifies that get_all_plugins() finds the correct number of plugins for each of the specified
    platforms. Verifies that 0 plugins are found for a platform that does not exist.
    """
    monkeypatch.setattr(sys, 'platform', platform)
    plugins = plugin_manager.get_all_plugins()
    assert len(plugins) == sum(plugin_platform_category_cache[platform].values())


@pytest.mark.parametrize('platform', ['win32', 'darwin', 'linux', 'linux2', 'fake-dos'])
def test_get_plugins_of_category(plugin_manager, plugin_platform_category_cache, monkeypatch, platform):
    """
    Assert that fetching plugins by categories works for multiple platforms.

    This assertion is checked by counting the number of platform compatible plugins.
    """

    monkeypatch.setattr(sys, 'platform', platform)
    audioinput_count = plugin_platform_category_cache[platform]['audioinput']
    audiomixer_count = plugin_platform_category_cache[platform]['audiomixer']
    videoinput_count = plugin_platform_category_cache[platform]['videoinput']
    videomixer_count = plugin_platform_category_cache[platform]['videomixer']
    importer_count = plugin_platform_category_cache[platform]['importer']
    output_count = plugin_platform_category_cache[platform]['output']

    # Categories: AudioInput, AudioMixer, VideoInput, VideoMixer, Importer, Output
    assert len(plugin_manager.get_plugins_of_category('AudioInput')) == audioinput_count
    assert len(plugin_manager.get_plugins_of_category('AudioMixer')) == audiomixer_count
    assert len(plugin_manager.get_plugins_of_category('VideoInput')) == videoinput_count
    assert len(plugin_manager.get_plugins_of_category('VideoMixer')) == videomixer_count
    assert len(plugin_manager.get_plugins_of_category('Importer')) == importer_count
    assert len(plugin_manager.get_plugins_of_category('Output')) == output_count


@pytest.mark.parametrize('platform', ['win32', 'darwin', 'linux', 'linux2', 'fake-dos'])
def test_get_category_plugins(plugin_manager, plugin_platform_category_cache, monkeypatch, platform):
    """This test asserts that plugin getting commands work on multiple platforms."""
    monkeypatch.setattr(sys, 'platform', platform)
    audioinput_count = plugin_platform_category_cache[platform]['audioinput']
    audiomixer_count = plugin_platform_category_cache[platform]['audiomixer']
    videoinput_count = plugin_platform_category_cache[platform]['videoinput']
    videomixer_count = plugin_platform_category_cache[platform]['videomixer']
    importer_count = plugin_platform_category_cache[platform]['importer']
    output_count = plugin_platform_category_cache[platform]['output']

    assert len(plugin_manager.get_audioinput_plugins()) == audioinput_count
    assert len(plugin_manager.get_audiomixer_plugins()) == audiomixer_count
    assert len(plugin_manager.get_videoinput_plugins()) == videoinput_count
    assert len(plugin_manager.get_videomixer_plugins()) == videomixer_count
    assert len(plugin_manager.get_importer_plugins()) == importer_count
    assert len(plugin_manager.get_output_plugins()) == output_count


class TestFakeConfig(Config):
    foo = options.StringOption("Bar")
    i = options.IntegerOption(0)
    pi = options.FloatOption(3.14)
    not_true = options.BooleanOption(False)


class TestFakePlugin(IAudioInput):
    name = 'Fake Plugin'
    os = ['fake-dos']
    CONFIG_CLASS = TestFakeConfig


def test_load_plugin_config(plugin_manager):
    """
    Test that if a plugin sets a CONFIG_CLASS attribute then the configuration can be loaded.

    - Verifies that PluginManager.load_plugin_config() returns a configuration when a CONFIG_CLASS is present and that
    the load_plugin_config() method does not set the plugin_object.config attribute.
    - Verifies that IBackendPlugin.load_config() sets a plugin_object.config attribute when a CONFIG_CLASS is specified
    """
    plugins = plugin_manager.get_all_plugins()
    for plugin in plugins:
        if plugin.plugin_object.CONFIG_CLASS:
            assert plugin_manager.load_plugin_config(plugin.plugin_object.CONFIG_CLASS, plugin.plugin_object.get_section_name())
            assert not hasattr(plugin.plugin_object, 'config')
            plugin.plugin_object.load_config(plugin_manager)
            assert plugin.plugin_object.config
        else:
            assert not plugin_manager.load_plugin_config(plugin.plugin_object.CONFIG_CLASS, plugin.plugin_object.get_section_name())


def test_load_fake_config(plugin_manager):
    """
    Test that when a plugin with a CONFIG_CLASS loads its configuration, that all of the configuration values are valid.
    """
    fake_plugin = TestFakePlugin()
    fake_plugin.load_config(plugin_manager)
    assert fake_plugin.config.foo == 'Bar'
    assert fake_plugin.config.i == 0
    assert fake_plugin.config.pi == 3.14
    assert not fake_plugin.config.not_true


def test_load_fake_plugin_config(plugin_manager):
    """
    Test that when the PluginManager calls load_plugin_config() an instance of the plugin's CONFIG_CLASS is returned
    with the correct values.
    """
    fake_plugin = TestFakePlugin()
    fake_config = plugin_manager.load_plugin_config(fake_plugin.CONFIG_CLASS, fake_plugin.get_section_name())
    assert fake_config.foo == 'Bar'
    assert fake_config.i == 0
    assert fake_config.pi == 3.14
    assert not fake_config.not_true
