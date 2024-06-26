import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from datetime import timedelta
from daug.utils.dpyexcept import excepter
from daug.utils.dpylog import dpylogger
from typing import Literal
from typing import TypeAlias

TYPE_LITERAL_TARGET: TypeAlias = Literal['自分', '全員', 'BOT']
TYPE_LITERAL_OPTION: TypeAlias = Literal['なし', 'リアクション付きを除く']


def _is_target(message: discord.Message, interaction: discord.Interaction, target: str, option: str) -> bool:
    if option == 'リアクション付きを除く' and message.reactions:
        return False
    if target == 'BOT' and not message.author.bot:
        return False
    if target == '自分' and message.author != interaction.user:
        return False
    return True


async def _send_start_message(interaction: discord.Interaction, target: TYPE_LITERAL_TARGET, option: TYPE_LITERAL_OPTION):
    if target == '全員':
        await interaction.response.send_message('このチャンネル内の発言を一括削除します', ephemeral=True)
    elif target == 'BOT':
        await interaction.response.send_message('このチャンネル内のBOTの発言を一括削除します', ephemeral=True)
    else:
        await interaction.response.send_message('このチャンネル内のあなたの発言を一括削除します', ephemeral=True)


async def _send_complete_message(interaction: discord.Interaction, target: TYPE_LITERAL_TARGET, option: TYPE_LITERAL_OPTION):
    if target == '全員':
        await interaction.followup.send('このチャンネル内の発言を一括削除しました', ephemeral=True)
    elif target == 'BOT':
        await interaction.followup.send('このチャンネル内のBOTの発言を一括削除しました', ephemeral=True)
    else:
        await interaction.followup.send('このチャンネル内のあなたの発言を一括削除しました', ephemeral=True)


async def _purge(interaction: discord.Interaction, target: TYPE_LITERAL_TARGET, option: TYPE_LITERAL_OPTION):
    def check(message: discord.Message) -> bool:
        return _is_target(message, interaction, target, option)
    await interaction.channel.purge(limit=None, check=check)


async def _delete_messages(interaction: discord.Interaction, target: TYPE_LITERAL_TARGET, option: TYPE_LITERAL_OPTION):
    fourteen_days_ago = datetime.now() - timedelta(days=14)
    logs = [log async for log in interaction.channel.history(limit=None, after=fourteen_days_ago) if _is_target(log, interaction, target, option)]
    if len(logs) > 0:
        await interaction.channel.delete_messages(logs)


class DeleteLogCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name='ログ削除')
    @app_commands.describe(target='削除対象のメッセージ投稿者', option='追加条件')
    @app_commands.rename(target='削除対象', option='追加条件')
    @excepter
    @dpylogger
    async def delete_logs(self, interaction: discord.Interaction, target: TYPE_LITERAL_TARGET = '自分', option: TYPE_LITERAL_OPTION = 'なし'):
        """チャンネル内のあなたの発言を一括削除します"""
        if interaction.channel.type is discord.ChannelType.private:
            if target != 'BOT':
                await interaction.response.send_message('DMで削除できるのはBOTの発言のみです', ephemeral=True)
                return
        elif target == '全員' and not interaction.user.resolved_permissions.manage_channels:
            await interaction.response.send_message('全員分の発言を削除するにはチャンネル管理権限が必要です', ephemeral=True)
            return
        await _send_start_message(interaction, target, option)
        if hasattr(interaction.channel, 'purge'):
            try:
                await _purge(interaction, target, option)
            except discord.errors.Forbidden:
                await interaction.followup.send('メッセージを削除する権限がありません', ephemeral=True)
                return
            except discord.errors.HTTPException:
                pass
        if hasattr(interaction.channel, 'delete_messages'):
            try:
                await _delete_messages(interaction, target, option)
            except discord.errors.Forbidden:
                await interaction.followup.send('メッセージを削除する権限がありません', ephemeral=True)
                return
            except discord.errors.NotFound:
                pass
            except discord.errors.ClientException:
                pass
            except discord.errors.HTTPException:
                pass
        async for log in interaction.channel.history(limit=None):
            if not _is_target(log, interaction, target, option):
                continue
            try:
                await log.delete()
            except discord.errors.NotFound:
                pass
            except discord.errors.Forbidden:
                await interaction.followup.send('メッセージを削除する権限がありません', ephemeral=True)
                return
            except discord.errors.HTTPException:
                await interaction.followup.send(f'1件のメッセージの削除に失敗しました {log.jump_url}', ephemeral=True)
        await _send_complete_message(interaction, target, option)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DeleteLogCog(bot))
