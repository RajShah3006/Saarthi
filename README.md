# 🏹 Saarthi (The Guide)

**An AI-Powered University PathFinder for Ontario Students**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![AI](https://img.shields.io/badge/AI-Google_Gemini-orange)
![UI](https://img.shields.io/badge/UI-Gradio-purple)
![Status](https://img.shields.io/badge/Status-Prototype-green)

## 📖 Overview

**Saarthi** (meaning "Charioteer" or "Guide" in Sanskrit) is an intelligent chatbot designed to help high school students navigate the complex landscape of university applications in Ontario. 

Unlike standard search tools, Saarthi uses **live web scraping** combined with **Generative AI** to understand a student's unique profile (grades, interests, location) and match them with real-time program data from [OUInfo](https://www.ouinfo.ca).

## ✨ Key Features

* **Real-Time Data:** Scrapes up-to-date program requirements, prerequisites, and admission averages directly from Ontario Universities' Info.
* **Deep-Dive Analysis:** (Optional) Can visit external university websites to gather specific details on labs, co-ops, and professors.
* **Context-Aware AI:** Uses Google's **Gemini 2.5 Flash** model to synthesize scraped data into personalized advice.
* **Interactive UI:** Built with **Gradio** for a clean, user-friendly chat interface.
* **Smart Caching:** (Planned) Caches scraped data to reduce latency and server load.

## ⚙️ How It Works



1.  **User Input:** The student provides their grades, interests (e.g., "Robotics"), and location.
2.  **Scraping Engine:** The bot searches OUInfo for programs matching the interests.
3.  **Data Extraction:** It extracts critical data: Prerequisites, Admission Averages, and Program URLs.
4.  **AI Synthesis:** The raw data is fed into the Gemini LLM with a custom prompt.
5.  **Response:** The AI acts as a guidance counselor, ranking universities and suggesting high school courses.
