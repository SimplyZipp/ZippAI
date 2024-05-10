import logging
import typing
import asyncio
from collections.abc import Callable
import discord
from discord.ext import commands
from discord import app_commands
from configuration import Configuration, Fields
from discordhandlers.abstracthandler import Handler, BasicMessage

# Maybe set roles for command usage

# TODO: Remove from channels and guilds
# If a channel is deleted from a guild, automatically remove it from config
# If bot is removed from a guild, delete the guild config


class DiscordClient(commands.Bot):

    def __init__(self,
                 *,
                 handler: Handler,
                 config: Configuration,
                 intents: discord.flags.Intents = None,
                 **kwargs):
        super().__init__(command_prefix='$',
                         intents=get_intents() if intents is None else intents,  # Default intents if none specified
                         **kwargs)
        self.handler = handler
        self.logger = logging.getLogger(__name__)
        self.config = config

        asyncio.run(self.add_cog(Commands(self)))

    async def on_ready(self) -> None:
        for guild in self.guilds:
            self.config.add_guild(guild.id, guild.name)
        self.logger.info(f'Logged on as {self.user}')

    async def on_message(self, message: discord.Message) -> None:
        self.logger.debug(f'{message.channel}[ID: {message.channel.id}]: Message from {message.author}')
        if message.author == self.user:
            return
        if message.author.bot:
            return

        if not self.config.channel_is_allowed(message.guild.id, message.channel.id):
            self.logger.debug(f'Message from disallowed channel {message.channel.name}')
            return

        if message.content is None:
            self.logger.info('Message is None')
            return
        msg = BasicMessage(message.content, user=message.author.name, channel_id=message.channel.id, guild_id=message.guild.id)
        response = await self.handler.respond(msg)
        if response is not None:
            await message.channel.send(response)


class Commands(commands.Cog):
    def __init__(self, bot: DiscordClient):
        """
        A discord.py Cog housing all the commands this bot can use.

        :param bot: A reference to the bot this Cog is being attached to
        """
        self.bot = bot

    @app_commands.command(name='add-channel', description='Add a channels the bot can listen to. Limited number per guild.')
    @app_commands.default_permissions(manage_channels=True)
    async def add_channel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        """
        Sets the bots active channel (one per guild). Guild and channel IDs are stored as strings

        :param interaction:
        :param channel:
        :return: None
        """
        # TODO: Check for permissions
        opts = await self.bot.handler.get_default_options()
        msg = self.bot.config.add_channel(interaction.guild_id, channel.id, opts)
        await interaction.response.send_message(msg, ephemeral=True)  # noqa

    @app_commands.command(name='remove-channel', description='Remove a channels from the bots allowed list.')
    @app_commands.default_permissions(manage_channels=True)
    async def remove_channel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        # TODO: Check for permissions
        msg = self.bot.config.remove_channel(interaction.guild_id, channel.id)
        await interaction.response.send_message(msg, ephemeral=True)  # noqa

    @app_commands.command(name='channels', description='Return a list of channels the bot listens to.')
    async def get_channels(self, interaction: discord.Interaction):
        name_list: typing.List[str] = []
        for ch_id in self.bot.config.get_channels(interaction.guild_id):
            name_list.append(interaction.guild.get_channel(int(ch_id)).name)
        await interaction.response.send_message(', '.join(name_list), ephemeral=True)  # noqa

    @app_commands.command(name='set-option', description='Set an option to give the generator. Fine tuning these can drastically change generator responses')
    async def set_option(self, interaction: discord.Interaction, option: str, value: str):
        msg = await self.bot.handler.set_option(option, value, interaction.guild_id, interaction.channel_id)
        await interaction.response.send_message(msg, ephemeral=True)  # noqa

    @set_option.autocomplete('option')
    async def set_option_autocomplete(self,
                                      interaction: discord.Interaction,
                                      current: str
                                      ) -> typing.List[app_commands.Choice[str]]:
        options = await self.bot.handler.get_options()
        choices = []
        for opt in options:
            if current in opt:
                choices.append(app_commands.Choice(name=opt, value=opt))
        return choices

    @app_commands.command(name='sync', description='Syncs the bots commands with the current guild, or globally if True.')
    @app_commands.rename(globally='global')
    @app_commands.default_permissions(manage_guild=True)
    async def sync_commands(self, interaction: discord.Interaction, globally: typing.Optional[bool] = False) -> None:
        """
        Syncs the bots commands with the *current guild, or globally if True.

        *only syncs to the test guild right now.

        :param interaction:
        :param globally: True to sync globally. Default: False
        :return: None
        """
        if str(interaction.user.id) != self.bot.config.options[Fields.Owner]:
            await interaction.response.send_message('You must be the owner to sync globally.', ephemeral=True)  # noqa
            return
        if not globally:
            guild = interaction.guild  # discord.Object(id=self.bot.config.get_dev_guild())
            self.bot.tree.copy_global_to(guild=guild)
            message = 'Synced!'
        else:
            guild = None
            message = 'Sent global sync request. Can take up to an hour to have an effect.'
        await self.bot.tree.sync(guild=guild)
        await interaction.response.send_message(message, ephemeral=True)  # noqa


def get_intents() -> discord.flags.Intents:
    """
    Get the default intents that this bot needs to run.

    Currently only requires message access.

    :return: The intents
    """
    intents = discord.Intents.default()
    intents.message_content = True
    return intents
