import csv
import io

def result_to_csv(result: dict, input: dict) -> str:
        output = io.StringIO()
        csv_writer = csv.writer(output, delimiter=',')
        csv_writer.writerow(['Calculation Input'])
        csv_writer.writerow([''])
        if input.get('portfolio', None) is not None:
            csv_writer.writerow(['Portfolio', input['portfolio']])
        if input.get('funds', None) is not None:
            csv_writer.writerow(['Account Cash Balance', input['funds']])
        if input.get('symbols', None) is not None:
            csv_writer.writerow(['Symbol', input['symbols']])
        if input.get('cash', None) is not None:
            csv_writer.writerow(['Investment (in cash)', input['cash']])
        if input.get('stockBuyCount', None) is not None:
            csv_writer.writerow(['Stocks Bought', input['stockBuyCount']])
        if input.get('stockPrice', None) is not None:
            csv_writer.writerow(['Custom Stock Price', input['stockPrice']])
        if input.get('commission', None) is not None:
            csv_writer.writerow(['Commission', input['commission']])
        if input.get('drip', None) is not None:
            csv_writer.writerow(['Drip', 'No' if input['drip'] == '0' else 'Yes'])
        if input.get('frequency', None) is not None:
            csv_writer.writerow(['Dividend Frequency', input['frequency']])
        if input.get('years', None) is not None:
            csv_writer.writerow(['Years', input['years']])
        csv_writer.writerow([''])
        csv_writer.writerow(['Company Name', result['stock_data'].get('name', ''), 'Beta (5Y Monthly)', result['stock_data'].get('beta', '')]) 
        csv_writer.writerow(['Symbol', result['stock_data'].get('symbol', ''), 'PE Ratio (TTM)', result['stock_data'].get('pe_ratio', '')]) 
        csv_writer.writerow(['Exchange', result['stock_data'].get('exchange', ''), '50-Day Moving Average', result['stock_data'].get('fifty_day_average', '')])
        csv_writer.writerow(['Share Price', result['stock_data'].get('price', ''), '200-Day Moving Average', result['stock_data'].get('two_hundred_day_average', '')])
        csv_writer.writerow(['Dividend Frequency', 'N/A', 'Ex-Dividend Date', result['stock_data']['exdividend_date']])
        csv_writer.writerow(['Dividend Per Share', result['stock_data'].get('dividend', ''), 'Payment Date', result['stock_data'].get('payment_date', '')])
        csv_writer.writerow(['Dividend Yield', result['stock_data'].get('dividend_yield', ''), '52 Week Range', result['stock_data'].get('fifty_two_week_range', '')])
        csv_writer.writerow(['Dividend Growth Rate', 'N/A', 'Payout Ratio', result['stock_data'].get('payout_ratio', '')])
        csv_writer.writerow([])
        calc_result = result['calculation_result']
        for y, qs in calc_result.items():
            for q in qs.keys():
                csv_writer.writerow([f'Year {y} Quarter {q}'])
                if y == 1 and q == 1:
                    csv_writer.writerow(['Book Value (Initial Investment Cash Q1)', qs[1]['investment']])            
                    csv_writer.writerow(['Cash Balance after Investment', qs[1]['cash_balance_after_invest']])            
                    csv_writer.writerow(['Initial Share Brought', qs[1]['initial_share_brought']])            
                    csv_writer.writerow(['Average Cost', qs[1]['initial_share_brought']])
                    continue
                elif y > 0 and q < len(qs.keys()):
                    csv_writer.writerow(['', 'W/O Drip', 'With Drip'])
                    csv_writer.writerow([f'No. of Drip Shares Received in Q{q}', '', qs[q]['drip_received']])
                    csv_writer.writerow([f'Total No. of Drip Shares end of Q{q}', qs[q]['total_drip'][0], qs[q]['total_drip'][1] ])
                    csv_writer.writerow(['Dividend Cash Received from Intial Shares /Cash Received Aftr Drip', qs[q]['dividend_cash_received'][0], qs[q]['dividend_cash_received'][1] ])
                    csv_writer.writerow([f'Cash received from Drip Shares in Year {y} - Q{q}', '', qs[q]['cash_received_drip']])
                if q == len(qs.keys()):
                    csv_writer.writerow(['Total Cash Received from Drip Shares / Total Cash Received after drip', qs[q]['total_cash_received'][0], qs[q]['total_cash_received'][1]])
                    csv_writer.writerow(['Portfolio Unrealized Gain/Loss', qs[q]['portfolio_gain_loss'][0], qs[q]['portfolio_gain_loss'][1]])
                csv_writer.writerow([f'Portfolio Cash W/O DRIP and With Drip Q{q} end of Year {y} - Q1', qs[q]['portfolio_cash'][0], qs[q]['portfolio_cash'][1]])                    

        return output.getvalue()