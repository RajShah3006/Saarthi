# utils/validators.py - Input validation and sanitization
import re
import html
from typing import List
from models import ServiceResult


class Validators:
    """Input validation and sanitization utilities"""
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 500) -> str:
        """Sanitize text input - remove dangerous chars, limit length"""
        if not text:
            return ""
        
        # Convert to string if needed
        text = str(text)
        
        # HTML escape to prevent injection
        text = html.escape(text)
        
        # Remove potential markdown injection (links, images)
        
        # [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

        # ![alt](url) -> removed
        text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text.strip()
    
    @staticmethod
    def validate_average(average) -> tuple:
        """Validate and normalize average (returns (is_valid, value, error_msg))"""
        try:
            value = float(average)
            if value < 0 or value > 100:
                return False, None, "Average must be between 0 and 100"
            return True, value, None
        except (ValueError, TypeError):
            return False, None, "Average must be a number"
    
    @staticmethod
    def validate_profile_inputs(
        interests: str,
        extracurriculars: str,
        average,
        grade: str,
        location: str,
        config
    ) -> ServiceResult:
        """Validate all profile inputs at once"""
        errors = []
        
        # Check interests not empty
        if not interests or len(interests.strip()) < 3:
            errors.append("Please enter your academic interests (at least 3 characters)")
        
        # Check interests length
        if interests and len(interests) > config.MAX_INTERESTS_LENGTH:
            errors.append(f"Interests too long (max {config.MAX_INTERESTS_LENGTH} characters)")
        
        # Check extracurriculars length
        if extracurriculars and len(extracurriculars) > config.MAX_INTERESTS_LENGTH:
            errors.append(f"Extracurriculars too long (max {config.MAX_INTERESTS_LENGTH} characters)")
        
        # Validate average
        valid_avg, _, avg_error = Validators.validate_average(average)
        if not valid_avg:
            errors.append(avg_error)
        
        # Check grade selected
        if not grade or grade not in config.GRADE_OPTIONS:
            errors.append("Please select a valid grade level")
        
        # Check location length
        if location and len(location) > config.MAX_LOCATION_LENGTH:
            errors.append(f"Location too long (max {config.MAX_LOCATION_LENGTH} characters)")
        
        if errors:
            return ServiceResult.failure("\n".join(f"• {e}" for e in errors))
        
        return ServiceResult.success("Validation passed")