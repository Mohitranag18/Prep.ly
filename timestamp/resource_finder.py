# Handles finding relevant resource links using Gemini site guessing + DDG scraping

import streamlit as st
import requests
import json
import html
from urllib.parse import quote, urlencode
import string
import time
from bs4 import BeautifulSoup
import google.generativeai as genai
import random

try:
    from config import GEMINI_API_KEYS
except ImportError:
    st.error("Error: Could not find config.py or GEMINI_API_KEYS within it.")
    GEMINI_API_KEYS = []

# --- Gemini Site Guessing Function ---

@st.cache_data(ttl=3600) # Cache for 1 hour
def guess_sites_gemini(keywords, num_sites=3):
    """Uses Gemini API to guess relevant website domains based on keywords."""
    if not GEMINI_API_KEYS:
        st.error("No Gemini API keys configured.")
        return []
    if not keywords:
        return []

    topic = " ".join(keywords)
    st.info(f"Asking Gemini to suggest relevant sites for topic: '{topic}'")

    generation_config = {"temperature": 0.5}
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    prompt = f"""Based on the following keywords extracted from a YouTube video title and transcript (up to a certain point), suggest {num_sites} website domains that are **strictly for practicing questions** related to the topic. Focus on sites known for providing question banks, quizzes, coding challenges, or practice problems. Avoid general information sites like Wikipedia unless they have dedicated practice sections.

Keywords: "{topic}"

Respond ONLY with a valid JSON list of strings, where each string is just the domain name known for practice questions (e.g., 'leetcode.com', 'hackerrank.com', 'geeksforgeeks.org/practice', 'projecteuler.net', 'codewars.com').
Example format:
["leetcode.com", "geeksforgeeks.org", "hackerrank.com"]
"""

    guessed_sites = []
    for i, key in enumerate(GEMINI_API_KEYS):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(model_name="gemini-2.0-flash",
                                          generation_config=generation_config,
                                          safety_settings=safety_settings)
            response = model.generate_content(prompt)
            cleaned_response = response.text.strip().lstrip('```json').rstrip('```').strip()
            
            parsed_list = json.loads(cleaned_response)
            if isinstance(parsed_list, list) and all(isinstance(s, str) for s in parsed_list):
                 valid_domains = [site.lower().strip() for site in parsed_list if '.' in site and ' ' not in site]
                 if valid_domains:
                     st.success(f"Gemini suggested sites: {', '.join(valid_domains)}")
                     return valid_domains
                 else:
                      st.warning("Gemini response was a list, but contained no valid-looking domains.")
                      return [] # Return empty, don't retry for this type of error
            else:
                st.warning(f"Gemini site suggestion response was not a valid JSON list of strings: {cleaned_response}")
                return [] # Return empty, don't retry

        except json.JSONDecodeError as json_err:
            st.warning(f"Gemini site suggestion response was not valid JSON: {json_err}. Response: '{response.text}'")
            return [] # Don't retry
        except Exception as e:
            st.warning(f"Gemini API call failed for site guessing (key #{i+1}): {e}")
            if i == len(GEMINI_API_KEYS) - 1:
                st.error("All Gemini API keys failed for site guessing.")
                return []
            # Otherwise, loop continues

    return []

# --- DuckDuckGo Scraping Function ---

@st.cache_data(ttl=3600) # Cache for 1 hour
def scrape_duckduckgo_links(keywords, site_filter=None, num_results=5):
    """Attempts to scrape DuckDuckGo search results, optionally filtering by site."""
    if not keywords:
        return []

    query_parts = keywords[:] # Copy keywords
    if site_filter:
        query_parts.insert(0, f"site:{site_filter}") # Prepend site filter

    query = " ".join(query_parts)
    search_info = f"'{query}'" + (f" on site '{site_filter}'" if site_filter else "")
    params = {'q': query}
    search_url = f"https://html.duckduckgo.com/html/?{urlencode(params)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    links_found = []
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        results = soup.find_all('div', class_='result')

        for result in results[:num_results]: # Limit results per site search
            link_tag = result.find('a', class_='result__a')
            title_tag = result.find('h2', class_='result__title')

            if link_tag and title_tag:
                link = link_tag.get('href')
                title = title_tag.get_text(strip=True)

                if link and title and link.startswith('http') and 'duckduckgo.com' not in link:
                    links_found.append({
                        "source": site_filter if site_filter else "DuckDuckGo",
                        "title": title,
                        "link": link
                    })


    except requests.exceptions.RequestException as e:
        st.warning(f"Web search request failed for {search_info}: {e}")
    except Exception as e:
        st.warning(f"Error processing web search for {search_info}: {e}")

    return links_found

def get_resources(keywords, target_num_resources=5):
    """
    Gets resource links: Guesses sites with Gemini, then scrapes DDG for each site.
    """
    if not keywords:
        return []

    translator = str.maketrans('', '', string.punctuation)
    cleaned_keywords = [k.translate(translator).strip() for k in keywords if k]
    cleaned_keywords = [k for k in cleaned_keywords if k]

    if not cleaned_keywords:
         return []

    # 1. Guess relevant sites using Gemini
    guessed_sites = guess_sites_gemini(cleaned_keywords, num_sites=5)

    all_resources = []
    processed_links = set()
    max_results_per_site = max(1, target_num_resources // len(guessed_sites)) if guessed_sites else target_num_resources

    # 2. Scrape DDG for each guessed site
    if guessed_sites:
        st.info(f"--- Searching suggested sites for resources ---")
        for site in guessed_sites:
            try:
                # Limit results per site to distribute findings
                site_resources = scrape_duckduckgo_links(
                    cleaned_keywords,
                    site_filter=site,
                    num_results=max_results_per_site
                )
                for res in site_resources:
                     if res['link'] not in processed_links:
                         all_resources.append(res)
                         processed_links.add(res['link'])
                         # Stop if we hit the overall target early
                         if len(all_resources) >= target_num_resources:
                             break
            except Exception as e:
                st.warning(f"Error scraping site {site}: {e}")
            # Stop searching sites if we hit the overall target
            if len(all_resources) >= target_num_resources:
                break
    else:
        st.info("Gemini did not suggest specific sites. Performing general web search...")

    # 3. If no sites guessed OR not enough results, do a general DDG scrape
    resources_still_needed = target_num_resources - len(all_resources)
    if resources_still_needed > 0 and not guessed_sites: # Only do general scrape if Gemini failed
         try:
             general_resources = scrape_duckduckgo_links(
                 cleaned_keywords,
                 site_filter=None, # No site filter
                 num_results=resources_still_needed
             )
             for res in general_resources:
                  if res['link'] not in processed_links:
                      all_resources.append(res)
                      processed_links.add(res['link'])
         except Exception as e:
             st.warning(f"Error during general web scrape: {e}")

    # 4. Final Check
    if not all_resources:
        st.warning(f"Could not find any resources for keywords: {cleaned_keywords}.")

    return all_resources[:target_num_resources] # Return up to the target number
