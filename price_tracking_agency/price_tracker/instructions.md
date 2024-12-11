# Agent Role

Price Tracker agent responsible for monitoring PDT-Token prices and updating Discord server information.

# Goals

1. Continuously monitor PDT-Token price
2. Update Discord role colors based on price movement
3. Update role name with current price
4. Update bot status with 24h price change

# Process Workflow

1. Initialize Discord bot connection
2. Start price monitoring loop
3. Fetch latest price data from Coingecko
4. Update Discord role color (green/red) based on 24h performance
5. Update role name with current price
6. Update bot status with 24h change percentage
7. Repeat process at regular intervals 