# import requests
# import logging
# from sqlalchemy.orm import Session
# from config import DEXSCREENER_API_URL
# from database import Token
# from datetime import datetime, timezone

# logger_dexscreener = logging.getLogger(__name__ + ".dexscreener_fetcher")

# def fetch_dexscreener_pairs(chain_id: str = "solana", query: str = None, page: int = 1):
#     try:
#         search_params = {"page": page}
#         if query:
#             search_params["q"] = f"{query} on {chain_id}"
#         else:
#             native_token_map = {"solana": "SOL", "ethereum": "WETH", "base": "ETH"}
#             native_query_token = native_token_map.get(chain_id.lower(), chain_id)
#             search_params["q"] = f"{native_query_token} on {chain_id}"

#         # FIX: Use the correct endpoint for chain-specific pairs
#         url = f"{DEXSCREENER_API_URL}/chains/{chain_id}/pairs"
#         logger_dexscreener.info(f"Fetching from Dexscreener: {url} with params {search_params}")
#         response = requests.get(url, params=search_params, timeout=15)
#         response.raise_for_status()
#         data = response.json()
#         pairs = data.get("pairs", [])
#         logger_dexscreener.info(f"Fetched {len(pairs)} potential pairs from Dexscreener for chain {chain_id} (Query: {search_params.get('q')}, Page: {page}).")
#         return pairs
#     except requests.RequestException as e:
#         logger_dexscreener.error(f"Error fetching from Dexscreener for chain {chain_id}: {e}")
#         if e.response is not None:
#             logger_dexscreener.error(f"Dexscreener API Response: Status {e.response.status_code}, Body: {e.response.text}")
#         return []
#     except Exception as e:
#         logger_dexscreener.error(f"An unexpected error occurred in dexscreener_fetcher: {e}", exc_info=True)
#         return []

