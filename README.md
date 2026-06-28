# 📡 Real-Time Crypto Portfolio Tracker & Reporter

A multi-threaded real-time cryptocurrency portfolio tracking application built from scratch using **Python**, **Flask**, and **SQLite3**. This system automatically connects to external financial markets via a public REST API to track active investments, calculate financial margins, and run background services

---

## 🌟 Application Features

1. **Live Third-Party API Integration**
   * Uses Python's `requests` library to fetch real-time token values directly from the official CoinGecko public REST API.
2. **Multi-Threaded Background Worker**
   * Features an independent background thread microservice that runs continuously in a loop, updating prices every 60 seconds without freezing the user interface.
3. **Dynamic Profit & Loss (P&L) Ledger**
   * Automatically calculates your total invested cost, current live market value, and net profit or loss percentages on the fly using SQLite database records.
4. **Interactive Asset Transaction Logger**
   * Includes a clean dashboard form interface where users can easily input and record new asset positions.

---

## ⚙️ Tech Stack & Concepts Covered

* **Backend Framework:** Python with Flask (Handling routes, session states, and web engine controls).
* **Database Layer:** SQLite3 (For storing user investments and caching live market prices).
* **Concurrency:** Python's built-in `threading` module (For executing non-blocking background microservices).
* **Network Communication:** HTTP client calls via the `requests` library.

---

## 🛠️ Step-by-Step Local Setup Guide

Follow these simple steps to run this application on your machine:

### 1. Install Necessary Libraries
Open your terminal in VS Code and install the web framework and networking packages:
```bash
pip install Flask requests
