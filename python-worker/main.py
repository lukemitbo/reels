import os
import logging
import tempfile
from twitter import get_tweets
from serper import get_news_title_and_snippet, get_search_result_links
from google_sheets import get_all_queries, add_to_sheet
from generate_script import generate_topic, generate_script
from extract_text import fetch_and_extract
from audio import tts
from video import assemble_video, get_run_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting pipeline...")
    
    # Step 1: Scrape tweets
    logger.info("Scraping tweets...")
    tweets = get_tweets("ai news")
    logger.info(f"Found {len(tweets)} tweets")
    
    # Step 2: Search "ml research" past week
    logger.info("Searching ML research news...")
    ml_research = get_news_title_and_snippet("ml research", "w")
    logger.info(f"Found {len(ml_research)} ML research articles")
    
    # Step 3: Search "ai tech" past day
    logger.info("Searching AI tech news...")
    ai_tech = get_news_title_and_snippet("ai tech", "d")
    logger.info(f"Found {len(ai_tech)} AI tech articles")
    
    if len(ml_research) == 0 and len(ai_tech) == 0 and len(tweets) == 0:
        logger.error("No news or tweets found")
        return
    
    # Step 4: Gather past queries
    logger.info("Fetching previous queries from Google Sheets...")
    previous_queries = get_all_queries()
    logger.info(f"Found {len(previous_queries)} previous queries")
    
    # Step 5: Combine news sources into a single list of topics
    recent_news_topics = []
    recent_news_topics.extend(tweets)
    recent_news_topics.extend([f"{title}: {snippet}" for title, snippet in ml_research])
    recent_news_topics.extend([f"{title}: {snippet}" for title, snippet in ai_tech])
    logger.info(f"Combined {len(recent_news_topics)} news topics")
    
    # Step 6: Generate topic
    logger.info("Generating topic...")
    query = generate_topic(previous_queries, recent_news_topics)
    logger.info(f"Generated topic query: {query}")
    
    # Step 7: Save generated topic to Google Sheets
    logger.info("Saving topic to Google Sheets...")
    add_to_sheet(query)
    logger.info("Topic saved to Google Sheets")
    
    # Step 8: Search web for the topic
    logger.info(f"Searching web for: {query}")
    search_links = get_search_result_links(query, "w")
    logger.info(f"Found {len(search_links)} search result links")
    if len(search_links) == 0:
        logger.error("No search result links found")
        return
    
    # Step 9: Extract content from URLs
    logger.info("Extracting content from URLs...")
    extracted_texts = []
    for url in search_links[:6]:  # Limit to 10 URLs
        logger.info(f"Extracting from: {url}")
        text = fetch_and_extract(url)
        if text:
            extracted_texts.append(text)
            logger.info(f"Extracted {len(text)} characters from {url}")
    
    # Step 10: Combine extracted text into a single context string
    context_text = "\n\n".join(extracted_texts)
    logger.info(f"Combined context text length: {len(context_text)} characters")
    
    # Step 11: Generate script
    logger.info("Generating script...")
    title, script = generate_script(context_text)
    logger.info(f"Generated script with title: {title} and {len(script)} dialogue lines")
    
    # Step 12: Generate audio and timings
    logger.info("Generating audio...")
    audio_bytes, speaker_timings, word_alignments = tts(script)
    logger.info(f"Generated audio: {len(audio_bytes)} bytes, {len(speaker_timings)} speaker segments, {len(word_alignments)} word alignments")
    
    # Step 13: Save video
    logger.info("Assembling video...")
    run_id = get_run_id()
    
    # Get script directory for relative paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create temporary file for audio
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name
    
    # Set up paths
    bg_folder = os.path.join(script_dir, "background-videos")
    pngs_folder = os.path.join(script_dir, "pngs")
    font_path = os.path.join(script_dir, "fonts", "SuperMalibu-Wp77v.ttf")
    out_path = os.path.join(script_dir, "final-videos", f"final-{run_id}.mp4")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    # Assemble video
    assemble_video(
        dialogue_wav_path=temp_audio_path,
        bg_folder=bg_folder,
        out_path=out_path,
        speaker_timings=speaker_timings,
        pngs_folder=pngs_folder,
        word_alignments=word_alignments,
        font_path=font_path,
        title=title,
    )
    
    # Clean up temporary audio file
    os.unlink(temp_audio_path)
    
    logger.info(f"Video saved to: {out_path}")
    logger.info("Pipeline completed successfully!")

if __name__ == "__main__":
    main()

