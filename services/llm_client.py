# services/llm_client.py - Gemini client with retries and timeouts
import logging
import time
from typing import Optional
from functools import wraps

from config import Config

logger = logging.getLogger("saarthi.llm")


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retry with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed: {e}")
            raise last_exception
        return wrapper
    return decorator


class LLMClient:
    """Gemini client wrapper with retries, timeouts, and fallback"""
    
    def __init__(self, config: Config):
        self.config = config
        self.has_api = bool(config.GEMINI_API_KEY)
        self.client = None
        self.model = None
        self.use_new_api = False
        
        if self.has_api:
            self._initialize_client()
        else:
            logger.warning("No API key - LLM client in demo mode")
    
    def _initialize_client(self):
        """Initialize Gemini client with fallback between API versions"""
        # Try new API first
        try:
            from google import genai
            self.client = genai.Client(api_key=self.config.GEMINI_API_KEY)
            self.model = self.config.GEMINI_MODEL
            self.use_new_api = True
            logger.info("✅ Using google-genai (new API)")
            return
        except ImportError:
            logger.debug("google-genai not available, trying legacy API")
        except Exception as e:
            logger.warning(f"google-genai init failed: {e}")
        
        # Fallback to legacy API
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(self.config.GEMINI_MODEL)
            self.use_new_api = False
            logger.info("✅ Using google-generativeai (legacy API)")
            return
        except ImportError:
            logger.error("No Gemini API library available")
        except Exception as e:
            logger.error(f"Legacy API init failed: {e}")
        
        self.has_api = False
        logger.warning("LLM client falling back to demo mode")
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate response with retries"""
        if not self.has_api:
            return self._demo_response(prompt)
        
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        try:
            if self.use_new_api:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=full_prompt
                )
                return response.text
            else:
                response = self.model.generate_content(full_prompt)
                return response.text
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    def _demo_response(self, prompt: str) -> str:
        """Demo response when no API available"""
        prompt_lower = prompt.lower()
        
        if "computer" in prompt_lower or "software" in prompt_lower or "tech" in prompt_lower:
            return """## 🎓 Computer Science Recommendations

**Top Programs for You:**

1. **University of Toronto - Computer Science**
   - Admission: 85-90%
   - Prerequisites: Advanced Functions, Calculus & Vectors
   - ✅ Co-op Available

2. **University of Waterloo - Software Engineering**
   - Admission: 90-95%
   - Prerequisites: Advanced Functions, Calculus, Physics
   - ✅ Co-op Available (renowned program)

3. **UBC - Computer Science**
   - Admission: 85-88%
   - Prerequisites: Pre-Calculus 12, English 12
   - ✅ Co-op Available

**Next Steps:**
1. Maintain or improve your grades in prerequisite courses
2. Build programming projects (GitHub portfolio)
3. Participate in hackathons or coding competitions
4. Consider AP Computer Science if available

*Note: This is demo mode. Add your Gemini API key for personalized AI guidance.*"""

        elif "business" in prompt_lower or "commerce" in prompt_lower:
            return """## 🎓 Business Recommendations

**Top Programs:**

1. **Ivey Business School (Western)**
   - Admission: 85-90%
   - Case-based learning approach
   - Strong alumni network

2. **Queen's Commerce**
   - Admission: 88-92%
   - Highly competitive
   - Excellent co-op opportunities

3. **Schulich (York)**
   - Admission: 85-88%
   - International focus
   - ✅ Co-op Available

*This is demo mode. Enable AI for personalized guidance.*"""

        else:
            return """## 🎓 University Guidance

Based on your profile, here are some general recommendations:

**Next Steps:**
1. Research programs matching your specific interests
2. Check prerequisite requirements for target schools
3. Focus on maintaining strong grades
4. Develop relevant extracurricular activities
5. Visit university websites and attend info sessions

**Tips:**
- Quality over quantity for extracurriculars
- Start applications early
- Request reference letters in advance

*Add your Gemini API key in Hugging Face Secrets for personalized AI-powered recommendations.*"""