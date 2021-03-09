#!/usr/bin/env python3

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw, ImageFont
from pyquery import PyQuery as pq

parser = argparse.ArgumentParser(description='')

parser.add_argument('--source-url',
                    action='store',
                    nargs=1,
                    default='https://ragnarokonline.gungho.jp/gameguide/system/equip-powerup/special-enchant.html',
                    type=str,
                    help='import souce url')

parser.add_argument('--export-json',
                    action='store',
                    nargs=1,
                    default='./special_enchant.json',
                    type=str,
                    help='export path')

parser.add_argument('--items-url',
                    action='store',
                    nargs=1,
                    default='https://ragnarokonline.0nyx.net/assets/json/items.json',
                    type=str,
                    help='import items json url')

args = parser.parse_args()

def main(args: dict):
    with urllib.request.urlopen(args.source_url) as response:
        html = response.read()

    with urllib.request.urlopen(args.items_url) as response:
        items_data = json.load(response)

    dom = pq(html)

    enchant_list: dict = {}
    enchant_npc: str = None

    slot_numbering = {
        "第1エンチャント": "第4スロット",
        "第2エンチャント": "第3スロット",
        "第3エンチャント": "第2スロット",
        "第4エンチャント": "第1スロット",
        "1番目に選択できるエンチャント": "第4スロット",
        "2番目に選択できるエンチャント": "第3スロット",
        "3番目に選択できるエンチャント": "第2スロット",
        "4番目に選択できるエンチャント": "第1スロット",
        "スロットエンチャント": "第1スロット",
    }

    for doc in dom('#main3column > h3,table').items():
        if doc.text() == "スペシャルエンチャントを行うには":
            continue

        if doc("h3 > span"):
            #エンチャントNPC
            enchant_npc = doc("h3 > span").text()
            enchant_npc = re.sub(r"^(NPC.+」).*$", "\\1", enchant_npc)
            enchant_list[enchant_npc] = {"target_items":{}}
        elif doc("table"):
            items = doc("table")("thead > tr > th:nth-child(1)").html()
            description = doc("table")("thead > tr > th:nth-child(2)").text().replace("\n","")

            items = items.split("<br />")
            for item in items:
                enchant_list[enchant_npc]["target_items"][item] = {
                    "description": description,
                    "slot":{}
                }

                enchants_dataset = []
                enchant_slot = doc("table")("tbody > tr > td:nth-child(1)")
                for slot in enchant_slot:
                    slot = pq(slot)
                    text = slot.text()
                    slot_message = re.sub(r"^(.+?エンチャント)[\n]?.*$", "\\1", text)
                    slot_smelting = None
                    if "精錬値" in text:
                        slot_smelting = re.sub(r"^.*\n.+?([0-9]+).+$", "\\1", text)

                    enchants = [ value for value in slot.next().text()
                        .replace("?","-")
                        .replace("-"," - ")
                        .replace("+"," + ")
                        .replace("Special","Special ")
                        .replace("＜","<")
                        .replace("＞",">")
                        .split("、") if value != ""]

                    if len(enchants) > 0:
                        enchants_dataset = [] # initialize

                    for name in enchants:
                        item_ids = [key for key, value in items_data.items() if value["displayname"] == name]
                        if len(item_ids) > 0:
                            item_id = item_ids[0]
                            enchants_dataset.append({
                                "id": item_id,
                                "displayname": items_data[item_id]["displayname"],
                                "description": items_data[item_id]["description"]
                            })

                    enchant_list[enchant_npc]["target_items"][item]["slot"][slot_numbering[slot_message]] = {
                        "message": slot_message,
                        "smelting": slot_smelting,
                        "enchants": enchants_dataset
                    }
    with open(args.export_json, "w", encoding="utf-8") as fp:
        json.dump(enchant_list, fp, indent=1, ensure_ascii=False)

if __name__ == '__main__':
    main(args)
