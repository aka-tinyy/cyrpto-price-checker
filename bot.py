import discord
import logging
import aiohttp
from discord.ui import Button, View

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = discord.Bot()

@bot.event
async def on_interaction(interaction):
    await bot.process_application_commands(interaction)
    if "refresh" in str(interaction.data):
        transaction_id = interaction.message.embeds[0].description.split(" ")[2]
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.blockcypher.com/v1/btc/main/txs/{transaction_id}") as r:
                data = await r.json()
                if r.status == 200:
                    total = 0
                    if data['confirmations'] > 0:
                        for output in data['outputs']:
                            if output['script_type'] == 'pay-to-witness-script-hash' or output['script_type'] == 'pay-to-script-hash':
                                recipient = output['addresses'][0]
                                total = output['value']
                        sender = data['inputs'][0]['addresses'][0]
                        if total == 0 or total == None:
                            value_btc = "Unknown"
                        else:
                            value_btc = total / 100000000
                        embed = discord.Embed(title='Transaction Status', color=0x00ff00)
                        embed.add_field(name='Transaction ID', value=transaction_id, inline=False)
                        embed.add_field(name='Value', value=f'{value_btc} BTC', inline=False)
                        embed.add_field(name='Timestamp', value=data['received'], inline=False)
                        embed.add_field(name='Sender', value=sender, inline=False)
                        embed.add_field(name='Recipient', value=recipient, inline=False)
                        embed.add_field(name='Confirmations', value=data['confirmations'], inline=False)
                        await interaction.response.edit_message(embed=embed, view=None)                   
                    else:
                        await interaction.response.send_message("Transaction is unconfirmed still", ephemeral=True)
        



async def get_usd_price(btc):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.coindesk.com/v1/bpi/currentprice.json") as r:
            data = await r.json(content_type=None)
            usd = data['bpi']['USD']['rate_float']
            #round to the thousandth
            return btc * usd


@bot.slash_command()
async def check_status(ctx, transaction_id: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.blockcypher.com/v1/btc/main/txs/{transaction_id}") as r:
            data = await r.json()
            if r.status == 200:
                if data['confirmations'] > 0:
                    # Get the sender and recipient addresses
                    for output in data['outputs']:
                        if output['script_type'] == 'pay-to-witness-script-hash' or output['script_type'] == 'pay-to-script-hash':
                            recipient = output['addresses'][0]
                            total = output['value']
                    sender = data['inputs'][0]['addresses'][0]
                    value_btc = total / 100000000
                    # Create an embed with the transaction information
                    embed = discord.Embed(title='Transaction Status', color=0x00ff00)
                    embed.add_field(name='Transaction ID', value=transaction_id, inline=False)
                    embed.add_field(name='Value', value=f'{value_btc} BTC', inline=False)
                    embed.add_field(name='Value in USD', value=f"${round(await get_usd_price(value_btc), 3)}", inline=False)
                    embed.add_field(name='Timestamp', value=data['received'], inline=False)
                    embed.add_field(name='Sender', value=sender, inline=False)
                    embed.add_field(name='Recipient', value=recipient, inline=False)
                    embed.add_field(name='Confirmations', value=data['confirmations'], inline=False)
                    await ctx.respond(embed=embed)
                else:
                    embed = discord.Embed(title="Transaction is unconfirmed", description=f"Transaction ID: {transaction_id}", color=0xFF0000)
                    embed.add_field(name="Transaction value", value=f"Unknown", inline=False)
                    view = discord.ui.View()
                    refresh = Button(label="Refresh", custom_id="refresh", style=discord.ButtonStyle.green)
                    view.add_item(refresh)
                    await ctx.respond(embed=embed, view=view)
            else:
                await ctx.respond("Transaction not found", ephemeral=True)
    



@bot.event
async def on_read():
    logger.info("Client logged in as {0.user}".format(bot))
    logger.info(bot.user.name)
    logger.info(bot.user.id)
    logger.info("------")


bot.run("")
