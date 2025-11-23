# university-recommender-ai

**university-recommender-ai** is an intelligent, Ontario-focused university and program recommendation system that leverages web scraping and AI-driven conversation to provide tailored guidance for students.

## Features

The core Jupyter Notebook performs the following:

- **Collects user academic and interest information** (subjects, grade, location, overall average, future goals)
- **Scrapes university program listings and details** from OUInfo (Ontario Universities' Info) and other sources
- **Extracts prerequisites, admission averages, program details** using flexible HTML parsing
- **Identifies and ranks programs relevant to the student's interests** (e.g., robotics, engineering, automation)
- **Generates personalized recommendations** outlining:
  - The most relevant programs and universities
  - Required prerequisites and high school courses
  - Typical admission averages
  - Suggested personal projects and activities to strengthen applications
- **Uses a conversational AI model (e.g., Gemini/GPT) to interactively present insights and advice**

## Use Case

This project is ideal for students seeking detailed, actionable guidance on Ontario university choices, with an emphasis on STEM and technology fields. It features robust scraping logic and AI customization for truly personalized university recommendations.

## Technologies Used

- Python
- Web scraping (BeautifulSoup, requests)
- AI/ML models for conversational recommendations
- Jupyter Notebook for interactive exploration
