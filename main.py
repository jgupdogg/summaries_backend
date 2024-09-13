from articles import Article
from initialize import *
from sites.site_agg import site_parsers

def main(test_mode=True):

    try:
        for site_key, site_info in site_parsers.items():
            print(f"Processing {site_info['name']}...")

            # Load the site soup
            soup = scraper.make_request(site_info['link'])

            # Get the links
            links = site_info['links_parse'](soup)

            if not links:
                print(f"No links found for {site_info['name']}")
                continue

            # In test mode, only process the first link
            if test_mode:
                links = links[:1]

            for link_data in links:
                # try:
                    # Get soup for the article
                    article_soup = scraper.make_request(link_data['link'])

                    # Parse the article
                    article_data = site_info['article_parse'](article_soup)

                    # Merge link_data and article_data
                    full_article_data = {**link_data, **article_data, 'symbol': site_key}

                    # Store the result as an Article object
                    article = Article.from_dict(full_article_data)

                    # Generate all representations
                    article.generate_all_representations()
       
                    # Upsert to Pinecone
                    article.upsert_to_pinecone()

                # except Exception as e:
                #     print(f"Error processing article from {site_info['name']}: {str(e)}")

            if test_mode:
                print(f"Test mode: Processed one article from {site_info['name']}")
                print("\n" + "="*50 + "\n")

    finally:
        # Ensure the driver is closed even if an exception occurs
        scraper.close_driver()

if __name__ == "__main__":
    main(test_mode=True)