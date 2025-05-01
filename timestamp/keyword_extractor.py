import spacy
from transformers import pipeline
import numpy as np
import logging
from typing import List, Optional
import torch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load spaCy multilingual model (for NER, etc.)
try:
    nlp = spacy.load("xx_ent_wiki_sm")  # Multilingual entity recognition model
    logger.info("spaCy multilingual model loaded successfully.")
except Exception as e:
    logger.error(f"Error loading spaCy multilingual model: {e}")
    nlp = None  # Fallback if spaCy model fails

# Preload transformer model to avoid loading on each request
MODEL_NAME = "bert-base-multilingual-cased"
keyword_extractor = pipeline("feature-extraction", model=MODEL_NAME, tokenizer=MODEL_NAME, device=0 if torch.cuda.is_available() else -1)
logger.info(f"Loaded transformer model: {MODEL_NAME}")

def extract_keywords_nlp(
    transcript_chunk: Optional[str],
    num_keywords: int = 7,
    language: str = "en"
) -> List[str]:
    """
    Extracts keywords using multilingual NLP models.

    Args:
        transcript_chunk: The relevant transcript chunk text (optional).
        num_keywords: The desired number of keywords.
        language: The language of the transcript (default "en").

    Returns:
        A list of extracted keywords, or an empty list if an error occurs or no text is provided.
    """
    if not transcript_chunk:
        logger.warning("No transcript chunk provided for keyword extraction.")
        return []

    # Use a multilingual BERT model for keyword extraction
    try:
        features = keyword_extractor(transcript_chunk)
    except Exception as e:
        logger.error(f"Error extracting features using transformer model: {e}")
        return []

    # Flatten the feature matrix to get the most important terms
    feature_matrix = np.array(features).flatten()

    # Get the words associated with the feature matrix (tokenized input)
    tokens = keyword_extractor.tokenizer.tokenize(transcript_chunk)

    # Map features to tokens
    token_features = list(zip(tokens, feature_matrix))

    # Sort the tokens by their feature importance (using the extracted feature values)
    sorted_tokens = sorted(token_features, key=lambda x: x[1], reverse=True)

    # Extract the top N keywords (ignoring sub-word tokens like '##')
    keywords = [token for token, _ in sorted_tokens[:num_keywords] if not token.startswith("##")]

    # Optionally, use spaCy's NER model for named entity recognition if desired
    if nlp and language != "en":
        try:
            doc = nlp(transcript_chunk)
            entities = [ent.text for ent in doc.ents]
            keywords.extend(entities)
            logger.info(f"Entities extracted: {entities}")
        except Exception as e:
            logger.warning(f"Error during NER extraction with spaCy: {e}")

    logger.info(f"Extracted keywords: {keywords}")
    return keywords
