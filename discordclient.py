import logging
import typing
from collections.abc import Callable
import discord
from discord.ext import commands
from discord import app_commands
from configuration import Configuration, Fields
import asyncio

# Maybe set roles for command usage

# TODO: Remove from channels and guilds
# If a channel is deleted from a guild, automatically remove it from config
# If bot is removed from a guild, delete the guild config


class BasicMessage:

    def __init__(self, message: str, *, user: str, unique_id: str | None):
        self.content = message
        self.user = user
        self.id = unique_id


class DiscordClient(commands.Bot):

    def __init__(self,
                 *,
                 response_callable: Callable[[BasicMessage], typing.Awaitable[str | None]] | None = None,
                 config: Configuration,
                 intents: discord.flags.Intents = None,
                 **kwargs):
        super().__init__(command_prefix='$',
                         intents=get_intents() if intents is None else intents,  # Default intents if none specified
                         **kwargs)
        self.response_call = response_callable
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

        if self.response_call is None:
            self.logger.warning('No message response callable setup!')
            return
        if message.content is None:
            self.logger.info('Message is None')
            return
        msg = BasicMessage(message.content, user=message.author.name, unique_id=str(message.channel.id))
        response = await self.response_call(msg)
        if response is not None:
            await message.channel.send(response)


class Commands(commands.Cog):
    def __init__(self, bot: DiscordClient):
        """
        A discord.py Cog housing all the commands this bot can use.

        :param bot: A reference to the bot this Cog is being attached to
        """
        self.bot = bot

    @app_commands.command(name='add-channel')
    async def add_channel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        """
        Sets the bots active channel (one per guild). Guild and channel IDs are stored as strings

        :param interaction:
        :param channel:
        :return: None
        """
        # TODO: Check for permissions
        msg = self.bot.config.add_channel(interaction.guild_id, channel.id)
        await interaction.response.send_message(msg, ephemeral=True)  # noqa

    @app_commands.command(name='remove-channel')
    async def remove_channel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        # TODO: Check for permissions
        if self.bot.config.remove_channel(interaction.guild_id, channel.id):
            await interaction.response.send_message(f'Removed channel ID {channel.id}', ephemeral=True)  # noqa
        else:
            await interaction.response.send_message('Channel hasn\'t been added', ephemeral=True)  # noqa

    @app_commands.command(name='sync')
    @app_commands.rename(globally='global')
    async def sync_commands(self, interaction: discord.Interaction, globally: typing.Optional[bool] = False) -> None:
        """
        Syncs the bots commands with the *current guild, or globally if True.

        *only syncs to the test guild right now.

        :param interaction:
        :param globally: True to sync globally. Default: False
        :return: None
        """
        if str(interaction.user.id) != self.bot.config.options[Fields.Owner]:
            return
        if not globally:
            guild = discord.Object(id=self.bot.config.get_dev_guild())
            self.bot.tree.copy_global_to(guild=guild)
            message = 'Synced!'
        else:
            guild = None
            message = 'Sent global sync request. Can take up to 24 hours to have an effect.'
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
