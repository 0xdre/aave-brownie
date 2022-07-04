from operator import lt
from scripts.helpers import get_account
from brownie import config, network, interface
from scripts.get_weth import get_weth
from web3 import Web3

# 0.1
AMOUNT = Web3.toWei(0.1, 'ether')


def main():
    account = get_account()
    erc20_address = config['networks'][network.show_active()]['weth_token']

    # getting wETH token
    # if network.show_active() in ['mainnet-fork']:
    get_weth()

    # getting lending pool in active network
    lending_pool = get_lending_pool()
    print(f'Lending pool addresss {lending_pool}')

    # approving erc20
    approval = approve_erc20(AMOUNT, lending_pool.address, erc20_address, account)

    # depositing weth to lending pool
    print(f"Depositing {Web3.fromWei(AMOUNT, 'ether')} wETH to lending pool")
    depositing = lending_pool.deposit(erc20_address, AMOUNT, account.address, 0, {'from': account})
    depositing.wait(1)
    print(f"{Web3.fromWei(AMOUNT, 'ether')} wETH was deposited to {lending_pool}")

    # get account data
    available_borrow_eth, total_debt_eth = get_account_data(lending_pool, account)

    print("Lets borrow")
    dai_eth_price = get_asset_price(config['networks'][network.show_active()]['dai_eth_price_feed'])
    amount_dai_to_borrow = (1 / dai_eth_price) * (available_borrow_eth * 0.1)
    print(f'We are going to borrow {amount_dai_to_borrow} DAI.')
    dai_address = config['networks'][network.show_active()]['dai_token']
    #erc20_address.approve(account.address, '')

       
    borrowing = lending_pool.borrow(
        dai_address, 
        Web3.toWei(amount_dai_to_borrow, 'ether'), 
        1, 
        0, 
        account.address, 
        {'from': account}
    )

    borrowing.wait(1)
    print(f'Succesfully borrowed {amount_dai_to_borrow} DAI !')

    get_account_data(lending_pool, account)

    repay_all(amount_dai_to_borrow, lending_pool, account)
    get_account_data(lending_pool, account)


def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, 'ether'), 
        lending_pool, 
        config['networks'][network.show_active()]['dai_token'], 
        account
    )

    repaying = lending_pool.repay(
        config['networks'][network.show_active()]['dai_token'], 
        Web3.toWei(amount, 'ether'),
        1,
        account.address,
        {'from': account}
    )
    repaying.wait(1)
    print(f'Succesfully repayed {amount} DAI')


def get_asset_price(price_feed_address):
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    dai_eth_price = dai_eth_price_feed.latestRoundData()[1]

    print(f"The DAI price is {Web3.fromWei(dai_eth_price, 'ether')} ETH")

    return float(Web3.fromWei(dai_eth_price, 'ether'))


def get_account_data(lending_pool, account):
    print(f'Getting account data')
    (
        totalCollateralETH,
        totalDebtETH,
        availableBorrowsETH,
        currentLiquidationThreshold,
        ltv,
        healthFactor
    ) = lending_pool.getUserAccountData(account.address)

    totalCollateralETH = Web3.fromWei(totalCollateralETH, 'ether')
    totalDebtETH = Web3.fromWei(totalDebtETH, 'ether')
    availableBorrowsETH = Web3.fromWei(availableBorrowsETH, 'ether')
    currentLiquidationThreshold = Web3.fromWei(currentLiquidationThreshold, 'ether')
    ltv = Web3.fromWei(ltv, 'ether')
    healthFactor = Web3.fromWei(healthFactor, 'ether')

    print(f'You have a {totalCollateralETH} wETH deposited.')
    print(f'You have {totalDebtETH} wETH borrowed.')
    print(f'You can borrow {availableBorrowsETH} wETH.')

    return(float(availableBorrowsETH), float(totalDebtETH))


def get_lending_pool():
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config['networks'][network.show_active()]['lending_pool_addresses_provider']
    )

    lending_pool_address = lending_pool_addresses_provider.getLendingPool()

    lending_pool = interface.ILendingPool(lending_pool_address)

    return lending_pool

def approve_erc20(amount, spender, erc20_address, account):
    print("Approving ERC20 token ... ")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {'from': account})
    tx.wait(1)
    print("Approved erc20")
    return tx

