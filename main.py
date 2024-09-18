from articles import Article
from sites.site_agg import site_parsers
from bs4 import BeautifulSoup  # Assuming you're using BeautifulSoup for parsing
from scraper_api import make_scraper_request
import logging


def main(test_mode=True):
    """
    Main function to scrape and process articles from various sites.

    Args:
        test_mode (bool): If True, only the first article per site is processed.
    """
    try:
        for site_key, site_info in site_parsers.items():
            logging.info(f"Processing {site_info['name']}...")

            try:
                # Load the site HTML content via the scraper service
                site_html = make_scraper_request(site_info['link'], use_proxy=True)
                soup = BeautifulSoup(site_html, 'html.parser')

                # Extract article links using the site's specific parser
                links = site_info['links_parse'](soup)

                if not links:
                    logging.warning(f"No links found for {site_info['name']}.")
                    continue

                # In test mode, only process the first link
                if test_mode:
                    links = links[:1]

                for link_data in links:
                    try:
                        # Scrape the article page
                        article_html = make_scraper_request(link_data['link'], use_proxy=True)
                        article_soup = BeautifulSoup(article_html, 'html.parser')

                        # Parse the article content using the site's specific parser
                        article_data = site_info['article_parse'](article_soup)

                        # Merge link_data and article_data, and add the site symbol
                        full_article_data = {
                            **link_data,
                            **article_data,
                            'symbol': site_key
                        }

                        # Create an Article object from the merged data
                        article = Article.from_dict(full_article_data)

                        # Generate all necessary representations for the article
                        article.generate_all_representations()

                        # Upsert the article data to Pinecone
                        article.upsert_to_pinecone()

                    except Exception as e:
                        logging.error(f"Error processing article from {site_info['name']} ({link_data['link']}): {str(e)}")

                if test_mode:
                    logging.info(f"Test mode: Processed one article from {site_info['name']}")

            except Exception as e:
                logging.error(f"Error processing site {site_info['name']} ({site_info['link']}): {str(e)}")

    finally:
        # If there's any cleanup needed, do it here
        # Since scraping is handled by the remote service, there's no driver to close
        logging.info("Scraping process completed.")

if __name__ == "__main__":
    main(test_mode=True)
