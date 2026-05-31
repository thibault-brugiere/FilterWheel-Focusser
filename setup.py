# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# setup.py - Device setup endpoints.
#
# Part of the AlpycaDevice Alpaca skeleton/template device driver
#
# Author:   Robert B. Denny <rdenny@dc3.com> (rbd)
#
# Python Compatibility: Requires Python 3.7 or later
# GitHub: https://github.com/ASCOMInitiative/AlpycaDevice
#
# -----------------------------------------------------------------------------
# MIT License
#
# Copyright (c) 2022-2024 Bob Denny
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
# Edit History:
# 27-Dec-2022   rbd V0.1 Initial edit. Simply say no GUI.
# 30-Dec-2022   rbd V0.1 Device number captured and sent to responder
#

import json
import os
from falcon import Request, Response
from shr import PropertyResponse, DeviceMetadata, log_request

PARAMS_FILE = "filterwheel_parameters.json"

class svrsetup:
    def on_get(self, req: Request, resp: Response):
        log_request(req)
        resp.content_type = 'text/html'
        resp.text = '<!DOCTYPE html><html><body><h2>Server setup is in config.toml</h2></body></html>'

from pathlib import Path

# Fichier JSON des paramètres
PARAMS_FILE = Path(__file__).parent / "filterwheel_parameters.json"


class devsetup:
    def on_get(self, req: Request, resp: Response, devnum: str):
        resp.content_type = 'text/html'
        if PARAMS_FILE.exists():
            with open(PARAMS_FILE, "r", encoding="utf-8") as f:
                params = f.read()
        else:
            params = "{}"

        resp.text = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Filterwheel Setup (same than focuser)</title>
            <style>
                body {{
                    background-color: #121212;
                    color: #e0e0e0;
                    font-family: Arial, sans-serif;
                }}
                textarea {{
                    width: 100%;
                    max-width: 800px;
                    height: 400px;
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    border: 1px solid #444;
                    padding: 10px;
                    font-family: monospace;
                    font-size: 14px;
                }}
                button {{
                    background-color: #007acc;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    font-size: 14px;
                    cursor: pointer;
                    margin-top: 10px;
                }}
                button:hover {{
                    background-color: #005f99;
                }}
            </style>
        </head>
        <body>
            <h2>Filterwheel Setup</h2>
            <textarea id="editor">{params}</textarea><br>
            <button id="saveBtn">Enregistrer</button>

            <script>
            const editor = document.getElementById("editor");
            document.getElementById("saveBtn").onclick = async () => {{
                try {{
                    const resp = await fetch(window.location.href, {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: editor.value
                    }});
                    if (resp.ok) {{
                        alert("✅ Paramètres enregistrés avec succès !");
                    }} else {{
                        const data = await resp.json();
                        alert("❌ Erreur : " + data.message);
                    }}
                }} catch(e) {{
                    alert("❌ Erreur réseau : " + e);
                }}
            }};
            </script>
        </body>
        </html>
        """

    def on_post(self, req: Request, resp: Response, devnum: str):
        try:
            data = req.bounded_stream.read().decode("utf-8")
            json_obj = json.loads(data)
            with open(PARAMS_FILE, "w", encoding="utf-8") as f:
                json.dump(json_obj, f, indent=4)

            resp.content_type = "application/json"
            resp.status = 200
            resp.text = json.dumps({"status": "ok", "message": "Paramètres enregistrés"})
        except Exception as e:
            resp.content_type = "application/json"
            resp.status = 400
            resp.text = json.dumps({"status": "error", "message": str(e)})