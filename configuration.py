import logging
import json
from typing import Any, List


class Fields:
    Token = 'token'
    Guilds = 'guilds'
    Owner = 'owner'
    DevGuild = 'development_guild'
    MaxChannels = 'channels_per_guild'


class Configuration:

    DEFAULT_SETTINGS = {
        Fields.Owner: None,
        Fields.DevGuild: None,
        Fields.Token: None,
        Fields.MaxChannels: 2,
        Fields.Guilds: {}
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.options: dict = {}

    def add_guild(self, guild_id: int, guild_name: str):
        """
        Add a default configuration for a guild if it doesn't exist

        :param guild_id: The guild's ID
        :param guild_name: The canonical name of the guild
        :return:
        """
        gid = str(guild_id)
        if gid in self.options[Fields.Guilds].keys():
            return

        self.options[Fields.Guilds][gid] = {
            'allowed_channel': None,
            'name': guild_name,
            'channels': {}
        }

    def get_channels(self, guild_id: int) -> dict[str, Any]:
        return self.options[Fields.Guilds][str(guild_id)]['channels']

    def add_channel(self, guild_id: int, channel_id: int) -> str:
        channels: dict[str, Any] = self.get_channels(guild_id)

        if len(channels.keys()) >= self.options[Fields.MaxChannels]:
            return 'Channel limit reached'

        # Check if the channel already exists
        if channels.get(str(channel_id), None) is not None:
            return 'Channel already exists'

        # For now, don't catch invalid guild_ids because I want to know if it fails
        channels[str(channel_id)] = {}
        return f'Channel set to ID {channel_id}'

    def remove_channel(self, guild_id: int, channel_id: int) -> bool:
        channels = self.get_channels(guild_id)

        if str(channel_id) not in channels:
            return False

        del channels[str(channel_id)]
        return True

    def channel_is_allowed(self, guild_id: int, channel_id: int) -> bool:

        return str(channel_id) in self.options[Fields.Guilds][str(guild_id)]['channels']

    def get_dev_guild(self) -> int:
        return int(self.options[Fields.DevGuild])

    def load(self, filename: str) -> None:
        self.logger.info(f'Loading configuration from file: {filename}')
        try:
            file = open(filename, 'r')
        except OSError:
            self.options = Configuration.DEFAULT_SETTINGS.copy()
            self.save(filename)
            file = open(filename, 'r')
        self.options = json.loads(file.read())
        file.close()

        self.logger.debug(str(self.options))

        for k, v in Configuration.DEFAULT_SETTINGS.items():
            value = self.options.get(k, None)
            if value is None:
                self.options[k] = v
        # maybe save here since things might get added

        self.verify_types()

    def save(self, filename: str) -> None:
        self.logger.info(f'Saving configuration to file: {filename}')
        self.logger.debug(str(self.options))
        file = open(filename, 'w')
        file.write(json.dumps(self.options, indent=2, separators=(', ', ': ')))
        file.close()

    def verify_types(self):
        try:
            assert type(self.options[Fields.Owner]) == str, 'Owner ID needs to be a string'
            assert type(self.options[Fields.Token]) == str, 'Bot Token needs to be a string'
            assert type(self.options[Fields.Guilds]) == dict, 'Guild dictionary is not a dictionary'
            assert type(self.options[Fields.DevGuild]) == str, 'Development guild needs to be a valid string ID'
        except AssertionError as ex:
            self.logger.critical(ex)
            raise


if __name__ == '__main__':
    config = Configuration()
    config.load('config.txt')