# def store_tokens_from_dexscreener(db: Session, pairs_data: list):
#     if not pairs_data:
#         logger_dexscreener.info("No Dexscreener pairs data to store.")
#         return 0, 0
#     new_tokens_count = 0
#     updated_tokens_count = 0
#     processed_pair_addresses = set()
#     for pair_info in pairs_data:
#         if not pair_info or not isinstance(pair_info, dict):
#             logger_dexscreener.warning(f"Skipping invalid pair_info item: {pair_info}")
#             continue
#         pair_address = pair_info.get('pairAddress')
#         if not pair_address:
#             logger_dexscreener.warning(f"Skipping pair with missing pairAddress: {pair_info.get('baseToken', {}).get('symbol')}")
#             continue
#         if pair_address in processed_pair_addresses:
#             continue
#         processed_pair_addresses.add(pair_address)
#         base_token_info = pair_info.get('baseToken')
#         if not base_token_info or not base_token_info.get('address'):
#             logger_dexscreener.warning(f"Skipping pair {pair_address} with missing baseToken address.")
#             continue
#         try:
#             existing_token = db.query(Token).filter(Token.pair_address == pair_address).first()
#             pair_created_at_ts = pair_info.get('pairCreatedAt')
#             pair_created_at_dt = None
#             if pair_created_at_ts:
#                 try:
#                     pair_created_at_dt = datetime.fromtimestamp(pair_created_at_ts / 1000, tz=timezone.utc)
#                 except Exception as ts_e:
#                     logger_dexscreener.warning(f"Could not parse pairCreatedAt timestamp {pair_created_at_ts} for {pair_address}: {ts_e}")
#             volume = pair_info.get('volume', {})
#             price_change = pair_info.get('priceChange', {})
#             liquidity = pair_info.get('liquidity', {})
#             info_section = pair_info.get('info', {})
#             social_links_raw = {}
#             if info_section:
#                 websites = info_section.get('websites', [])
#                 socials = info_section.get('socials', [])
#                 if websites and isinstance(websites, list) and websites[0].get('url'):
#                     social_links_raw['website'] = websites[0]['url']
#                 for social_item in socials:
#                     if isinstance(social_item, dict) and social_item.get('label') and social_item.get('url'):
#                         social_links_raw[social_item['label'].lower()] = social_item['url']
#             top_level_links = pair_info.get('links')
#             if isinstance(top_level_links, dict):
#                 for k, v_link in top_level_links.items():
#                     if v_link and k not in social_links_raw:
#                         social_links_raw[k.lower()] = v_link
#             common_data = {
#                 "chain_id": pair_info.get('chainId'),
#                 "dex_id": pair_info.get('dexId'),
#                 "url": pair_info.get('url'),
#                 "base_token_address": base_token_info['address'],
#                 "base_token_name": base_token_info.get('name'),
#                 "base_token_symbol": base_token_info.get('symbol'),
#                 "quote_token_symbol": pair_info.get('quoteToken', {}).get('symbol'),
#                 "price_usd": float(pair_info['priceUsd']) if pair_info.get('priceUsd') else None,
#                 "price_native": float(pair_info['priceNative']) if pair_info.get('priceNative') else None,
#                 "volume_h24": float(volume.get('h24')) if volume.get('h24') else None,
#                 "volume_h6": float(volume.get('h6')) if volume.get('h6') else None,
#                 "volume_h1": float(volume.get('h1')) if volume.get('h1') else None,
#                 "price_change_h24": float(price_change.get('h24')) if price_change.get('h24') else None,
#                 "price_change_h6": float(price_change.get('h6')) if price_change.get('h6') else None,
#                 "price_change_h1": float(price_change.get('h1')) if price_change.get('h1') else None,
#                 "liquidity_usd": float(liquidity.get('usd')) if liquidity.get('usd') else (float(liquidity.get('base')) * float(pair_info['priceUsd']) if liquidity.get('base') and pair_info.get('priceUsd') else None),
#                 "fdv": float(pair_info.get('fdv')) if pair_info.get('fdv') else None,
#                 "market_cap_usd": float(pair_info.get('marketCap')) if pair_info.get('marketCap') else None,
#                 "holders": int(pair_info.get('holders')) if pair_info.get('holders') else None,
#                 "pair_created_at": pair_created_at_dt,
#                 "social_links_raw": social_links_raw if social_links_raw else None,
#                 "last_dexscreener_fetch_at": datetime.now(timezone.utc)
#             }
#             if existing_token:
#                 for key, value in common_data.items():
#                     setattr(existing_token, key, value)
#                 updated_tokens_count += 1
#             else:
#                 token_data = Token(
#                     pair_address=pair_address,
#                     **common_data,
#                     first_seen_at=datetime.now(timezone.utc)
#                 )
#                 db.add(token_data)
#                 new_tokens_count += 1
#         except KeyError as e_key:
#             logger_dexscreener.error(f"Missing key {e_key} in Dexscreener pair data for {pair_address}: {pair_info}")
#         except ValueError as e_val:
#             logger_dexscreener.error(f"Data type error for {pair_address} (e.g. converting string to float): {e_val}. Data: {pair_info}")
#         except Exception as e_gen:
#             logger_dexscreener.error(f"Error processing/storing Dexscreener pair {pair_address}: {e_gen}", exc_info=True)
#             db.rollback()
#             continue
#     try:
#         db.commit()
#         logger_dexscreener.info(f"Dexscreener sync: Stored {new_tokens_count} new tokens, updated {updated_tokens_count} tokens.")
#     except Exception as e_commit:
#         logger_dexscreener.error(f"Database commit error after Dexscreener sync: {e_commit}", exc_info=True)
#         db.rollback()
#     return new_tokens_count, updated_tokens_count

import requests
import logging
from sqlalchemy.orm import Session
from config import DEXSCREENER_API_URL
from database import Token
from datetime import datetime, timezone

logger_dexscreener = logging.getLogger(__name__ + ".dexscreener_fetcher")

