import discord
from discord import app_commands
from discord.ext import commands
from daug.utils.dpyexcept import excepter
from daug.utils.dpylog import dpylogger

MESSAGE_CREATE_VOICE = """新しくボイスチャンネルを作成しました。"""


async def create_voice(interaction: discord.Interaction):
    await interaction.response.send_message('新しくVCを作成します', ephemeral=True)
    new_channel = await interaction.guild.create_voice_channel(
        name=f'{interaction.user.display_name}の部屋',
        category=interaction.guild.get_channel(interaction.channel.category_id),
    )
    await new_channel.send(f'{interaction.user.mention} {MESSAGE_CREATE_VOICE}')


class VoiceChannelConfigButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='VC作成', style=discord.ButtonStyle.green, custom_id='voice_channel:create')
    @excepter
    @dpylogger
    async def _create_voice_channel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await create_voice(interaction)


class VoiceChannelPanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(VoiceChannelConfigButton())

    @app_commands.command(name='vc操作パネル設置', description='VC関連操作パネルを設置します')
    @app_commands.guild_only()
    @excepter
    @dpylogger
    async def _put_button_edit_panel_app_command(self, interaction: discord.Interaction):
        await interaction.response.send_message('VC関連操作パネルを設置します', ephemeral=True)
        await interaction.channel.send(view=VoiceChannelConfigButton())


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoiceChannelPanelCog(bot))
