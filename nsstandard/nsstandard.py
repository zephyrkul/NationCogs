from random import randint

import discord
from discord.ext import commands

from __main__ import send_cmd_help
from cogs.utils import checks

from .utils.dataIO import dataIO

class NSStandard:

    def __init__(self, bot):
        self.bot = bot
        self.nsapi = None
        self.illion = ["million", "billion", "trillion"]
        self.zday = False # Global flag for Z-Day, since I don't see a way to detect it automatically

    @commands.command(pass_context=True)
    async def nation(self, ctx, *, nation):  # API requests: 2; non-API requests: 1
        """Retrieves general info about a specified NationStates nation"""
        self._checks(ctx.prefix)
        if nation[0] == nation[-1] and nation.startswith("\""):
            nation = nation[1:-1]
        data = self.nsapi.api("category", "demonym2plural", "flag", "founded", "freedom", "fullname", "influence", "lastactivity", "motto", "population", "region", "wa", "zombie" if self.zday else "fullname", self.nsapi.shard("census", scale="65+66", mode="score"), nation=nation).collect()
        regdata = self.nsapi.api("founder", region=data["region"]).collect()
        found = ""
        if regdata["founder"] == data["id"]:
            found = " (Founder)"
        endo = int(float(data["census"]["scale"][1]["score"]))
        if endo == 1:
            endo = "{:d} endorsement".format(endo)
        else:
            endo = "{:d} endorsements".format(endo)
        if data["founded"] == "0":
            data["founded"] = "in Antiquity"
        embed = discord.Embed(title=data["fullname"], url="https://www.nationstates.net/nation={}".format(data["id"]), description="[{}](https://www.nationstates.net/region={}){} | {} {} | Founded {}".format(
            data["region"], regdata["id"], found, self._illion(data["population"]), data["demonym2plural"], data["founded"]), colour=0x8bbc21 if self.zday else randint(0, 0xFFFFFF))
        embed.set_author(name="NationStates Z-Day" if self.zday else "NationStates",
                         url="https://www.nationstates.net/")
        embed.set_thumbnail(url=data["flag"])
        if self.zday:
            embed.add_field(name=data["zombie"]["zaction"].title() if data["zombie"]["zaction"] else "No Action", value="Survivors: {} | Zombies: {} | Dead: {}".format(self._illion(data["zombie"]["survivors"]), self._illion(data["zombie"]["zombies"]), self._illion(data["zombie"]["dead"])), inline=False)
        embed.add_field(name=data["category"], value="{}\t|\t{}\t|\t{}".format(data["freedom"]["civilrights"], data["freedom"]["economy"], data["freedom"]["politicalfreedom"]), inline=False)
        embed.add_field(name=data["unstatus"], value="{} | {:d} influence ({})".format(endo, int(float(data["census"]["scale"][0]["score"])), data["influence"]), inline=False)
        embed.set_footer(text="Last active {}".format(data["lastactivity"]))
        try:
            await self.bot.say(embed=embed)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission to send this")

    @commands.command(pass_context=True)
    async def region(self, ctx, *, region):  # API requests: 3; non-API requests: 1
        """Retrieves general info about a specified NationStates region"""
        self._checks(ctx.prefix)
        if region[0] == region[-1] and region.startswith("\""):
            region = region[1:-1]
        data = self.nsapi.api("delegate", "delegateauth", "flag", "founded", "founder", "name", "numnations", "power", "tags", "zombie" if self.zday else "name", region=region).collect()
        if data["delegate"] == "0":
            data["delegate"] = "No Delegate"
        else:
            deldata = self.nsapi.api("fullname", "influence", self.nsapi.shard(
                "census", scale="65+66", mode="score"), nation=data["delegate"]).collect()
            endo = int(float(deldata["census"]["scale"][1]["score"]))
            if endo == 1:
                endo = "{:d} endorsement".format(endo)
            else:
                endo = "{:d} endorsements".format(endo)
            data["delegate"] = "[{}](https://www.nationstates.net/nation={}) | {} | {:d} influence ({})".format(deldata[
                "fullname"], data["delegate"], endo, int(float(deldata["census"]["scale"][0]["score"])), deldata["influence"])
        if "X" in data["delegateauth"]:
            data["delegateauth"] = ""
        else:
            data["delegateauth"] = " (Non-Executive)"
        if data["founded"] == "0":
            data["founded"] = "in Antiquity"
        if data["founder"] == "0":
            data["founder"] = "No Founder"
        else:
            try:
                data["founder"] = "[{}](https://www.nationstates.net/nation={})".format(
                    self.nsapi.api("fullname", nation=data["founder"]).collect()["fullname"], data["founder"])
            except ValueError:
                data["founder"] = "{} (Ceased to Exist)".format(data[
                    "founder"].replace("_", " ").capitalize())
        embed = discord.Embed(title=data["name"], url="https://www.nationstates.net/region={}".format(data["id"]), description="[{} nations](https://www.nationstates.net/region={}/page=list_nations) | Founded {} | Power: {}".format(
            data["numnations"], data["id"], data["founded"], data["power"]), colour=0x8bbc21 if self.zday else randint(0, 0xFFFFFF))
        embed.set_author(name="NationStates Z-Day" if self.zday else "NationStates",
                         url="https://www.nationstates.net/")
        if data["flag"]:
            embed.set_thumbnail(url=data["flag"])
        if self.zday:
            embed.add_field(name="Zombies", value="Survivors: {} | Zombies: {} | Dead: {}".format(self._illion(data["zombie"]["survivors"]), self._illion(data["zombie"]["zombies"]), self._illion(data["zombie"]["dead"])), inline=False)
        embed.add_field(name="Founder", value=data["founder"], inline=False)
        embed.add_field(name="Delegate{}".format(
            data["delegateauth"]), value=data["delegate"], inline=False)
        tags = data["tags"]["tag"]
        embed.set_footer(text=tags if isinstance(tags, str)
                         else ", ".join(data["tags"]["tag"]))
        try:
            await self.bot.say(embed=embed)
        except discord.HTTPException:
            await self.bot.say("I need the `Embed links` permission to send this")

    def _illion(self, num: str):
        num = int(num)
        index = 0
        while num >= 1000:
            index += 1
            num = round(num) / 1e3
        return "{} {}".format(num, self.illion[index])

    def _checks(self, prefix):
        if self.nsapi is None or self.nsapi != self.bot.get_cog("NSApi"):
            self.nsapi = self.bot.get_cog("NSApi")
            if self.nsapi is None:
                raise RuntimeError(
                    "NSApi cog is not loaded. Please ensure it is:\nInstalled: {p}cog install NationCogs nsapi\nLoaded: {p}load nsapi".format(p=prefix))
        self.nsapi.check_agent()


def setup(bot):
    bot.add_cog(NSStandard(bot))