def fetch_dexscreener_pairs(chain_id: str = "solana", query: str = None, page: int = 1):
    try:
        # Use the correct DexScreener API endpoint
        # For getting trending/new pairs, we'll use the search endpoint
        if query:
            # Search for specific tokens
            url = f"{DEXSCREENER_API_URL}/search"
            params = {"q": query}
        else:
            # Get latest pairs for a specific chain
            url = f"https://api.dexscreener.com/latest/dex/pairs/{chain_id}"
            params = {}
        
        logger_dexscreener.info(f"Fetching from Dexscreener: {url} with params {params}")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Handle different response structures
        if "pairs" in data:
            pairs = data["pairs"]
        elif "pair" in data:
            pairs = [data["pair"]]  # Single pair response
        elif isinstance(data, list):
            pairs = data  # Direct list of pairs
        else:
            pairs = []
        
        logger_dexscreener.info(f"Fetched {len(pairs)} potential pairs from Dexscreener for chain {chain_id}")
        return pairs
        
    except requests.RequestException as e:
        logger_dexscreener.error(f"Error fetching from Dexscreener for chain {chain_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger_dexscreener.error(f"Dexscreener API Response: Status {e.response.status_code}, Body: {e.response.text}")
        return []
    except Exception as e:
        logger_dexscreener.error(f"An unexpected error occurred in dexscreener_fetcher: {e}", exc_info=True)
        return []

def fetch_trending_pairs(chain_id: str = "solana", limit: int = 50):
    """Fetch trending pairs using DexScreener's token profiles endpoint"""
    try:
        # Use the token profiles endpoint which gives us trending tokens
        url = "https://api.dexscreener.com/token-profiles/latest/v1"
        
        logger_dexscreener.info(f"Fetching trending pairs from: {url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Filter for the specific chain and get pairs
        pairs = []
        if isinstance(data, list):
            for item in data[:limit]:
                if item.get('chainId') == chain_id:
                    # Get the actual pair data for this token
                    token_address = item.get('tokenAddress')
                    if token_address:
                        pair_data = fetch_token_pairs(token_address, chain_id)
                        if pair_data:
                            pairs.extend(pair_data)
        
        logger_dexscreener.info(f"Fetched {len(pairs)} trending pairs for chain {chain_id}")
        return pairs
        
    except Exception as e:
        logger_dexscreener.error(f"Error fetching trending pairs: {e}")
        return []

def fetch_token_pairs(token_address: str, chain_id: str = "solana"):
    """Fetch pairs for a specific token address"""
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        pairs = data.get("pairs", [])
        # Filter pairs by chain if specified
        if chain_id:
            pairs = [pair for pair in pairs if pair.get('chainId') == chain_id]
        
        return pairs
        
    except Exception as e:
        logger_dexscreener.error(f"Error fetching pairs for token {token_address}: {e}")
        return []

def store_tokens_from_dexscreener(db: Session, pairs_data: list):
    if not pairs_data:
        logger_dexscreener.info("No Dexscreener pairs data to store.")
        return 0, 0
    
    new_tokens_count = 0
    updated_tokens_count = 0
    processed_pair_addresses = set()
    
    for pair_info in pairs_data:
        if not pair_info or not isinstance(pair_info, dict):
            logger_dexscreener.warning(f"Skipping invalid pair_info item: {pair_info}")
            continue
            
        pair_address = pair_info.get('pairAddress')
        if not pair_address:
            logger_dexscreener.warning(f"Skipping pair with missing pairAddress: {pair_info.get('baseToken', {}).get('symbol')}")
            continue
            
        if pair_address in processed_pair_addresses:
            continue
        processed_pair_addresses.add(pair_address)
        
        base_token_info = pair_info.get('baseToken')
        if not base_token_info or not base_token_info.get('address'):
            logger_dexscreener.warning(f"Skipping pair {pair_address} with missing baseToken address.")
            continue
        
        try:
            existing_token = db.query(Token).filter(Token.pair_address == pair_address).first()
            
            # Parse pair creation timestamp
            pair_created_at_ts = pair_info.get('pairCreatedAt')
            pair_created_at_dt = None
            if pair_created_at_ts:
                try:
                    pair_created_at_dt = datetime.fromtimestamp(pair_created_at_ts / 1000, tz=timezone.utc)
                except Exception as ts_e:
                    logger_dexscreener.warning(f"Could not parse pairCreatedAt timestamp {pair_created_at_ts} for {pair_address}: {ts_e}")
            
            # Extract volume data
            volume = pair_info.get('volume', {})
            price_change = pair_info.get('priceChange', {})
            liquidity = pair_info.get('liquidity', {})
            
            # Extract social links
            info_section = pair_info.get('info', {})
            social_links_raw = {}
            if info_section:
                websites = info_section.get('websites', [])
                socials = info_section.get('socials', [])
                
                if websites and isinstance(websites, list) and websites[0].get('url'):
                    social_links_raw['website'] = websites[0]['url']
                
                for social_item in socials:
                    if isinstance(social_item, dict) and social_item.get('label') and social_item.get('url'):
                        social_links_raw[social_item['label'].lower()] = social_item['url']
            
            # Check for top-level links
            top_level_links = pair_info.get('links')
            if isinstance(top_level_links, dict):
                for k, v_link in top_level_links.items():
                    if v_link and k not in social_links_raw:
                        social_links_raw[k.lower()] = v_link
            
            common_data = {
                "chain_id": pair_info.get('chainId'),
                "dex_id": pair_info.get('dexId'),
                "url": pair_info.get('url'),
                "base_token_address": base_token_info['address'],
                "base_token_name": base_token_info.get('name'),
                "base_token_symbol": base_token_info.get('symbol'),
                "quote_token_symbol": pair_info.get('quoteToken', {}).get('symbol'),
                "price_usd": float(pair_info['priceUsd']) if pair_info.get('priceUsd') else None,
                "price_native": float(pair_info['priceNative']) if pair_info.get('priceNative') else None,
                "volume_h24": float(volume.get('h24')) if volume.get('h24') else None,
                "volume_h6": float(volume.get('h6')) if volume.get('h6') else None,
                "volume_h1": float(volume.get('h1')) if volume.get('h1') else None,
                "price_change_h24": float(price_change.get('h24')) if price_change.get('h24') else None,
                "price_change_h6": float(price_change.get('h6')) if price_change.get('h6') else None,
                "price_change_h1": float(price_change.get('h1')) if price_change.get('h1') else None,
                "liquidity_usd": float(liquidity.get('usd')) if liquidity.get('usd') else (float(liquidity.get('base')) * float(pair_info['priceUsd']) if liquidity.get('base') and pair_info.get('priceUsd') else None),
                "fdv": float(pair_info.get('fdv')) if pair_info.get('fdv') else None,
                "market_cap_usd": float(pair_info.get('marketCap')) if pair_info.get('marketCap') else None,
                "holders": int(pair_info.get('holders')) if pair_info.get('holders') else None,
                "pair_created_at": pair_created_at_dt,
                "social_links_raw": social_links_raw if social_links_raw else None,
                "last_dexscreener_fetch_at": datetime.now(timezone.utc)
            }
            
            if existing_token:
                for key, value in common_data.items():
                    setattr(existing_token, key, value)
                updated_tokens_count += 1
            else:
                token_data = Token(
                    pair_address=pair_address,
                    **common_data,
                    first_seen_at=datetime.now(timezone.utc)
                )
                db.add(token_data)
                new_tokens_count += 1
                
        except KeyError as e_key:
            logger_dexscreener.error(f"Missing key {e_key} in Dexscreener pair data for {pair_address}: {pair_info}")
        except ValueError as e_val:
            logger_dexscreener.error(f"Data type error for {pair_address} (e.g. converting string to float): {e_val}. Data: {pair_info}")
        except Exception as e_gen:
            logger_dexscreener.error(f"Error processing/storing Dexscreener pair {pair_address}: {e_gen}", exc_info=True)
            db.rollback()
            continue
    
    try:
        db.commit()
        logger_dexscreener.info(f"Dexscreener sync: Stored {new_tokens_count} new tokens, updated {updated_tokens_count} tokens.")
    except Exception as e_commit:
        logger_dexscreener.error(f"Database commit error after Dexscreener sync: {e_commit}", exc_info=True)
        db.rollback()
    
    return new_tokens_count, updated_tokens_count
