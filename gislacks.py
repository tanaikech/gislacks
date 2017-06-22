# -*- coding: utf-8 -*-

"""
    gislacks.py
    Submitter of text files from Sublime Text to Gist and Slack.
    This can submit editing a text file at Sublime Text to Gist, Slack and both.
    https://github.com/tanaikech/gislacks
    June 22, 2017 - version 1.0.0
"""

import sublime
import sublime_plugin

from datetime import datetime
from urllib.parse import urlparse, parse_qs
import json
import re
import os
import subprocess


class gislacks:

    def __init__(self, s, edit):
        """This is defined by calling as an instance.
        @param command sublime_plugin.TextCommand
        @param edit sublime.Edit
        """
        self.app = "gislack"
        self.s = s
        self.edit = edit
        self.settings = sublime.load_settings("gislacks.sublime-settings")
        self.sview = s.view
        self.slack_channel = self.settings.get("slack_channel")
        self.fullpath = self.sview.file_name()
        self.wdir = self.__wd()
        self.gislack_cfgpath = self.__cfgd()
        self.gislack_path = self.settings.get("gislack_path")
        self.flag = ""
        self.msg = '''\
### gislack is not found ###
If gislack is not in path, please set it.
Or you can set the path to 'gislack_path' in 'gislacks.sublime-settings'

If you have not gislack, please get gislack from https://github.com/tanaikech/gislack.

$ go get -u github.com/tanaikech/gislack

Also you can directly get the execution file from https://github.com/tanaikech/gislack/releases

After get it, at first, please retrieve client ID and client secret for GitHub and Slack.
Then, push [Ctrl + Shift + p] and run [gislacks: Authorization Gist] and [gislacks: Authorization Slack].

By these, access tokens are retrieved on Sublime.
You can submit scripts to Gist and Slack using this plugin.
You can see the detail information at https://github.com/tanaikech/gislack'''

    def __wd(self):
        """Function to set working directory
        """
        if len(self.sview.window().folders()) == 0:
            wd = ""
            if os.environ.get('HOME') is not None:
                wd = os.environ.get('HOME')
            elif os.environ.get('USERPROFILE') is not None:
                wd = os.environ.get('USERPROFILE')
            else:
                wd = "./"
            msg = "Please open folder for working.\n\nFile -> Open Folder\n\nNow '%s' is used as a working folder." % wd
            sublime.message_dialog(msg)
            return wd
        else:
            return self.sview.window().folders()[0]

    def __cfgd(self):
        """Function to set gislack.cfg directory
        """
        if self.settings.get("gislack_cfgpath") != "":
            return self.settings.get("gislack_cfgpath")
        else:
            return self.wdir

    def __exe(self, args):
        """Function to execute gislack commands
        @param args Strings
        """
        cmd = [
            os.path.join(self.settings.get("gislack_path"), self.app),
            "json",
            "--json=" + json.dumps(args)
        ]
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        ).communicate()

    def appCheck(self):
        """Function to check the existence of gislack
        """
        res = self.__exe({
            "command": "appcheck",
            "options": {
                "appcheck": True,
            }
        })
        if len(res[1]) == 0:
            return True
        else:
            self.dispResult(self.msg)
            sublime.message_dialog(self.msg)
            return False

    def Get(self, args):
        """Function to send json data of gislack commands to __exe()
        @param args json data of gislack commands
        """
        if self.appCheck() is True:
            if args["options"]["cfgdirectory"] == "":
                args["options"]["cfgdirectory"] = self.wdir
            res = self.__exe(args)
            if len(res[1]) == 0:
                return res[0].decode('utf-8')
            else:
                return res[1].decode('utf-8')
        else:
            return None

    def dispResult(self, result):
        """Function to display results
        @param results Strings
        """
        d = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        od = "[" + d + "] "
        window = self.sview.window()
        view = window.get_output_panel("exec")
        window.run_command("hide_panel", {"panel": "output.exec"})
        window.run_command("show_panel", {"panel": "output.exec"})
        view.set_read_only(False)
        view.insert(self.edit, view.size(), od + result)
        view.set_read_only(True)

    def initAuth(self, flag):
        """Function to initialize the authorization process
        @param flag gist or slack
        """
        print("path = " + self.gislack_cfgpath)
        if self.appCheck() is True:
            self.flag = flag

            def on_done(data):
                datar = data.split(",")
                if len(datar) > 2 or len(datar) == 1:
                    sublime.message_dialog("Error: Wrong inputted data.")
                    return

                ok = sublime.ok_cancel_dialog("Your client id and secret are\n{}\n{}\nAre those ok?".format(datar[0].strip(), datar[1].strip()))
                if ok is not True:
                    if self.flag == "gist":
                        exe = "gislacks_authgist"
                    elif self.flag == "slack":
                        exe = "gislacks_authslack"
                    self.sview.run_command(exe)
                    return
                self.getCode(datar)

            if self.flag == "gist":
                msg_done = "Input client ID and client Secret for GitHub"
                msg_cancel = "## YourClientId ##, ## YourClientSecret ##"
            elif self.flag == "slack":
                msg_done = "Input client ID and client Secret for Slack"
                msg_cancel = "## YourClientId ##, ## YourClientSecret ##"
            sublime.active_window().show_input_panel(msg_done, msg_cancel, on_done, None, None)

    def getCode(self, datar):
        """Function to get authorization code
        @param dataar Array included client ID and secret
        """
        if self.flag == "gist":
            args = {
                "command": "auth",
                "options": {
                    "gistclientid": datar[0].strip(),
                    "gistclientsecret": datar[1].strip(),
                    "cfgdirectory": self.gislack_cfgpath
                }
            }
        elif self.flag == "slack":
            args = {
                "command": "auth",
                "options": {
                    "slackclientid": datar[0].strip(),
                    "slackclientsecret": datar[1].strip(),
                    "cfgdirectory": self.gislack_cfgpath
                }
            }
        res = self.Get(args)
        sublime.set_clipboard(res)
        sublime.message_dialog("Now, URL for retrieving authorization code was imported to your clipboard.\n\nPlease paste the URL to your browser, and authorize.\nRetrieve and copy the authorization code.\n\n### After you can copy the code (to clipboard), click OK.")
        code = sublime.get_clipboard()

        def on_done(data):
            q = parse_qs(urlparse(data).query)
            if ("code" in q) is True:
                code = q["code"][0]
            else:
                code = data
                if "http" in code:
                    sublime.message_dialog("Error: Wrong code.")
                    return
            self.getAccesstoken(code, datar)

        sublime.active_window().show_input_panel("The code is displayed, please push the enter key. If you cannot see the code, please paste the code you got.", code, on_done, None, None)

    def getAccesstoken(self, data, datar):
        """Function to get access token
        @param data Code
        @param dataar Array included client ID and secret
        """
        if self.flag == "gist":
            args = {
                "command": "auth",
                "options": {
                    "gistcode": data,
                    "cfgdirectory": self.gislack_cfgpath,
                    "gistclientid": datar[0].strip(),
                    "gistclientsecret": datar[1].strip()
                }
            }
        elif self.flag == "slack":
            args = {
                "command": "auth",
                "options": {
                    "slackcode": data,
                    "cfgdirectory": self.gislack_cfgpath,
                    "slackclientid": datar[0].strip(),
                    "slackclientsecret": datar[1].strip()
                }
            }
        res = self.Get(args)
        if res is None:
            sublime.message_dialog("Error: Access token was not retrieved. Please confirm the code, your client ID and client secret.")
            return
        if str(res).strip() == "Done.":
            if self.flag == "gist":
                msg = "Access token for using Gist was retrieved!"
            elif self.flag == "slack":
                msg = "Access token for using Slack was retrieved!"
            sublime.message_dialog(msg)
        else:
            if res is not None:
                sublime.message_dialog(str(res))


class GislacksAuthgistCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        """Function to authorize GitHub
        @param edit sublime.Edit
        """
        gislacks(self, edit).initAuth("gist")


class GislacksAuthslackCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        """Function to authorize Slack
        @param edit sublime.Edit
        """
        gislacks(self, edit).initAuth("slack")


class GislacksUdoubleCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        """Function to submit a script to both Slack and Gist. For Gist, it is updated after 1st submit.
        @param edit sublime.Edit
        """
        g = gislacks(self, edit)
        if g.fullpath is not None:
            if g.settings.get("slack_channel") != "":
                oldfilewithpath = g.fullpath
                file_name = os.path.basename(oldfilewithpath)
                dst = file_name.replace('gist_updateid_', '')
                fid = re.match(r"(.*)_", dst)
                if fid:
                    try:
                        basefilename = dst.replace(fid.group(0), '')
                        res = g.Get({
                            "command": "doublesubmit",
                            "options": {
                                "cfgdirectory": g.settings.get("gislack_cfgpath"),
                                "updateoverwrite": fid.group(1),
                                "file": oldfilewithpath,
                                "filename": basefilename,
                                "channel": g.settings.get("slack_channel"),
                                "simpleresult": True
                            }
                        })
                        if "Error" in res:
                            sublime.message_dialog(res)
                        else:
                            g.dispResult(res)
                    except Exception as e:
                        sublime.message_dialog("Error: " + str(e))
                else:
                    res = g.Get({
                        "command": "doublesubmit",
                        "options": {
                            "cfgdirectory": g.settings.get("gislack_cfgpath"),
                            "file": g.fullpath,
                            "title": os.path.basename(g.fullpath),
                            "channel": g.settings.get("slack_channel")
                        }
                    })
                    if "Error" in res:
                        sublime.message_dialog("Error: " + res)
                    else:
                        g.dispResult(res)
                        window = self.view.window()
                        window.run_command('close_file')
                        view = window.new_file()
                        filename = "gist_updateid_" + json.loads(res)["gist_response"]["id"] + "_" + os.path.basename(g.fullpath)
                        view.set_name(filename)
                        view.settings().set("auto_indent", False)
                        view.run_command("insert", {"characters": self.view.substr(sublime.Region(0, self.view.size()))})
                        view.set_scratch(True)
                        view.run_command("prompt_save_as")
            else:
                g.dispValues("Please set a channel name on Slack to 'gislacks.sublime-settings'.")
        else:
            sublime.message_dialog("Target file has not been opened.")


class GislacksDoubleCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        """Function to submit a script to both Slack and Gist.
        @param edit sublime.Edit
        """
        g = gislacks(self, edit)
        if g.fullpath is not None:
            if g.settings.get("slack_channel") != "":
                res = g.Get({
                    "command": "doublesubmit",
                    "options": {
                        "cfgdirectory": g.settings.get("gislack_cfgpath"),
                        "file": g.fullpath,
                        "title": os.path.basename(g.fullpath),
                        "channel": g.settings.get("slack_channel"),
                        "simpleresult": True
                    }
                })
                if "Error" in res:
                    sublime.message_dialog(res)
                else:
                    g.dispResult(res)
            else:
                g.dispValues("Please set a channel name on Slack to 'gislacks.sublime-settings'.")
        else:
            sublime.message_dialog("Target file has not been opened.")


class GislacksGistCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        """Function to submit a script to Gist
        @param edit sublime.Edit
        """
        g = gislacks(self, edit)
        if g.fullpath is not None:
            res = g.Get({
                "command": "gist",
                "options": {
                    "cfgdirectory": g.settings.get("gislack_cfgpath"),
                    "files": g.fullpath,
                    "title": os.path.basename(g.fullpath)
                }
            })
            if "Error" in res:
                sublime.message_dialog(res)
            else:
                g.dispResult(res)
        else:
            sublime.message_dialog("Target file has not been opened.")


class GislacksGetgistsCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        """Function to get list of gists
        @param edit sublime.Edit
        """
        g = gislacks(self, edit)
        res = g.Get({
            "command": "gist",
            "options": {
                "listasjson": True,
                "cfgdirectory": g.settings.get("gislack_cfgpath")
            }
        })
        if str.strip(res) == "No gists.":
            sublime.message_dialog("No gists.")
            return
        elif "Error" in res:
            sublime.message_dialog(res)
            return
        elif res is None:
            return
        ar = []
        ids = []
        for e in json.loads(res):
            dat = e["updated_at"] + " : " + e["description"]
            ar.append(dat)
            ids.append(e["id"])

        def selected(idx):
            if idx > -1:
                self.disp(g, edit, ids[idx])

        self.list_items = ar
        sublime.active_window().show_quick_panel(self.list_items, selected, sublime.MONOSPACE_FONT)

    def disp(self, g, edit, idxx):
        """Function to display results
        @param g gislacks()
        @param edit sublime.Edit
        @param idxx gist ID
        """
        res = g.Get({
            "command": "gist",
            "options": {
                "get": idxx,
                "cfgdirectory": g.settings.get("gislack_cfgpath")
            }
        })
        dat = json.loads(res)
        if len(dat[0]["files"]) == 1:
            content = ""
            filename = ""
            for e in dat[0]["files"].keys():
                content = dat[0]["files"][e]["content"].replace('\r', '')
                filename = dat[0]["files"][e]["filename"]
            window = self.view.window()
            view = window.new_file()
            filename = "gist_updateid_" + idxx + "_" + filename
            view.set_name(filename)
            view.settings().set("auto_indent", False)
            view.run_command("insert", {"characters": content})
            view.set_scratch(True)
            view.run_command("prompt_save_as")
        else:
            sublime.message_dialog("There are {} files for the gist you chose. This plugin can edit for a gist with only 1 file.".format(len(dat[0]["files"])))


class GislacksUpdategistCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        """Function to update gist
        @param edit sublime.Edit
        """
        g = gislacks(self, edit)
        if g.fullpath is not None:
            oldfilewithpath = g.fullpath
            dst = os.path.basename(oldfilewithpath).replace('gist_updateid_', '')
            fid = re.match(r"(.*)_", dst)
            if fid:
                try:
                    basefilename = dst.replace(fid.group(0), '')
                    res = g.Get({
                        "command": "gist",
                        "options": {
                            "cfgdirectory": g.settings.get("gislack_cfgpath"),
                            "updateoverwrite": fid.group(1),
                            "filenames": basefilename,
                            "files": oldfilewithpath
                        }
                    })
                    if "Error" in res:
                        sublime.message_dialog(res)
                    else:
                        g.dispResult(res)
                except Exception as e:
                    sublime.message_dialog("Error: " + str(e))
            else:
                sublime.message_dialog("This file cannot be used for updating Gists.")
        else:
            sublime.message_dialog("Target file has not been opened.")


class GislacksGetgisthistoryCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        """Function to get version history of a gist
        @param edit sublime.Edit
        """
        g = gislacks(self, edit)
        if g.fullpath is not None:
            fid = re.match(r"(.*)_", os.path.basename(g.fullpath).replace('gist_updateid_', ''))
            if fid:
                res = g.Get({
                    "command": "gist",
                    "options": {
                        "gethistory": fid.group(1),
                        "cfgdirectory": g.settings.get("gislack_cfgpath")
                    }
                })
                if str.strip(res) == "No gists.":
                    sublime.message_dialog("No gists.")
                    return
                elif "Error" in res:
                    sublime.message_dialog(res)
                    return
                elif res is None:
                    return
                ar = []
                ids = []
                for e in json.loads(res):
                    dat = e["committed_at"]
                    ar.append(dat)
                    ids.append(e["url"])

                def selected(idx):
                    if idx > -1:
                        self.disp(g, edit, ids[idx])

                self.list_items = ar
                sublime.active_window().show_quick_panel(self.list_items, selected, sublime.MONOSPACE_FONT)

            else:
                sublime.message_dialog("Gist history cannot be retrieved from this file.")
        else:
            sublime.message_dialog("Target file has not been opened.")

    def disp(self, g, edit, idxx):
        """Function to display results
        @param g gislacks()
        @param edit sublime.Edit
        @param idxx gist ID
        """
        res = g.Get({
            "command": "gist",
            "options": {
                "getversion": idxx,
                "cfgdirectory": g.settings.get("gislack_cfgpath")
            }
        })
        dat = json.loads(res)
        if len(dat[0]["files"]) == 1:
            content = ""
            filename = ""
            for e in dat[0]["files"].keys():
                content = dat[0]["files"][e]["content"].replace('\r', '')
                filename = dat[0]["files"][e]["filename"]
            window = self.view.window()
            view = window.new_file()
            view.set_name(filename)
            view.settings().set("auto_indent", False)
            view.run_command("insert", {"characters": content})
            view.set_scratch(True)
            view.run_command("prompt_save_as")
        else:
            sublime.message_dialog("There are {} files for the gist you chose. This plugin can edit for a gist with only 1 file.".format(len(dat[0]["files"])))


class GislacksSlackCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        """Function to submit a script to Slack
        @param edit sublime.Edit
        """
        g = gislacks(self, edit)
        if g.fullpath is not None:
            if g.settings.get("slack_channel") != "":
                res = g.Get({
                    "command": "slack",
                    "options": {
                        "cfgdirectory": g.settings.get("gislack_cfgpath"),
                        "file": g.fullpath,
                        "title": os.path.basename(g.fullpath),
                        "channel": g.settings.get("slack_channel"),
                    },
                })
                if "Error" in res:
                    sublime.message_dialog(res)
                else:
                    g.dispResult(res)
            else:
                g.dispValues("Please set a channel name on Slack to 'gislacks.sublime-settings'.")
        else:
            sublime.message_dialog("Target file has not been opened.")


class GislacksGetslackfilesCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        """Function to get file list of Slack
        @param edit sublime.Edit
        """
        g = gislacks(self, edit)
        res = g.Get({
            "command": "slack",
            "options": {
                "filelistasjson": True,
                "cfgdirectory": g.settings.get("gislack_cfgpath")
            }
        })
        if str.strip(res) == "No files.":
            sublime.message_dialog("No files.")
            return
        elif "Error" in res:
            sublime.message_dialog(res)
            return
        elif res is None:
            return
        ar = []
        ids = []
        dat = json.loads(res)
        for e in dat["files"]:
            dat = e["name"] + " - " + str(datetime.strptime(e["createdtime"], '%Y-%m-%dT%H:%M:%S+09:00')) + " - " + e["title"]
            ar.append(dat)
            ids.append(e["id"])

        def selected(idx):
            if idx > -1:
                self.disp(g, edit, ids[idx])

        self.list_items = ar
        sublime.active_window().show_quick_panel(self.list_items, selected, sublime.MONOSPACE_FONT)

    def disp(self, g, edit, idxx):
        """Function to display results
        @param g gislacks()
        @param edit sublime.Edit
        @param idxx file ID
        """
        res = g.Get({
            "command": "slack",
            "options": {
                "getfile": idxx,
                "cfgdirectory": g.settings.get("gislack_cfgpath")
            }
        })
        dat = json.loads(res)
        if len(dat["content"]) > 0:
            window = self.view.window()
            view = window.new_file()
            filename = dat["file"]["name"]
            view.set_name(filename)
            view.settings().set("auto_indent", False)
            view.run_command("insert", {"characters": dat["content"].replace('\r', '')})
            view.set_scratch(True)
            view.run_command("prompt_save_as")
        else:
            sublime.message_dialog("There are {} files for the gist you chose. This plugin can edit for a gist with only 1 file.".format(len(dat[0]["files"])))
