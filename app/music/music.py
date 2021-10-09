from discord import Embed

BOT_ICON_URL = "https://cdn.discordapp.com/attachments/797083893014462477/896312760084889600/unknown.png"
class Music:
    def __init__(self, details: object):
        self.__details = details

    def get(self, *keys):
        data = {}
        for key in keys:
            if key:
                data[key] = self.__details[key]
            else:
                raise MusicError(f"{key.capitalize()} does not exist.")
        
        return data

    def get_details(self, simplified=True):
        fields = ["title", "channel", "duration", "thumbnail", "url", "like_count", "dislike_count"]
        return self.get(*fields) if simplified else self.__details

    def generate_embed(self, header: str, simplified=False, color=0xff0059, icon_url=BOT_ICON_URL):
        embed = (Embed(title=self.__details["title"], url=self.__details["url"]["display"], color=color)
            .set_thumbnail(url=self.__details["thumbnail"])
            .set_footer(text="Made with love by Laplace ❤️"))

        if header:
            embed.set_author(name=header, icon_url=icon_url)
        
        if not simplified:
             (embed.add_field(name="📺 Channel", value=self.__details["channel"])
            .add_field(name="🕒 Duration", value=self.__details["duration"], inline=False)
            .add_field(name="👍 Likes", value=self.__details["like_count"])
            .add_field(name="👎 Dislikes", value=self.__details["dislike_count"]))

        return embed

class MusicError(Exception):
    def __init__(self, *args):
        self.message = args[0] if args else None

    def __str__(self):
        return f"MUSIC ERROR: {self.message}" if self.message else f"MUSIC ERROR has been raised!"