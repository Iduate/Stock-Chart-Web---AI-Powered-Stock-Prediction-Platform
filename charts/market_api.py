import requests
import yfinance as yf
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import logging
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

class StockDataAPI:
    """Unified interface for different stock data APIs"""
    
    def __init__(self):
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY
        self.finnhub_key = settings.FINNHUB_API_KEY
        self.twelve_data_key = settings.TWELVE_DATA_API_KEY
        self.polygon_key = getattr(settings, 'POLYGON_API_KEY', '')
        self.iex_cloud_key = getattr(settings, 'IEX_CLOUD_API_KEY', '')
        self.base_delay = 1  # Base delay between API calls in seconds
    
    def get_stock_data(self, symbol, market_type='us_stock', interval='1day', period='1month'):
        """Get stock data from appropriate API based on market type"""
        try:
            logger.info(f"Fetching real data for {symbol} ({market_type})")
            
            # Try Alpha Vantage first for most reliable data
            if self.alpha_vantage_key and market_type in ['us_stock', 'crypto']:
                data = self._get_alpha_vantage_data(symbol)
                if data:
                    logger.info(f"Successfully fetched {len(data)} data points from Alpha Vantage for {symbol}")
                    return data
                time.sleep(self.base_delay)  # Rate limiting
            
            # Try Twelve Data as backup
            if self.twelve_data_key:
                data = self._get_twelve_data_api(symbol, interval)
                if data:
                    logger.info(f"Successfully fetched {len(data)} data points from Twelve Data for {symbol}")
                    return data
                time.sleep(self.base_delay)
            
            # Try Finnhub for real-time quotes
            if self.finnhub_key:
                data = self._get_finnhub_data(symbol)
                if data:
                    logger.info(f"Successfully fetched real-time data from Finnhub for {symbol}")
                    return data
            
            # Fallback to Yahoo Finance (free but less reliable)
            data = self._get_yahoo_finance_data(symbol, period)
            if data:
                logger.info(f"Successfully fetched {len(data)} data points from Yahoo Finance for {symbol}")
                return data
            
            logger.warning(f"No data available for {symbol} from any source")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
            return None
    
    def _get_yahoo_finance_data(self, symbol, period):
        """Get data from Yahoo Finance (free)"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return None
            
            data = []
            for date, row in hist.iterrows():
                data.append({
                    'timestamp': date,
                    'open': Decimal(str(row['Open'])),
                    'high': Decimal(str(row['High'])),
                    'low': Decimal(str(row['Low'])),
                    'close': Decimal(str(row['Close'])),
                    'volume': int(row['Volume']),
                })
            
            return data
        except Exception as e:
            logger.error(f"Yahoo Finance API error for {symbol}: {str(e)}")
            return None
    
    def _get_alpha_vantage_data(self, symbol, function='TIME_SERIES_DAILY'):
        """Get data from Alpha Vantage using your API key"""
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return None
            
        url = "https://www.alphavantage.co/query"
        params = {
            'function': function,
            'symbol': symbol,
            'apikey': self.alpha_vantage_key,
            'outputsize': 'compact'
        }
        
        try:
            logger.info(f"Calling Alpha Vantage API for {symbol}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check for API limit message
            if 'Note' in data:
                logger.warning(f"Alpha Vantage API limit reached: {data['Note']}")
                return None
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return None
            
            # Parse daily time series
            if 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                result = []
                
                for date_str, values in list(time_series.items())[:30]:  # Last 30 days
                    try:
                        result.append({
                            'timestamp': timezone.make_aware(datetime.strptime(date_str, '%Y-%m-%d')),
                            'open': Decimal(values['1. open']),
                            'high': Decimal(values['2. high']),
                            'low': Decimal(values['3. low']),
                            'close': Decimal(values['4. close']),
                            'volume': int(values['5. volume']),
                        })
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Error parsing data point for {date_str}: {e}")
                        continue
                
                return sorted(result, key=lambda x: x['timestamp'], reverse=True)
            
            logger.warning(f"No time series data found in Alpha Vantage response for {symbol}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Alpha Vantage API request error for {symbol}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Alpha Vantage API parsing error for {symbol}: {str(e)}")
            return None
    
    def _get_twelve_data_api(self, symbol, interval='1day'):
        """Get data from Twelve Data using your API key"""
        if not self.twelve_data_key:
            logger.warning("Twelve Data API key not configured")
            return None
            
        url = "https://api.twelvedata.com/time_series"
        params = {
            'symbol': symbol,
            'interval': interval,
            'apikey': self.twelve_data_key,
            'outputsize': 30  # Last 30 data points
        }
        
        try:
            logger.info(f"Calling Twelve Data API for {symbol}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'status' in data and data['status'] == 'error':
                logger.error(f"Twelve Data API error: {data.get('message', 'Unknown error')}")
                return None
            
            if 'values' in data and data['values']:
                result = []
                for item in data['values']:
                    try:
                        result.append({
                            'timestamp': datetime.strptime(item['datetime'], '%Y-%m-%d'),
                            'open': Decimal(item['open']),
                            'high': Decimal(item['high']),
                            'low': Decimal(item['low']),
                            'close': Decimal(item['close']),
                            'volume': int(item['volume']) if item['volume'] else 0,
                        })
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Error parsing Twelve Data point: {e}")
                        continue
                
                return sorted(result, key=lambda x: x['timestamp'], reverse=True)
            
            logger.warning(f"No values found in Twelve Data response for {symbol}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Twelve Data API request error for {symbol}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Twelve Data API parsing error for {symbol}: {str(e)}")
            return None
    
    def _get_korean_stock_data(self, symbol, period):
        """Get Korean stock data - may require specific Korean APIs"""
        # For Korean stocks, you might need to use specific APIs like:
        # - Korea Investment & Securities API
        # - KIS Developers API
        # For now, try Yahoo Finance with .KS suffix
        kr_symbol = f"{symbol}.KS"
        return self._get_yahoo_finance_data(kr_symbol, period)
    
    def _get_japanese_stock_data(self, symbol, period):
        """Get Japanese stock data"""
        # For Japanese stocks, try Yahoo Finance with .T suffix
        jp_symbol = f"{symbol}.T"
        return self._get_yahoo_finance_data(jp_symbol, period)
    
    def _get_international_stock_data(self, symbol, market_type, period):
        """Get international stock data based on market type"""
        market_suffixes = {
            'uk_stock': '.L',    # London Stock Exchange
            'ca_stock': '.TO',   # Toronto Stock Exchange
            'fr_stock': '.PA',   # Paris Stock Exchange
            'de_stock': '.DE',   # Deutsche Börse
            'tw_stock': '.TW',   # Taiwan Stock Exchange
            'in_stock': '.NS',   # National Stock Exchange of India
        }
        
        suffix = market_suffixes.get(market_type, '')
        intl_symbol = f"{symbol}{suffix}"
        return self._get_yahoo_finance_data(intl_symbol, period)
    
    def _get_finnhub_data(self, symbol):
        """Get real-time data from Finnhub using your API key"""
        if not self.finnhub_key:
            logger.warning("Finnhub API key not configured")
            return None
            
        # Get current quote
        quote_url = "https://finnhub.io/api/v1/quote"
        params = {
            'symbol': symbol,
            'token': self.finnhub_key
        }
        
        try:
            logger.info(f"Calling Finnhub API for {symbol}")
            response = requests.get(quote_url, params=params, timeout=30)
            response.raise_for_status()
            quote_data = response.json()
            
            if 'c' in quote_data and quote_data['c'] > 0:  # 'c' is current price
                current_time = datetime.now()
                result = [{
                    'timestamp': current_time,
                    'open': Decimal(str(quote_data.get('o', quote_data['c']))),  # 'o' is open price
                    'high': Decimal(str(quote_data.get('h', quote_data['c']))),  # 'h' is high price
                    'low': Decimal(str(quote_data.get('l', quote_data['c']))),   # 'l' is low price
                    'close': Decimal(str(quote_data['c'])),  # 'c' is current price
                    'volume': int(quote_data.get('pc', 0)),  # 'pc' is previous close
                }]
                return result
            
            logger.warning(f"No valid quote data from Finnhub for {symbol}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Finnhub API request error for {symbol}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Finnhub API parsing error for {symbol}: {str(e)}")
            return None
    
    def get_current_price(self, symbol, market_type='us_stock'):
        """Get current price for a symbol using multiple APIs"""
        try:
            logger.info(f"Getting current price for {symbol}")
            
            # Try Finnhub first for real-time data
            if self.finnhub_key:
                quote_url = "https://finnhub.io/api/v1/quote"
                params = {'symbol': symbol, 'token': self.finnhub_key}
                
                try:
                    response = requests.get(quote_url, params=params, timeout=15)
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'c' in data and data['c'] > 0:
                        price = Decimal(str(data['c']))
                        logger.info(f"Got current price ${price} for {symbol} from Finnhub")
                        return price
                except Exception as e:
                    logger.warning(f"Finnhub current price failed for {symbol}: {e}")
            
            # Try Alpha Vantage for current price
            if self.alpha_vantage_key:
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': symbol,
                    'apikey': self.alpha_vantage_key
                }
                
                try:
                    response = requests.get(url, params=params, timeout=15)
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'Global Quote' in data:
                        quote = data['Global Quote']
                        if '05. price' in quote:
                            price = Decimal(quote['05. price'])
                            logger.info(f"Got current price ${price} for {symbol} from Alpha Vantage")
                            return price
                except Exception as e:
                    logger.warning(f"Alpha Vantage current price failed for {symbol}: {e}")
            
            # Fallback to Yahoo Finance
            if market_type == 'crypto':
                return self._get_current_crypto_price(symbol)
            else:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                if info and 'currentPrice' in info:
                    price = Decimal(str(info['currentPrice']))
                    logger.info(f"Got current price ${price} for {symbol} from Yahoo Finance")
                    return price
                    
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {str(e)}")
            
        return None
    
    def _get_current_crypto_price(self, symbol):
        """Get current cryptocurrency price"""
        try:
            # Using CoinGecko API (free)
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': symbol.lower(),
                'vs_currencies': 'usd'
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if symbol.lower() in data:
                return Decimal(str(data[symbol.lower()]['usd']))
            
            return None
        except Exception as e:
            logger.error(f"Error getting crypto price for {symbol}: {str(e)}")
            return None

class MarketDataUpdater:
    """Class to handle periodic market data updates"""
    
    def __init__(self):
        self.api = StockDataAPI()
    
    def update_all_markets(self):
        """Update data for all active markets"""
        from charts.models import Market, StockData
        
        active_markets = Market.objects.filter(is_active=True)
        
        for market in active_markets:
            logger.info(f"Updating data for {market.symbol}")
            data = self.api.get_stock_data(
                market.api_symbol, 
                market.market_type, 
                period='1d'
            )
            
            if data:
                # Save the latest data point
                latest_data = data[0] if data else None
                if latest_data:
                    StockData.objects.get_or_create(
                        market=market,
                        timestamp=latest_data['timestamp'],
                        defaults={
                            'open_price': latest_data['open'],
                            'high_price': latest_data['high'],
                            'low_price': latest_data['low'],
                            'close_price': latest_data['close'],
                            'volume': latest_data['volume'],
                        }
                    )
    
    def update_predictions_accuracy(self):
        """Check and update accuracy for due predictions"""
        from charts.models import ChartPrediction
        from django.utils import timezone
        
        due_predictions = ChartPrediction.objects.filter(
            status='pending',
            target_date__lte=timezone.now()
        )
        
        for prediction in due_predictions:
            # Get current price for the market
            current_price = self.api.get_current_price(
                prediction.market.api_symbol,
                prediction.market.market_type
            )
            
            if current_price:
                prediction.actual_price = current_price
                prediction.calculate_accuracy()
                prediction.status = 'completed'
                prediction.save()
                
                # Update user's overall accuracy
                prediction.user.update_accuracy_rate(prediction.accuracy_percentage)
                
                logger.info(f"Updated prediction {prediction.id} with accuracy {prediction.accuracy_percentage}%")
