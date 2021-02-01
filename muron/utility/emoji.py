from utility.loader import conf

custom_emoji = {}

def load_custom_emojis(bot):
    """Load all custom emojis from ressource servers"""
    global custom_emoji
    resource_servers = conf('resource_servers')
    for server_id in resource_servers:
        emojis = bot.get_guild(server_id).emojis
        for emoji in emojis:
            custom_emoji[emoji_to_str(emoji)] = server_id


def str_to_emoji(emoji_str,bot):
    """Return the emoji, handle custom emoji case"""
    global custom_emoji
    if emoji_str[0] == ':' and emoji_str[-1] == ':': # custom
        guild_id = custom_emoji.get(emoji_str,None)
        if guild_id is not None:
            guild_emojis = bot.get_guild(guild_id).emojis
            for guild_e in guild_emojis:
                if guild_e.name == emoji_str[1:-1]:
                    return str(guild_e)
        raise Exception(f'Custom emoji not in ressource servers : {emoji_str}')
    return emoji_str
    #raise Exception('Wrong format for emoji, need \':\' ')

def emoji_to_str(emoji):
    if not isinstance(emoji,str):# handle custom
        return f':{emoji.name}:'
    return emoji

def emoji_bar(size,ratio,full,empty,bot,border_data=None):
    """Create a bar of emoji with the asked ratio"""
    bar = ""
    for i in range(size):
        if (i/(size-1) <= ratio) and (ratio > 0):
            bar += str_to_emoji(full,bot)
        else:
            bar += str_to_emoji(empty,bot)
    return bar